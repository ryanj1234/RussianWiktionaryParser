from wiktionaryparser import WiktionaryParser

if __name__ == '__main__':
    wp = WiktionaryParser()
    entries = wp.fetch('пила')
    print(f"{len(entries)} entries found")
    for entry in entries:
        print(entry)
