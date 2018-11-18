### Тестовое задание R_E_G.RU

Скрипт берет список доменов, для каждого домена скачивает главную страницу сайта,
очищает html форматирование, добавляет в первые три строчки
title, meta:description, meta:keywords, записывает получившиеся данные
в выходную директорию и сохраняет результат в выходном csv файле

Все файлы сохраняются в кодировке utf-8.
Сайты с битыми кодировками не обрабатываются.

#### Запуск

Запуск в среде Pyhton 3.6 + aiohttp

`python regru.py`

Запуск в docker 

`docker build -t regru .&&docker run --rm -it -v $(pwd):/code regru python regru.py`

Запуск в docker-compose

`docker-compose up --build`

