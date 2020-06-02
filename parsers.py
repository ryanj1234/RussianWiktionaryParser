from abc import ABC, abstractmethod
from entries import WordEntry


class Parser(ABC):
    @abstractmethod
    def fetch(self, word) -> [WordEntry]:
        pass

    @abstractmethod
    def can_handle_entry(self, entry: any) -> bool:
        pass
