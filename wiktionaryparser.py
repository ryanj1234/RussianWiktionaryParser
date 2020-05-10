import copy
import json
import re
import bs4
import requests
import logging


class WiktionaryInflectionTable:
    def __init__(self, table_soup: bs4.BeautifulSoup, part_of_speech):
        self._logger = logging.getLogger('WikiInf')
        self._json = {}
        table_body = table_soup.tbody

        table_entries = table_body.find_all('span', {'class': re.compile('Cyrl form-of lang-ru')})
        for entry in table_entries:
            classes = entry['class']
            for cls in classes:
                if cls.endswith('-form-of'):
                    entry_key = cls.replace('-form-of', '')
                    item = entry.get_text().strip()
                    if entry_key in self._json:
                        self._json[entry_key].append(item)
                    else:
                        self._json[entry_key] = [item]

    def to_json(self):
        return self._json


class WiktionaryExample:
    def __init__(self, examples_tag):
        self._logger = logging.getLogger('WikiEx')
        self.text = examples_tag.get_text()


class WiktionaryDefinition:
    def __init__(self, list_item):
        self._logger = logging.getLogger('WikiDef')
        self.base_word = None
        self.base_link = None
        self.examples = []
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
        examples = list_item.find('dl')
        if examples:
            examples_tag = examples.extract()
            self._parse_examples(examples_tag)
        self.text = list_item.get_text().strip()
        self.parsed = True

    def _parse_examples(self, examples_tag):
        dd = examples_tag.find_all('i', {'Cyrl mention e-example'})
        for def_tag in dd:
            self.examples.append(WiktionaryExample(def_tag))


class WiktionaryEntry:
    pos_list = ['Verb', 'Noun', 'Adjective', 'Pronoun', 'Conjunction', 'Proper_noun', 'Numeral', 'Preposition', 'Adverb', 'Participle', 'Letter', 'Prefix', 'Punctuation_mark']

    def __init__(self, word, soup, part_of_speech=None):
        self._logger = logging.getLogger('Wiki-%s' % word)
        self.word = word
        self._soup = soup
        self.part_of_speech = ''
        self.definitions = []
        self.inflections = None
        self.base_links = []

        self._parse_part_of_speech(part_of_speech)
        self._parse_definitions()
        self._parse_inflection_table()
        self._parse_base_links()

    def _parse_base_links(self):
        for definition in self.definitions:
            if definition.base_link is not None:
                self.base_links.append(
                    {
                        'link': definition.base_link,
                        'word': definition.base_word,
                        'text': definition.text
                    }
                )

    def _parse_part_of_speech(self, part_of_speech):
        self._pos_heading = None
        if part_of_speech is None:
            self._find_part_of_speech()
        else:
            self._find_speech_header(part_of_speech)

    def _find_part_of_speech(self):
        pos_headings = self._soup.find_all('span', {'class': 'mw-headline'})
        for heading in pos_headings:
            heading_id = heading.get('id')
            if heading_id is not None:
                stripped_heading_id = remove_trailing_numbers(heading_id)
                if stripped_heading_id in WiktionaryEntry.pos_list:
                    self.part_of_speech = stripped_heading_id
                    self._pos_heading = heading
                    self._logger.debug('Part of speech found: %s', self.part_of_speech)
                    break
        else:
            self._logger.error('Could not determine part of speech')

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
                self._logger.debug('No definition list found')

    def _parse_definition(self, definition):
        if definition.name == 'li':
            wiki_def = WiktionaryDefinition(definition)
            if wiki_def.parsed:
                self.definitions.append(wiki_def)

    def _find_speech_header(self, part_of_speech):
        pos_heading = self._soup.find('span', {'class': 'mw-headline', 'id': part_of_speech})
        if pos_heading is None:
            self._logger.debug('Could not find provided part of speech header: %s', part_of_speech)
        else:
            self._pos_heading = pos_heading
            self.part_of_speech = remove_trailing_numbers(part_of_speech).replace('_', ' ')

    def _parse_inflection_table(self):
        inflection_table = self._soup.find('table', {'class': re.compile('inflection-table')})
        if inflection_table is not None:
            self.inflections = WiktionaryInflectionTable(inflection_table, self.part_of_speech)
        else:
            self._logger.debug('No inflection table found')

    def __str__(self):
        self_str = f"{self.word}: {self.part_of_speech}\n"
        for i, definition in enumerate(self.definitions):
            self_str += f"\t{i+1}. {definition.text}\n"
            for example in definition.examples:
                self_str += f"\t\t{example.text}\n"
        return self_str.replace('́', '')  # remove accents


class WiktionaryParser:
    def __init__(self):
        self._logger = logging.getLogger('WiktionaryParser')

    def fetch(self, entered_word):
        self._logger.info('Fetching page for word %s', entered_word)
        entries = []
        raw_soup = make_soup(entered_word)
        if raw_soup is not None:
            toc = get_table_of_contents(raw_soup)
            soup = filter_language(raw_soup)
            if soup is not None:
                if toc:
                    entry_list = parse_toc(toc)
                    if not len(entry_list):
                        logging.warning('Russian entry found for word %s but could not determine part of speech', entered_word)
                    for entry in entry_list:
                        entries.append(WiktionaryEntry(entered_word, soup, entry))
                else:
                    entries = [WiktionaryEntry(entered_word, soup)]
        else:
            self._logger.debug('No page found for word %s' % entered_word)
        return entries

    def search(self, word, limit=10):
        results = []
        resp = requests.get(f"https://en.wiktionary.org/w/api.php?action=opensearch&format=json&formatversion=2&search={word}&namespace=0&limit={limit}")
        if resp.status_code == 200:
            results = json.loads(resp.content.decode())
        else:
            self._logger.info('Error received from server: %u', resp.status_code)
        return results

    # TODO: search, lookup first result and check for word in declension table


def make_soup(word: str) -> bs4.BeautifulSoup:
    """Fetch wiki entry for given word and make some beautiful soup out if it."""
    resp = requests.get(f'https://en.wiktionary.org/wiki/{word}')
    if resp.status_code == 200:
        return bs4.BeautifulSoup(resp.content, features="lxml")
    return None


def filter_language(soup_data: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    if soup_data is not None:
        new_page = bs4.BeautifulSoup("<html><body><div class=\"mw-parser-output\"></div></body></html>", features="lxml")
        russian_headline = soup_data.find('span', {'class': 'mw-headline', 'id': 'Russian'})
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
            logging.debug('No russian entries found on page!')
            return None

        return new_page
    return None


def get_table_of_contents(soup):
    contents = soup.find_all('span', {'class': 'toctext'})
    for content in contents:
        if content.get_text() == 'Russian':
            return content
    return None


def parse_toc(toc):
    entry_list = []
    toc_section = toc.parent.parent
    item_list = toc_section.ul
    possible_items = item_list.find_all('a')
    for anchor in possible_items:
        href = anchor['href']
        if '#' in href:
            href = href.split('#')[1]
            # stripped_pos = href.split('_')[0]
            if remove_trailing_numbers(href) in WiktionaryEntry.pos_list:
                entry_list.append(href)
    return entry_list


def remove_trailing_numbers(heading_id):
    header_parts = heading_id.split('_')
    if header_parts[-1].isnumeric():
        # remove trailing number from heading if there is one
        stripped_heading_id = heading_id.replace(f'_{header_parts[-1]}', '')
    else:
        stripped_heading_id = heading_id
    return stripped_heading_id
