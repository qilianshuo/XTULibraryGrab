#!/usr/bin/python
# -*- coding: UTF-8 -*-
import configparser

from LibraryAPI import LibraryAPI

# from utils import block

config = configparser.RawConfigParser()
config.read('config.ini')

if __name__ == '__main__':
    """
    本次测试：
    1. 在main进程取消阻塞
    2. 在LibraryAPI.grab方法中增加抢座时间参数
    3. ……
    """
    users = config.get('account', 'user').split(',')

    thread_pool = []
    for user in users:
        link = config.get(user, 'link')
        lib_id = config.get(config.get(user, 'room'), 'lib_id')
        seat_coordinate = config.get(config.get(user, 'room'), config.get(user, 'seat'))
        thread_pool.append(LibraryAPI(link, lib_id, seat_coordinate, start_time=config.get('option', 'start_time')))

    for thread in thread_pool:
        thread.start()
        # thread.login()
        # thread.withdraw()
        # print(thread.get_room_list())
