from wiktionaryparser import WiktionaryParser
import logging

logging.basicConfig(level=logging.INFO)
if __name__ == '__main__':
    wp = WiktionaryParser()
    entries = wp.fetch('сказать')
    # wiki = WiktionaryParser()
    # entries = wiki.fetch_from_url('https://en.wiktionary.org/wiki/%D0%BA%D0%BE%D1%82')
    print(f"{len(entries)} entries found")
    for entry in entries:
        print(entry)
        print(entry.inflections.to_lower_set())
