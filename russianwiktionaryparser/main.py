from russianwiktionaryparser.wiktionaryparser import WiktionaryParser
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    wp = WiktionaryParser()
    entries = wp.fetch('изумленный')
    for entry in entries:
        print(entry)
