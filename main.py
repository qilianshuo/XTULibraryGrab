#!/usr/bin/python
# -*- coding: UTF-8 -*-
import configparser

from LibraryAPI import LibraryAPI
from utils import block

config = configparser.RawConfigParser()
config.read('config.ini')

if __name__ == '__main__':
    users = config.get('account', 'user').split(',')

    thread_pool = []
    for user in users:
        link = config.get(user, 'link')
        lib_id = config.get(config.get(user, 'room'), 'lib_id')
        seat_coordinate = config.get(config.get(user, 'room'), config.get(user, 'seat'))
        thread_pool.append(LibraryAPI(link, lib_id, seat_coordinate))

    start_time = config.get('option', 'start_time')
    block(start_time)

    for thread in thread_pool:
        thread.start()
