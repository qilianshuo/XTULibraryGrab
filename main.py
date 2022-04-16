#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import argparse
import configparser

from LibraryAPI import LibraryAPI

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
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', default='grab')
    args = parser.parse_args()

    thread_pool = []
    for user in users:
        link = config.get(user, 'link')
        lib_id = config.get(config.get(user, 'room'), 'lib_id')
        seat_coordinate = config.get(config.get(user, 'room'), config.get(user, 'seat'))
        thread_pool.append(LibraryAPI(link, lib_id, seat_coordinate, start_time=config.get('option', 'start_time')))

    if args.mode == 'grab':
        for thread in thread_pool:
            thread.start()

    elif args.mode == 'withdraw':
        for thread in thread_pool:
            thread.login()
            thread.withdraw()

    elif args.mode == 'monitor':
        for thread in thread_pool:
            thread.monitor(_filter=[
                '三楼东走廊自习区(3楼)',
                '三楼西走廊自习区(3楼)',
                '四楼东走廊自习区(4楼)',
                '四楼南自习区(4楼)',
                '四楼西走廊自习区(4楼)',
                '5楼自习室(5楼)',
                '6楼自习室(6楼)',
                '7楼自习室(7楼)'
            ])

    elif args.mode == 'test':
        print('Hello world!')
        # thread.login()
        # thread.withdraw()
        # print(thread.get_room_list())
