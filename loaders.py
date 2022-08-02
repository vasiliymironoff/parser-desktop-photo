import asyncio
import time
import aiofiles
import aiohttp
import requests
from bs4 import BeautifulSoup
import os
from util import get_headers
import math
import progressbar


class LoaderPhoto:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self._set_root_url()
        self.name_dir = 'images'

        self.count_photo = 0
        self.final_count_photo = int(input('Введите количество фотографий: '))

        self._create_directory()

        # self.widgets = ['Loading: ', progressbar.AnimatedMarker()]
        self.widgets = [
            'Загружено ', progressbar.Counter(), '/', str(self.final_count_photo),

        ]
        self.bar = progressbar.ProgressBar(widgets=self.widgets, maxval=self.final_count_photo).start()

    def _set_root_url(self) -> None:
        start_url = 'https://www.goodfon.ru/'
        response = requests.get(start_url, headers=get_headers()).text
        soup = BeautifulSoup(response, 'lxml')
        dict_category = dict()
        for a in soup.find('div', class_='head_menu').find_all('a'):
            dict_category[a.text.lower()] = a.get('href')
        print('Выберите категорию: ')
        max_length = len(max(dict_category.keys(), key=lambda x: len(x)))

        for i, key in enumerate(dict_category):
            print(key.ljust(max_length), end=' ')
            if i % 4 == 0 and i != 0:
                print()
        print('\n')
        name_category = input('Название категории (любое другое слово для случайных фото): ')
        new_root_url = dict_category.get(name_category, None)
        if new_root_url is not None:
            self.root_url = new_root_url
            print(f'Выбрана категория - {name_category}')
        else:
            self.root_url = start_url
            print('Категория не выбрана')

    def _create_directory(self):
        try:
            os.mkdir(self.name_dir)
        except FileExistsError:
            pass
        else:
            print('Папка images создана')


class SyncLoaderPhoto(LoaderPhoto):
    def __init__(self, verbose):
        super().__init__(verbose)

    def _download_photo(self, href: str) -> None:
        response = requests.get(href, headers=get_headers()).text
        soup = BeautifulSoup(response, 'lxml')
        src = soup.find('img', class_='wallpaper__item__fon__img').get('src')

        name_file = src.split("/")[-1]
        with open(f'{self.name_dir}/{name_file}.jpg', 'wb') as f:
            f.write(requests.get(src, headers=get_headers()).content)
        if self.verbose:
            print(f'[+] {name_file}')

    def run(self) -> None:
        time_st = time.time()
        for count_page in range(1, 100):
            if count_page == 1:
                url = self.root_url
            else:
                url = f'{self.root_url}index-{count_page}.html'
            response_page = requests.get(url, headers=get_headers()).text
            soup = BeautifulSoup(response_page, 'lxml')
            n_tag_a = soup.find('div', class_='wallpapers').find_all('a', class_=None)
            for tag_a in n_tag_a:
                href = tag_a.get('href')
                self._download_photo(href)
                self.count_photo += 1
                self.bar.update(self.count_photo)
                if self.count_photo == self.final_count_photo:
                    break
            else:
                continue
            break

        print(
            f'\nЗагрузка завершена. Скачано {self.final_count_photo} фото. Время: {round(time.time() - time_st, 2)} секунд.')


class DownloadEnd(Exception):
    pass


class AsyncLoaderPhoto(LoaderPhoto):
    def __init__(self, verbose):
        super().__init__(verbose)
        self.connector = aiohttp.TCPConnector(limit=150)
        self.count_append_download_photo = 0

    async def _download_photo(self, href):
        async with aiohttp.ClientSession() as session:
            async with session.get(href, headers=get_headers()) as response:
                answer = await response.text()
            soup = BeautifulSoup(answer, 'lxml')
            try:
                src = soup.find('img', class_='wallpaper__item__fon__img').get('src')
            except AttributeError:
                pass
            else:
                name_file = src.split("/")[-1]
                try:
                    async with aiofiles.open(f'{self.name_dir}/{name_file}.jpg', 'wb') as f:
                        async with session.get(src, headers=get_headers()) as response:
                            file = await response.read()
                        await f.write(file)
                except Exception as e:
                    if self.verbose:
                        print('[-]', e)
                    self.count_photo -= 1
                else:
                    if self.verbose:
                        print('[+]', name_file.ljust(50))
                    self.count_photo += 1
                    self.bar.update(self.count_photo)

    def _open_page_with_photo(self, url) -> list:
        response_page = requests.get(url, headers=get_headers()).text
        soup = BeautifulSoup(response_page, 'lxml')
        n_tag_a = soup.find('div', class_='wallpapers').find_all('a', class_=None)
        n_href_photo = []
        for tag_a in n_tag_a:
            href = tag_a.get('href')
            if self.count_append_download_photo >= self.final_count_photo:
                break
            self.count_append_download_photo += 1
            n_href_photo.append(self._download_photo(href))
        return n_href_photo

    async def download_start(self):
        count_pages = math.ceil(self.final_count_photo / 24)
        print('Предварительная настройка. Это может занять некоторое время.')
        n_func = []
        for i in range(1, count_pages + 1):
            url = f'{self.root_url}index-{i}.html'
            n_func.extend([asyncio.create_task(i) for i in self._open_page_with_photo(url)])
        await asyncio.gather(*n_func)

    def run(self):
        time_st = time.time()
        asyncio.run(self.download_start())
        print('\nЗагрузка завершена. ', end='')
        s = int(time.time() - time_st)
        print(f'Скачано {self.count_photo} фото. Время: {s // 60} минут {s % 60} секунд.')
