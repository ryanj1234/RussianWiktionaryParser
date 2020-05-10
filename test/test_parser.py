import os
from unittest.mock import patch
from wiktionaryparser import WiktionaryParser
from bs4 import BeautifulSoup
import logging

dir_path = os.path.dirname(os.path.realpath(__file__))
data_dir = 'data'

logging.basicConfig(level=logging.DEBUG)


def build_soup_from_file(word):
    full_file_path = os.path.join(dir_path, data_dir, f"{word} - Wiktionary.html")
    return BeautifulSoup(open(full_file_path, 'r', encoding='utf-8'), features="lxml")


def run_fetch(word):
    # mock = True
    wiki = WiktionaryParser()
    # if mock:
    with patch('wiktionaryparser.make_soup') as mock_fetch:
        mock_fetch.side_effect = build_soup_from_file
    return wiki.fetch(word)


def test_to_say():
    entries = run_fetch('сказать')
    assert len(entries) == 1, "Unexpected number of entries found"
    assert entries[0].part_of_speech == "Verb", "Incorrect part of speech found"
    assert len(entries[0].definitions) == 1, "Unexpected number of definitions found"
    assert entries[0].definitions[0].text == "to say, to tell"
    assert len(entries[0].definitions[0].examples) == 0, "Unexpected number of examples found"

    inflections = entries[0].inflections.to_json()
    assert inflections['inf'] == ['сказа́ть']
    assert inflections['past|act|part'] == ['сказа́вший']
    assert inflections['past|pass|part'] == ['ска́занный']
    assert inflections['past|adv|part'] == ['сказа́в', 'сказа́вши']

    assert inflections['1|s|fut|ind'] == ['скажу́']
    assert inflections['2|s|fut|ind'] == ['ска́жешь']
    assert inflections['3|s|fut|ind'] == ['ска́жет']
    assert inflections['1|p|fut|ind'] == ['ска́жем']
    assert inflections['2|p|fut|ind'] == ['ска́жете']
    assert inflections['3|p|fut|ind'] == ['ска́жут']

    assert inflections['2|s|imp'] == ['скажи́']
    assert inflections['2|p|imp'] == ['скажи́те']

    assert inflections['m|s|past|ind'] == ['сказа́л']
    assert inflections['f|s|past|ind'] == ['сказа́ла']
    assert inflections['n|s|past|ind'] == ['сказа́ло']
    assert inflections['p|past|ind'] == ['сказа́ли']


def test_cat():
    entries = run_fetch('кот')
    assert len(entries) == 1, "Unexpected number of entries found"
    assert entries[0].part_of_speech == "Noun", "Incorrect part of speech found"
    assert len(entries[0].definitions) == 1, "Unexpected number of definitions found"
    assert entries[0].definitions[0].text == "tomcat"
    assert len(entries[0].definitions[0].examples) == 4, "Unexpected number of examples found"
    assert entries[0].definitions[0].examples[0].text == 'кот в сапога́х'
    assert entries[0].definitions[0].examples[1].text == 'кот наплакал'
    assert entries[0].definitions[0].examples[2].text == 'Не всё коту́ ма́сленица, придёт и вели́кий пост.'
    assert entries[0].definitions[0].examples[3].text == 'купи́ть кота́ в мешке́'

    inflections = entries[0].inflections.to_json()
    assert inflections['nom|s'] == ['ко́т']
    assert inflections['nom|p'] == ['коты́']

    assert inflections['gen|s'] == ['кота́']
    assert inflections['gen|p'] == ['кото́в']
    assert inflections['dat|s'] == ['коту́']
    assert inflections['dat|p'] == ['кота́м']
    assert inflections['acc|s'] == ['кота́']
    assert inflections['acc|p'] == ['кото́в']
    assert inflections['ins|s'] == ['кото́м']
    assert inflections['ins|p'] == ['кота́ми']
    assert inflections['pre|s'] == ['коте́']
    assert inflections['pre|p'] == ['кота́х']


def test_thin():
    entries = run_fetch('худой')
    assert len(entries) == 2, "Unexpected number of entries found"

    assert entries[0].part_of_speech == "Adjective", "Incorrect part of speech found"
    assert len(entries[0].definitions) == 1, "Unexpected number of definitions found"
    assert entries[0].definitions[0].text == "thin, lean, skinny"
    assert len(entries[0].definitions[0].examples) == 0, "Unexpected number of examples found"

    assert entries[1].part_of_speech == "Adjective", "Incorrect part of speech found"
    assert len(entries[1].definitions) == 2, "Unexpected number of definitions found"
    assert entries[1].definitions[0].text == "bad"
    assert len(entries[1].definitions[0].examples) == 0, "Unexpected number of examples found"

    inflections = entries[0].inflections.to_json()
    assert inflections['nom|m|s'] == ['худо́й']
    assert inflections['nom|n|s'] == ['худо́е']
    assert inflections['nom|f|s'] == ['худа́я']
    assert inflections['nom|p'] == ['худы́е']

    assert inflections['gen|m//n|s'] == ['худо́го']
    assert inflections['gen|f|s'] == ['худо́й']
    assert inflections['gen|p'] == ['худы́х']

    assert inflections['dat|m//n|s'] == ['худо́му']
    assert inflections['dat|f|s'] == ['худо́й']
    assert inflections['dat|p'] == ['худы́м']

    assert inflections['an|acc|m|s'] == ['худо́го']
    assert inflections['in|acc|m|s'] == ['худо́й']
    assert inflections['acc|n|s'] == ['худо́е']
    assert inflections['acc|f|s'] == ['худу́ю']
    assert inflections['an|acc|p'] == ['худы́х']
    assert inflections['in|acc|p'] == ['худы́е']

    assert inflections['ins|m//n|s'] == ['худы́м']
    assert inflections['ins|f|s'] == ['худо́й', 'худо́ю']
    assert inflections['ins|p'] == ['худы́ми']

    assert inflections['pre|m//n|s'] == ['худо́м']
    assert inflections['pre|f|s'] == ['худо́й']
    assert inflections['pre|p'] == ['худы́х']

    assert inflections['short|m|s'] == ['худ']
    assert inflections['short|n|s'] == ['ху́до']
    assert inflections['short|f|s'] == ['худа́']
    assert inflections['short|p'] == ['худы́', 'ху́ды']


def test_said():
    entries = run_fetch('сказал')
    assert len(entries) == 1, "Unexpected number of entries found"

    assert entries[0].part_of_speech == "Verb", "Incorrect part of speech found"
    assert len(entries[0].definitions) == 1, "Unexpected number of definitions found"
    assert entries[0].definitions[0].text == "masculine singular past indicative perfective of сказа́ть (skazátʹ)"
    assert len(entries[0].definitions[0].examples) == 0, "Unexpected number of examples found"

    assert entries[0].definitions[0].base_word == 'сказа́ть'
    assert entries[0].definitions[0].base_link.endswith('/wiki/%D1%81%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D1%8C#Russian')

    assert entries[0].inflections is None


def test_to_obey():
    entries = run_fetch('подчиняться')
    assert len(entries) == 1, "Unexpected number of entries found"

    assert entries[0].part_of_speech == "Verb", "Incorrect part of speech found"
    assert len(entries[0].definitions) == 2, "Unexpected number of definitions found"
    assert entries[0].definitions[0].text == "to obey, to submit to, to surrender, to be subordinate to"
    assert len(entries[0].definitions[0].examples) == 0, "Unexpected number of examples found"

    assert entries[0].definitions[1].text == "passive of подчиня́ть (podčinjátʹ)"
    assert len(entries[0].definitions[1].examples) == 0, "Unexpected number of examples found"

    assert entries[0].definitions[1].base_word == 'подчиня́ть'
    assert entries[0].definitions[1].base_link.endswith('/wiki/%D0%BF%D0%BE%D0%B4%D1%87%D0%B8%D0%BD%D1%8F%D1%82%D1%8C#Russian')

    inflections = entries[0].inflections.to_json()
    assert inflections['inf'] == ['подчиня́ться']
    assert inflections['pres|act|part'] == ['подчиня́ющийся']
    assert inflections['pres|adv|part'] == ['подчиня́ясь']
    assert inflections['past|act|part'] == ['подчиня́вшийся']
    assert inflections['past|adv|part'] == ['подчиня́вшись']

    assert inflections['1|s|pres|ind'] == ['подчиня́юсь']
    assert inflections['2|s|pres|ind'] == ['подчиня́ешься']
    assert inflections['3|s|pres|ind'] == ['подчиня́ется']
    assert inflections['1|p|pres|ind'] == ['подчиня́емся']
    assert inflections['2|p|pres|ind'] == ['подчиня́етесь']
    assert inflections['3|p|pres|ind'] == ['подчиня́ются']

    assert inflections['2|s|imp'] == ['подчиня́йся']
    assert inflections['2|p|imp'] == ['подчиня́йтесь']

    assert inflections['m|s|past|ind'] == ['подчиня́лся']
    assert inflections['f|s|past|ind'] == ['подчиня́лась']
    assert inflections['n|s|past|ind'] == ['подчиня́лось']
    assert inflections['p|past|ind'] == ['подчиня́лись']


def test_saw():
    entries = run_fetch('пила')
    assert len(entries) == 2, "Unexpected number of entries found"

    assert entries[0].part_of_speech == "Noun", "Incorrect part of speech found"
    assert len(entries[0].definitions) == 1, "Unexpected number of definitions found"
    assert entries[0].definitions[0].text == "saw"
    assert len(entries[0].definitions[0].examples) == 1, "Unexpected number of examples found"
    assert entries[0].definitions[0].examples[0].text == "двуру́чная пила́"

    # TODO: declension table

    assert entries[1].part_of_speech == "Verb", "Incorrect part of speech found"
    assert len(entries[1].definitions) == 1, "Unexpected number of definitions found"
    assert entries[1].definitions[0].text == "feminine singular past indicative imperfective of пить (pitʹ)"
    assert len(entries[1].definitions[0].examples) == 0, "Unexpected number of examples found"


def test_russian():
    entries = run_fetch('Россия')
    assert len(entries) == 1, "Unexpected number of entries found"

    assert entries[0].part_of_speech == "Proper noun", "Incorrect part of speech found"
    assert len(entries[0].definitions) == 1, "Unexpected number of definitions found"
    assert entries[0].definitions[0].text == "Russia (a country in Eastern Europe and Asia)"
    assert len(entries[0].definitions[0].examples) == 3, "Unexpected number of examples found"
    assert entries[0].definitions[0].examples[0].text == "в Росси́и"
    assert entries[0].definitions[0].examples[1].text == "в Росси́ю"
    assert entries[0].definitions[0].examples[2].text == "из Росси́и"

    assert entries[0].inflections is not None
