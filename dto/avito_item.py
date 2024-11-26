from typing import Dict, Any

import datetime
from enum import Enum
from dataclasses import dataclass
from bs4 import BeautifulSoup
import dateparser

from curl_cffi.requests.models import Response
from loguru import logger


class AvitoItemStatus(Enum):
    ACTIVE = 'active'
    CLOSE = 'close'

# Парсинг страницы товара
@dataclass
class AvitoItemParse:
    id: int
    name: str
    price: int
    address: str
    descriptrion: str
    publication_date: datetime
    watch_count: int
    url: str
    status: AvitoItemStatus = AvitoItemStatus.ACTIVE

    @classmethod
    def parse(cls, response: Response):
        soup = BeautifulSoup(response.content, 'html.parser')
        return cls(
            id = soup.select_one('span[data-marker="item-view/item-id"]').text.strip().split()[1],
            price = soup.select_one('div[data-marker="item-view/item-price-container"]').text.strip().split()[0],
            name = soup.select_one('h1[data-marker="item-view/title-info"]').text.strip().split(),
            address = soup.select_one('div[itemprop="address"] span').text.strip(),
            descriptrion = soup.select_one('div[data-marker="item-view/item-description"]').text.strip(),        
            publication_date = dateparser.parse(soup.select_one('span[data-marker="item-view/item-date"]').text.strip()[2:]),
            watch_count=soup.select_one('span[data-marker="item-view/total-views"]').text.strip().split()[0],
            url = response.url
        )

def avito_item_parse(response: Response) -> Dict[str, Any]:
    soup = BeautifulSoup(response.content, 'html.parser')
    return {
        "id": soup.select_one('span[data-marker="item-view/item-id"]').text.strip().split()[1],
        "price": soup.select_one('div[data-marker="item-view/item-price-container"]').text.strip().split()[0],
        "name": soup.select_one('h1[data-marker="item-view/title-info"]').text.strip(),
        "address": soup.select_one('div[itemprop="address"] span').text.strip(),
        "descriptrion": soup.select_one('div[data-marker="item-view/item-description"]').text.strip(),        
        "publication_date": dateparser.parse(soup.select_one('span[data-marker="item-view/item-date"]').text.strip()[2:]),
        "watch_count": soup.select_one('span[data-marker="item-view/total-views"]').text.strip().split()[0],
        "url": response.url
    }