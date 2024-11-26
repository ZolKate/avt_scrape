import argparse
from typing import Optional
from queue import Queue
import time

from loguru import logger
from curl_cffi import requests
from curl_cffi.requests.exceptions import HTTPError  
from sqlalchemy import select
from bs4 import BeautifulSoup
import pandas as pd

from orm import Database
from orm.repos.avito_item import AvitoItemService
from orm.models.avito_item import AvitoItems
from dto import AvitoSearchOptions, avito_item_parse


# Максимальное кол-во объявлений у поиска - 5000
# Максимальное кол-во ссылок на странице - 50
# На пагинацию на странице поиска не надо обращать внимание,
# так как не всегда эти страницы и правда существуют

# Изначальная идея была создать очередь из задач (ссылок для парсинга с поисковой выдачи)
# И при помощи asyncio запустить ограниченное количество воркеров для этого
# Однако поставить нормально proxy_rotate, и в целом хоть одну прокси на aiohttp не вышло
# Поэтому синхронный парсер


TIMEOUT = 20
MAX_RETRIES = 3

class TooManyRequests(HTTPError):
    ...

class AvitoSearchScrapper:
    base_url: str = 'https://www.avito.ru'
    active_page: int = 1
    urls_queue: Queue = Queue()

    def __init__(self, service: AvitoItemService, search_options: AvitoSearchOptions):
        self.service = service
        self.search_options = search_options
        self.client = requests.Session(
            base_url=self.base_url, impersonate='chrome'
        )

    def start(self):
        self.parse_page()
        self.parse_items()

    def __request(self, url: str):
        for attempt in range(MAX_RETRIES):
            try:
                res = self.client.get(url)
                res.raise_for_status()
                return res
            except HTTPError as e:
                logger.error(f'{e.__class__.__name__}: {str(res.status_code)}')
                if res.status_code == 429:
                    logger.info('Retry')
                    time.sleep(TIMEOUT)
                    if attempt == MAX_RETRIES:
                        raise TooManyRequests(str(e)) from e

    def parse_page(self):
        try:
            res = self.__request(url=f'{self.search_options.build_url()}')
        except TooManyRequests as e:
            self.start()
        soup = BeautifulSoup(res.text, 'html.parser')
        urls = soup.select('div[data-marker="catalog-serp"] a[data-marker="item-title"]')

        if urls:
            [self.urls_queue.put(f'{url.attrs.get('href')}') for url in urls]
            self.search_options.page += 1
            self.parse_page()
        else:
            logger.info('No more results')
            return

    def parse_items(self):
        # chunk = []
        while not self.urls_queue.empty():
            res = self.__request(url=self.urls_queue.get())
            time.sleep(20)
            scraped = avito_item_parse(res)
            
            logger.info('Adding adv')
            if self.service.get_by_id(scraped["id"]) is not None:
                self.service.update(AvitoItems(**scraped))
            else:
                self.service.create(AvitoItems(**scraped))
            # chunk.append(AvitoItems(**avito_item_parse(res)))
        
        # self.service.create_all(chunk)

def start(search: str, region: Optional[str] = None):
    Database.create_database()
    with Database.session() as session:

        AvitoSearchScrapper(
            AvitoItemService(session),
            AvitoSearchOptions(text=search, region=region)
        ).start()

        advs = [item.to_dict() for item in AvitoItemService(session).get_all()]
        df = pd.DataFrame(advs)
        writer = pd.ExcelWriter('avito.xlsx', datetime_format="YYYY-MM-DD HH:MM:SS")
        df.to_excel(writer)
        writer.close()
        

if __name__ == "__main__":

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-s", '--search', required=True)
    parser.add_argument("-r", '--region')
    args = parser.parse_args()
    start(args.search, args.region)