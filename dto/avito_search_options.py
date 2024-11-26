from typing import Optional
from dataclasses import dataclass

from transliterate import translit

@dataclass
class AvitoSearchOptions:
    text: str
    region: Optional[str] = None
    page: int = 1

    def build_url(self):
        return f'{'all' if self.region is None else translit(self.region.lower(), reversed=True)}?cd=1&p={self.page}&q={self.text.strip().replace(' ', '+')}'