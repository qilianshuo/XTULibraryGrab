#!/usr/bin/python
# -*- coding: UTF-8 -*-
import re
import time
import execjs
import requests

from db import get_db


def insert_str(str_1: str, str_2: str, index: int) -> str:
    """
    Insert str2 to str1
    :param str_1: str to be inserted
    :param str_2: str to insert
    :param index: insert position
    :return: The new str
    """
    str_list = list(str_1)
    str_list.insert(index, str_2)
    return ''.join(str_list)


def get_seat_key(html: str) -> str:
    js_url = re.findall(r'(https://static.wechat.v2.traceint.com/template/theme2/cache/layout/.*?\.js)', html)
    if not js_url:
        js_url = re.findall(r'(http://static.wechat.v2.traceint.com/template/theme2/cache/layout/.*?\.js)', html)
    if not js_url:
        log_print("Failed to access the js url")
        raise SystemError
    js_url = js_url[0]

    sq = get_db()
    cache = sq.execute("""SELECT * FROM CACHE WHERE URL=?""", (js_url,)).fetchone()
    if cache is None:
        js_code = requests.get(js_url).content.decode('utf-8')
        try:
            key_code = re.findall(r'AJAX_URL\+"libid="\+[a-zA-Z]\+"&"\+(.*?)\+"="', js_code)[0]
        except IndexError:
            log_print("Failed to access the key!")
            raise SystemError

        js_code = re.sub(r'T.ajax_get\(.*\)', '', js_code)  # Remove redundant code
        final_code = insert_str(js_code, 'return ' + key_code, -2)

        ctx = execjs.compile(final_code)
        seat_key = ctx.call('reserve_seat')
        sq.execute("""INSERT INTO CACHE(url, content, key) values (?,?,?)""", (js_url, final_code, seat_key))
        sq.commit()
        log_print("Get from web: " + seat_key)
    else:
        log_print("Get key from database: " + cache[2])
        seat_key = cache[2]
    sq.close()
    return seat_key


def log_print(log) -> None:
    """
    Print the log with time
    :param log: Info to printed
    :return: None
    """
    print(time.strftime("[%m-%d %H:%M:%S] ", time.localtime()), end='')
    print(log)


def block(start_time: str) -> None:
    """
    Block the program until start_time
    :param start_time: The time to execute program
    :return: None
    """
    hour, minute = start_time.split(":")
    while True:
        if time.localtime(time.time())[3] == int(hour) and time.localtime(time.time())[4] >= int(minute):
            break
