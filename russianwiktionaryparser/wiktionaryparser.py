import copy
import json
import os
import re
import urllib
import logging
import bs4
import requests
from pydub import AudioSegment
from . entries import WordEntry, WordDefinition, WordExample
from . parsers import Parser

_LOG = logging.getLogger(__name__)


class WiktionaryInflectionTable:
    def __init__(self, table_soup: bs4.BeautifulSoup):
        self._json = {}
        self._stripped = {}

        if table_soup is not None:
            table_body = table_soup.tbody

            table_entries = table_body.find_all('span', {'class': re.compile('Cyrl form-of lang-ru')})
            for entry in table_entries:
                classes = entry['class']
                for cls in classes:
                    if cls.endswith('-form-of'):
                        entry_key = cls.replace('-form-of', '')
                        item = entry.get_text().strip()
                        # self._json[entry_key] = self._json.get(entry_key, []).append(item)
                        # self._stripped[entry_key] = self._stripped.get(entry_key, []).append(item.replace('́', ''))
                        if entry_key in self._json:
                            self._json[entry_key].append(item)
                            self._stripped[entry_key].append(item.replace('́', ''))
                        else:
                            self._json[entry_key] = [item]
                            self._stripped[entry_key] = [item.replace('́', '')]

    def to_json(self):
        return self._json

    def serialize(self):
        return self._stripped

    def to_lower_set(self):
        inflection_set = set()
        for key in self._json.keys():
            for item in self._json[key]:
                inflection_set.add(item.lower().replace('́', ''))
        return inflection_set

    @classmethod
    def build_from_serial(cls, inflections):
        inflections_table = WiktionaryInflectionTable(None)
        inflections_table._json = inflections
        return inflections_table


class WiktionaryExample(WordExample):
    def __init__(self, examples_tag=None):
        super().__init__()
        self._text = ''
        self._translation = ''
        if examples_tag is not None:
            mention_tag = examples_tag.find('i', {'class': 'Cyrl mention e-example'})
            if mention_tag is not None:
                self._text = mention_tag.get_text()
            translation_tag = examples_tag.find('span', {'class': 'e-translation'})
            if translation_tag is not None:
                self._translation = translation_tag.get_text()

    @classmethod
    def build_from_serial(cls, example):
        wiki_ex = WiktionaryExample()
        wiki_ex._text = example
        return wiki_ex


class WiktionaryDefinition(WordDefinition):
    def __init__(self, list_item=None):
        super().__init__()
        self.base_word = ''
        self.base_link = None
        self._text = ''
        self._examples = []

        if list_item is not None:
            base_ref = list_item.find('span', {'class': 'form-of-definition-link'})
            if base_ref is not None:
                self.base_word = base_ref.i.a.get_text()
                self.base_link = base_ref.i.a['href']

            citations = list_item.find_all('span', {'class': 'HQToggle'})
            for citation in citations:
                citation.decompose()
            citation_ul = list_item.find('div', {'class': 'citation-whole'})
            if citation_ul is not None:
                citation_ul.decompose()
            h_usage_tags = list_item.find_all('div', {'class': 'h-usage-example'})
            for usage_tag in h_usage_tags:
                usage_tag.extract()
                self._parse_usage_tag(usage_tag)
            tmp_text = list_item.get_text().strip()
            self._text = " ".join(tmp_text.split())  # get rid of any double spaces

    def _parse_usage_tag(self, usage_tag):
        self.examples.append(WiktionaryExample(usage_tag))

    @classmethod
    def build_from_serial(cls, serial):
        wiki_def = WiktionaryDefinition()
        wiki_def._text = serial['text']
        for example in serial['examples']:
            wiki_def.examples.append(WiktionaryExample.build_from_serial(example))
        return wiki_def


class WiktionaryEntry(WordEntry):
    pos_list = ['Verb', 'Noun', 'Adjective', 'Pronoun', 'Conjunction', 'Proper noun', 'Numeral', 'Preposition',
                'Adverb', 'Participle', 'Letter', 'Prefix', 'Punctuation mark', 'Interjection', 'Determiner',
                'Predicative', 'Proverb', 'Particle']

    def __init__(self, word, pos_header=None, tracing=None, *args, **kwargs):
        super().__init__(word, *args, **kwargs)
        self.word = word
        self._soup = None
        self.part_of_speech = ''
        self.definitions = []
        self.inflections = None
        self.audio_links = []
        self.base_links = []
        self.base_links_set = set()
        self.tracing = tracing if tracing is not None else []

        if pos_header is not None:
            self._soup = pos_header.parent.parent
            self._parse_part_of_speech(pos_header)
            self._parse_definitions()
            self._parse_inflection_table()
            self._parse_audio_links()
            self._parse_base_links()

    @classmethod
    def build_from_serial(cls, serial):
        entry = WiktionaryEntry(serial['word'])
        entry.part_of_speech = serial['part_of_speech']
        for definition in serial.get('definitions', []):
            entry.definitions.append(WiktionaryDefinition.build_from_serial(definition))
        if 'inflections' in serial:
            entry.inflections = WiktionaryInflectionTable.build_from_serial(serial['inflections'])
        return entry

    def follow_to_base(self):
        entries = []
        if self._purely_base:
            if len(self.base_links_set) == 1:
                wiki = WiktionaryParser()
                entries = wiki.fetch_from_url('https://en.wiktionary.org' + self.base_links_set.pop())
                for entry in entries:
                    entry.tracing.extend(self.tracing)
                    entry.tracing.append(f"Followed to base {self.base_links[0]['word']}")
        return entries

    @property
    def _purely_base(self):
        if len(self.definitions) == 0:
            return False
        for definition in self.definitions:
            if definition.base_link is None:
                return False
        return True

    def _parse_base_links(self):
        for definition in self.definitions:
            if definition.base_link is not None:
                self.base_links_set.add(definition.base_link)
                self.base_links.append(
                    {
                        'link': definition.base_link,
                        'word': definition.base_word,
                        'text': definition.text
                    }
                )

    def _parse_part_of_speech(self, pos_header):
        self._pos_heading = pos_header
        heading_id = pos_header['id']
        stripped_heading_id = remove_trailing_numbers(heading_id).replace('_', ' ')
        self.part_of_speech = stripped_heading_id
        _LOG.debug('Part of speech found: %s', self.part_of_speech)

    def _parse_definitions(self):
        if self._pos_heading is not None:
            next_items = self._pos_heading.parent.find_next_siblings()
            for item in next_items:
                if item.name == 'ol':
                    def_list = list(item.children)
                    for definition in def_list:
                        self._parse_definition(definition)
                    break
            else:
                _LOG.debug('No definition list found')

    def _parse_definition(self, definition):
        if definition.name == 'li' and definition.attrs.get('class') != ['mw-empty-elt']:
            self.definitions.append(WiktionaryDefinition(definition))

    def _parse_inflection_table(self):
        inflection_table = self._soup.find('table', {'class': re.compile('inflection-table')})
        if inflection_table is not None:
            self.inflections = WiktionaryInflectionTable(inflection_table)
        else:
            _LOG.debug('No inflection table found')

    def serialize(self):
        ser = {'word': self.word,
               'part_of_speech': self.part_of_speech,
               'definitions': [],
               'inflections': {}}
        for definition in self.definitions:
            examples = []
            for example in definition.examples:
                examples.append(example.text)
            ser['definitions'].append(
                {'text': definition.text, 'examples': examples, 'base_word': definition.base_word})
        if self.inflections is not None:
            ser['inflections'] = self.inflections.serialize()
        return ser

    def _parse_audio_links(self):
        audio_meta = self._soup.find_all('td', {'class': 'audiometa'})
        if audio_meta:
            _LOG.debug('%i audio links found', len(audio_meta))
            for meta_data in audio_meta:
                self.audio_links.append(meta_data.a['href'])
        else:
            _LOG.debug('No audio links found')

    def __str__(self):
        self_str = f"{self.word}: {self.part_of_speech}\n"
        for i, definition in enumerate(self.definitions):
            self_str += f"\t{i + 1}. {definition.text}\n"
            for example in definition.examples:
                self_str += f"\t\t{example.text} - {example.translation}\n"
        return self_str.replace('́', '')  # remove accents

    def __eq__(self, other):
        if isinstance(other, WiktionaryEntry):
            if self.word == other.word:
                if self.part_of_speech == other.part_of_speech:
                    for me, you in zip(self.definitions, other.definitions):
                        if me.text != you.text:
                            return False
                    return True
        return False


def split_page_by_etymology(etymologies):
    split_page = []
    for i, etymology in enumerate(etymologies):
        new_page = bs4.BeautifulSoup("<html><body><div class=\"mw-parser-output\"></div></body></html>",
                                     features="lxml")
        etymology_parent = etymology.parent
        if etymology_parent is not None and etymology_parent.name == 'h3':
            next_sibling = etymology_parent.next_sibling
            next_etymology = etymologies[i + 1].parent if i + 1 < len(etymologies) else None
            while next_sibling != next_etymology:
                new_page.body.div.append(copy.copy(next_sibling))
                next_sibling = next_sibling.next_sibling
        else:
            logging.debug('Error parsing etymologies')
            return split_page

        split_page.append(new_page)
    return split_page


class WiktionaryPageParser:
    def __init__(self, entered_word, soup: bs4.BeautifulSoup):
        self.entered_word = entered_word
        self.raw_soup = soup
        self.page_title = ''
        self._get_title()
        self.filtered_soup = self.filter_language()
        self.entries = []

        if self.filtered_soup is not None:
            etymologies = self.filtered_soup.find_all('span', {'class': 'mw-headline', 'id': re.compile('Etymology')})
            if len(etymologies) > 1:
                split_page = split_page_by_etymology(etymologies)
            else:
                split_page = [self.filtered_soup]

            for page in split_page:
                pos_list = get_parts_of_speech(page)
                for pos in pos_list:
                    self.entries.append(WiktionaryEntry(self.page_title, pos))

    def get_entries(self):
        return self.entries

    def filter_language(self):
        if self.raw_soup is not None:
            new_page = bs4.BeautifulSoup("<html><body><div class=\"mw-parser-output\"></div></body></html>",
                                         features="lxml")
            russian_headline = self.raw_soup.find('span', {'class': 'mw-headline', 'id': 'Russian'})
            if russian_headline is not None and russian_headline.parent.name == 'h2':
                parent = russian_headline.parent
                next_sibling = parent.next_sibling
                while next_sibling is not None:
                    if isinstance(next_sibling, bs4.element.Tag):
                        if next_sibling.name == 'h2':
                            break
                    new_page.body.div.append(copy.copy(next_sibling))
                    next_sibling = next_sibling.next_sibling
            else:
                logging.warning('No russian entries found on page!')
                return None

            return new_page
        return None

    def _get_title(self):
        first_heading = self.raw_soup.find('h1', {'class': 'firstHeading'})
        if first_heading is not None:
            self.page_title = first_heading.get_text()
            _LOG.debug('Page title found: %s', self.page_title)
            if self.entered_word != self.page_title:
                _LOG.info('Page redirected from word %s to %s', self.entered_word, self.page_title)
        else:
            _LOG.warning('Could not find title in page')


def convert_ogg_to_mp3(ogg_file):
    mp3_file = ogg_file.replace('.ogg', '.mp3')
    try:
        AudioSegment.from_file(ogg_file).export(mp3_file, format="mp3")
    except:
        print("Error occurred converting file")
    return mp3_file


class WiktionaryParser(Parser):
    def __init__(self):
        pass

    def can_handle_entry(self, entry: any) -> bool:
        if isinstance(entry, str):
            return True

    def fetch_from_url(self, url):
        _LOG.debug('fetching from url')
        entered_word = parse_word_from_url(url)
        raw_soup = make_soup_from_url(url)
        if raw_soup is not None:
            wiki_page = WiktionaryPageParser(entered_word, raw_soup)
            return wiki_page.get_entries()
        return []

    def fetch(self, entered_word, follow_to_base=False):
        _LOG.info('Fetching page for word "%s"', entered_word)
        entries = []
        raw_soup = make_soup(entered_word)
        if raw_soup is not None:
            wiki_page = WiktionaryPageParser(entered_word, raw_soup)
            entries = wiki_page.get_entries()
            if follow_to_base:
                # TODO
                pass
        else:
            _LOG.error('Error fetching page')
        return entries

    def search(self, word, limit=10):
        results = []
        resp = requests.get(
            f"https://en.wiktionary.org/w/api.php?action=opensearch&format=json&formatversion=2&search={word}&namespace=0&limit={limit}")
        if resp.status_code == 200:
            results = json.loads(resp.content.decode())
        else:
            _LOG.info('Error received from server: %u', resp.status_code)
        return results

    def download_audio(self, link, destination='.'):
        audio_file_page = requests.get(f'https://en.wiktionary.org{link}')
        if audio_file_page.status_code == 200:
            soup = bs4.BeautifulSoup(audio_file_page.content, features='lxml')
            full_media = soup.find('div', {'class': 'fullMedia'})
            if full_media is not None:
                file_name = full_media.p.a['title']
                file_link = full_media.p.a['href']
                _LOG.debug('Downloading file %s', file_name)
                audio_file = requests.get(f'https:{file_link}')
                file_dest = os.path.join(destination, file_name)
                open(file_dest, 'wb').write(audio_file.content)
                if '.mp3' not in file_dest:
                    file_dest = convert_ogg_to_mp3(file_dest)
                return file_dest
            else:
                _LOG.warning('Could not find media file on page')
                return None
        else:
            _LOG.warning('Error fetching file %s', link)
            return None


def parse_word_from_url(url):
    entered_word = urllib.parse.unquote(url.split('/')[-1])
    if '#' in entered_word:
        entered_word = ''.join(entered_word.split('#')[:-1])
    return entered_word


def make_soup(word: str):
    """Fetch wiki entry for given word and make some beautiful soup out if it."""
    resp = requests.get(
        f'https://en.wiktionary.org/w/index.php?search={word}+&title=Special%3ASearch&go=Go&wprov=acrw1_-1')
    if resp.status_code == 200:
        return bs4.BeautifulSoup(resp.content, features="lxml")
    return None


def make_soup_from_url(url):
    """Fetch wiki entry for given word and make some beautiful soup out if it."""
    resp = requests.get(url)
    if resp.status_code == 200:
        return bs4.BeautifulSoup(resp.content, features="lxml")
    return None


def remove_trailing_numbers(heading_id):
    header_parts = heading_id.split('_')
    if header_parts[-1].isnumeric():
        # remove trailing number from heading if there is one
        stripped_heading_id = heading_id.replace(f'_{header_parts[-1]}', '')
    else:
        stripped_heading_id = heading_id
    return stripped_heading_id


def get_parts_of_speech(soup):
    pos_list = []
    headlines = soup.find_all('span', {'class': 'mw-headline'})
    for headline in headlines:
        text = headline.get_text()
        if remove_trailing_numbers(text) in WiktionaryEntry.pos_list:
            pos_list.append(headline)
    return pos_list


def get_filename_from_link(link):
    return urllib.parse.unquote(link.split('/')[-1]).replace('File:', '')
