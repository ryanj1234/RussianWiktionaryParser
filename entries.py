from abc import ABC


class WordEntry(ABC):
    def __init__(self, word, *args, **kwargs):
        self.word = word
        self.audio_file = None
        self.part_of_speech = None
        self.definitions = None


class WordDefinition(ABC):
    def __init__(self):
        self._text = ''
        self._examples = []

    @property
    def text(self):
        return self._text

    @property
    def examples(self):
        return self._examples


class WordExample(ABC):
    def __init__(self):
        self._text = ''
        self._translation = ''

    @property
    def text(self):
        return self._text

    @property
    def translation(self):
        return self._translation
