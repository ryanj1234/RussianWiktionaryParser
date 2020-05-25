from wiktionaryparser import WiktionaryParser
import logging

logging.basicConfig(level=logging.INFO)
if __name__ == '__main__':
    wp = WiktionaryParser()
    entries = wp.fetch('сказать')
    wp.download_audio(entries[0].audio_links[0], '.')
