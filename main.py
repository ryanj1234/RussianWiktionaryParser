from wiktionaryparser import WiktionaryParser
import logging

logging.basicConfig(level=logging.INFO)
if __name__ == '__main__':
    wp = WiktionaryParser()
    entries = wp.fetch('Россия')
    print(f"{len(entries)} entries found")
    for entry in entries:
        print(entry)
