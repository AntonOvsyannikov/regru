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
import re

import aiohttp
import asyncio

import os
import ssl
# from html.parser import HTMLParser
from bs4 import BeautifulSoup

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

def get(d, key, default=None): return d.get(key, default) if d else default

def parse(doc):
    """Парсит скачанный html
    Парсит скачанный html, возвращает clear text, где первые три строчки это
    title, meta:keywords, meta:description
    """

    bs = BeautifulSoup(doc, "lxml")
    title = getattr(bs.find('title'), 'string', '')
    keywords = get(bs.find('meta', attrs={'name':'keywords'}), 'content', '')
    description = get(bs.find('meta', attrs={'name':'description'}), 'content', '')

    for s in bs('script'): s.extract()
    for s in bs('style'): s.extract()
    text = re.sub(r'\n+', '\n', getattr(bs.body, 'text', '').strip())

    return "{}\n{}\n{}\n{}".format(title, keywords, description, text)


# ===========================================
# Подготовительные операции

# Читаем входной csv файл
# Можно использовать pandas или csv, но так как формат известен проще всего распарсить вручную
# df = pandas.read_csv(DOMAIN_LIST, usecols=[1])

with open(DOMAIN_LIST) as f:
    domains = [s.rstrip().split(',')[1] for s in f][1:]

# domains = domains[200:500]
# domains = ['1nt-c.ru']

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
                    raw = await response.read()

                    data = parse(raw.decode(response.charset or 'utf-8', 'ignore') if raw else '')

                    fn = os.path.join(DOWNLOAD_DIR, '{}.txt'.format(domain))
                    try:
                        with open(fn, 'wt', encoding='utf-8') as f:
                            f.write(data)
                            flag = 1
                    except IOError:
                        print("{}: Can't write file {}".format(url, fn))

        except aiohttp.ClientError as e:
            log('Not connected, ERROR: {}'.format(e))

        except UnicodeError as e:
            log("UnicodeError, ERROR: {}".format(e))

        with open(OUTPUT_FILENAME, 'ab') as f:
            f.write('{},{},{}\n'.format(
                domain,
                'NULL' if status is None else status,
                flag
            ).encode('utf-8'))

        global processed
        processed += 1

        if processed == total or processed % 50 == 1:
            print('============================= Progress: {} of {} domains processed'.format(processed, total))


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
