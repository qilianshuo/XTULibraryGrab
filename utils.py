#!/usr/bin/python
# -*- coding: UTF-8 -*-
import re
import time
import js2py
import requests


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
    """
    Update: Remove cache mode; use js2py instead of execjs
    :param html: Html page
    :return: key
    """
    # TODO Match url not only use regular seat but also open room
    js_url = re.findall(r'(https://static.wechat.v2.traceint.com/template/theme2/cache/layout/.*?\.js)', html)
    if not js_url:
        js_url = re.findall(r'(http://static.wechat.v2.traceint.com/template/theme2/cache/layout/.*?\.js)', html)
    if not js_url:
        raise SystemError("Failed to access the js url")
    js_url = js_url[0]

    js_code = requests.get(js_url).content.decode('utf-8')
    try:
        key_code = re.findall(r'AJAX_URL\+"libid="\+[a-zA-Z]\+"&"\+(.*?)\+"="', js_code)[0]
    except IndexError:
        raise SystemError("Failed to access the key!")

    js_code = re.sub(r'T.ajax_get\(.*\)', '', js_code)  # Remove redundant code
    final_code = insert_str(js_code, 'return ' + key_code, -2)

    # ctx = execjs.compile(final_code)
    # seat_key = ctx.call('reserve_seat')
    context = js2py.EvalJs()
    context.execute(final_code)
    try:
        seat_key = context.reserve_seat()
        log_print("Use key: " + seat_key)
        return seat_key
    except (LookupError, OSError):
        log_print('[log]\n' + js_code)
        raise SystemError('Failed to execute the js!')


def log_print(log) -> None:
    """
    Print the log with time
    :param log: Info to printed
    :return: None
    """
    print(time.strftime("[%m-%d %H:%M:%S:", time.localtime()), end='')
    print('%d] ' % int((time.time() % 1) * 1000), end='')
    print(log)


def block(start_time: str) -> None:
    """
    Block the program until start_time
    :param start_time: The time to execute program
    :return: None
    """
    if start_time is None:
        return
    hour, minute = start_time.split(":")
    while True:
        if time.localtime(time.time())[3] == int(hour) and time.localtime(time.time())[4] >= int(minute):
            break


def get_lib_id(url: str) -> str:
    """
    Find lib_id in url
    :param url: Room URL
    :return: lib_id
    """
    pattern = re.compile(r'libid=(\d+)\.html')
    try:
        return pattern.findall(url)[0]
    except IndexError:
        log_print('URL is incorrect: ' + url)
        raise SystemError
