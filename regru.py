"""
Тестовое задание REG.RU
=======================

Скрипт берет список доменов, для каждого домена скачивает главную страницу сайта,
очищает html форматирование, добавляет в первые три строчки
title, meta:description, meta:keywords, записывает получившиеся данные
в выходную директорию и сохраняет результат в выходном csv файле

Все файлы сохраняются в кодировке utf-8.
Сайты с битыми кодировками не обрабатываются.

"""
import aiohttp
import asyncio

import os
import ssl
from html.parser import HTMLParser

# ===========================================
# Конфигурация

# Имя файла со списком доменов
DOMAIN_LIST = 'domains-list.csv'

# Имя выходного файла с таблицей результатов
OUTPUT_FILENAME = 'result.csv'

# Директория со скачанными и обработанными файлами
DOWNLOAD_DIR = './downloads/'

# Максимальное число одновременных соединений
MAX_CONNECTIONS = 100


# ===========================================
# html parser
# Можно сделать более аккуратно, например ожидать title внутри head и т.п.
# или использовать Beautiful Soup, зависит от задачи.


class Parser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.reset()
        self.data = []
        self.title = ''
        self.keywords = ''
        self.description = ''
        self.state = {}

    def error(self, message):
        self.data.append('Error {}'.format(message))

    def handle_starttag(self, tag, attrs):
        # print(tag,attrs)
        if tag == 'title':
            self.state['title'] = 1
        elif tag == 'meta':
            dattrs = {k: v for k, v in attrs}
            try:
                if dattrs['name'] == 'keywords':
                    self.keywords = dattrs['content']
                elif dattrs['name'] == 'description':
                    self.description = dattrs['content']
            except KeyError:
                pass

    def handle_data(self, data):
        if 'title' in self.state:
            self.title = data
            del self.state['title']
        self.data.append(data)

    def get_result(self):
        return '{}\n{}\n{}\n{}'.format(self.title, self.description, self.keywords, ''.join(self.data))


# ===========================================
# Подготовительные операции

# Читаем входной csv файл
# Можно использовать pandas или csv, но так как формат известен проще всего распарсить вручную
# df = pandas.read_csv(DOMAIN_LIST, usecols=[1])

with open(DOMAIN_LIST) as f:
    domains = [s.rstrip().split(',')[1] for s in f][1:]

# domains = domains[:500]
# domains = ['кто.рф']

total = len(domains)
processed = 0

print('==================================')
print('REG.RU Scrap domains test task\n{} domains to process'.format(len(domains)))
print('==================================\n\n')

# Готовим файл с результатами, будем добавлять в него записи по мере обработки
with open(OUTPUT_FILENAME, 'w') as f:
    f.write('dname,status,flag\n')

# ===========================================
# Рабочие корутины

# Семафор для ограничения количества одновременных соединений
sem = asyncio.Semaphore(MAX_CONNECTIONS)


async def fetch(session, domain):
    url = 'http://{}/'.format(domain)

    def log(s):
        print('{}: {}'.format(url, s))

    status = None
    flag = 0

    async with sem:
        try:
            async with session.get(url) as response:
                status = response.status
                log('Connected, STATUS: {}'.format(status))

                if status == 200:
                    doc = await response.text()
                    parser = Parser()
                    parser.feed(doc)
                    data = parser.get_result()

                    fn = os.path.join(DOWNLOAD_DIR, '{}.txt'.format(domain))
                    try:
                        with open(fn, 'wb') as f:
                            f.write(data.encode('utf-8'))
                            flag = 1
                    except IOError:
                        print("{}: Can't write file {}".format(url, fn))

        except aiohttp.ClientError as e:
            log('Not connected, ERROR: {}'.format(e))

        except UnicodeError as e:
            log("Bad charset, ERROR: {}".format(e))

        with open(OUTPUT_FILENAME, 'ab') as f:
            f.write('{},{},{}\n'.format(
                domain,
                'NULL' if status is None else status,
                flag
            ).encode('utf-8'))

        global processed
        processed += 1

        if processed == total or processed % 50 == 1:
            print('========== Progress: {} of {} domains processed'.format(processed, total))


async def main():
    async with aiohttp.ClientSession() as session:
        await asyncio.wait([fetch(session, d) for d in domains])


# ===========================================
# Event loop

loop = asyncio.get_event_loop()


def exception_handler(loop, context):
    if isinstance(context['exception'], ssl.CertificateError):
        # игнорируем CertificateError, иначе оно вываливается в логах
        pass  # ignore todo: log it?
    else:
        loop.default_exception_handler(context)


loop.set_exception_handler(exception_handler)

loop.run_until_complete(main())

loop.close()

print('Finished')
