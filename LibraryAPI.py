#!/usr/bin/python
# -*- coding: UTF-8 -*-
import re
import threading
import requests

from utils import log_print, get_seat_key


class LibraryAPI(threading.Thread):
    api = {
        'DATA_URL': 'https://wechat.v2.traceint.com/data/',
        'STATIC_URL': 'https://static.wechat.v2.traceint.com/static/',
        'HOST': 'https://wechat.v2.traceint.com',
        'SELECT_URL': 'https://wechat.v2.traceint.com/index.php/reserve/get/libid=%s&%s=%s&yzm=',
        'INDEX_URL': 'https://wechat.v2.traceint.com/index.php/reserve/index.html',
        'HOLD_SUBMIT_URL': 'https://wechat.v2.traceint.com/index.php/hold/ajaxsubmit.html',
        'HOLD_CANCEL_URL': 'https://wechat.v2.traceint.com/index.php/hold/cancle.html',
        'seat_list_url': 'https://wechat.v2.traceint.com/index.php/reserve/mylist.html'
    }

    def __init__(self, login_link, lib_id, seat_coordinate):
        self.session = requests.session()
        self.session.headers = {
            'Host': 'wechat.v2.traceint.com',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/85.0.4183.102 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
                      '*/*;q=0.8,application/signed-exchange;v=b3;q=0.9,',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }

        self.login_link = login_link
        self.lib_id = lib_id
        self.seat_coordinate = seat_coordinate
        super().__init__()

    def login(self) -> str:
        resp = self.session.get(self.login_link)
        resp.encoding = resp.apparent_encoding
        if 'https://wechat.v2.traceint.com/index.php' in resp.url:
            log_print('Successful login.')
            return resp.text
        else:
            log_print('Login failed.')
            raise SystemError

    def check_status(self) -> int:
        """
        The status of select
        :return: 0 or 1 or 2
        """
        html = self.session.get(self.api['INDEX_URL'])
        if '学习中' in html:
            return 1
        elif '暂留中' in html:
            return 2
        else:
            return 0

    def find_room(self) -> dict:
        """
        Find room which has free seats
        :return: {room_name: room_url}
        """
        resp = self.session.get(self.api['INDEX_URL'])
        resp.encoding = resp.apparent_encoding

        list_group = re.findall(r'<div class="list-group".*?>([\s\S]*?)</div>', resp.text)
        if list_group is None:
            log_print('Failed to match room list')
            return {}
        # room_list: [(room_url, room_name, room_status),]
        room_list = re.findall(
            r'<a href=".*?" data-url="(.*?)".*?><.*?>(.*?)<.*?>(.*?)<.*?>',
            list_group[0].replace('\t', '').replace('\n', ''))

        vacant_room = {}
        for room in room_list:
            if room[2] == 'close':
                continue
            if int(room[2].split('/')[0]):
                vacant_room[room[1]] = self.api['HOST'] + room[0]

        if not vacant_room:
            log_print('No free room.')
            return vacant_room
        else:
            log_print('Successfully found an empty room!')
            return vacant_room

    def find_seat(self, lib_id: str) -> dict:
        """
        For some historical reasons, lib_id might be a number or a link. So it's needed to judge its type
        :param lib_id: room id or room link
        :return: {seat_id: seat_coordinate}
        """
        lib_id = str(lib_id)
        if 'http' not in lib_id:
            lib_id = self.api['HOST'] + lib_id
        resp = self.session.get(url=lib_id)
        resp.encoding = resp.apparent_encoding

        pattern = re.compile(r'<div class="grid_cell {2}grid_1" data-key="(.*?)".*?><em>(\d+)</em></div>')
        seat_list = pattern.findall(resp.text.replace('\n', ''))
        vacant_seat = {}
        if seat_list:
            # TODO Remove test code
            get_seat_key(resp.text)
            for seat in seat_list:
                vacant_seat[seat[1]] = seat[0]
            log_print('Successful found a seat.')
            return vacant_seat
        else:
            log_print('Nothing...')
            return vacant_seat

    def select(self, lib_id=None, seat_coordinate=None, key=None) -> bool:
        """
        Access the seat selection api to select seat
        :param lib_id: The room to select
        :param seat_coordinate: seat_coordinate such as '22,7'
        :param key: Calculate by a js_file
        :return: Seat selection results
        """
        select_url = self.api['SELECT_URL'] % (lib_id, key, seat_coordinate)
        result = self.session.get(url=select_url).json()
        log_print(result['msg'])
        # TODO Waiting to be tested.
        if result['code'] == 0:
            return True
        else:
            return False

    def withdraw(self):
        """
        Withdraw the selected seat
        :return:
        """
        data = self.session.post('https://wechat.v2.traceint.com/index.php/reserve/token.html',
                                 data={'type': 'cancle'}).json()
        token = data['msg']
        resp = self.session.post('https://wechat.v2.traceint.com/index.php/cancle/index', data={'t': token})
        log_print(resp.json())

    def grab(self, lib_id, seat_coordinate) -> bool:
        """
        Quick select the aim seat
        :param lib_id: Room to select
        :param seat_coordinate: Seat to select
        :return: Select results
        """
        index_html = self.login()
        key = get_seat_key(index_html)
        return self.select(lib_id, seat_coordinate, key)

    def monitor(self) -> bool:
        """
        Monitor the free seat and select it
        :return: Select results
        """
        # TODO Logic optimization
        if not self.login():
            return False

        room_list = self.find_room()
        while not room_list:
            room_list = self.find_room()
        room = room_list[list(room_list.keys())[0]]

        seat_list = self.find_seat(room)
        seat = seat_list[list(seat_list.keys())[0]]

        resp = self.session.get(room)
        key = get_seat_key(resp.text)
        self.select(room, seat, key)

    def signin(self) -> bool:
        """
        Signin to access five point
        :return: Status of signin
        """
        html = self.session.get('https://wechat.v2.traceint.com/index.php/usertask/index.html').text
        try:
            task_id = re.findall(r'/index.php/usertask/detail/id=(\d+).html', html)[0]
        except IndexError:
            return False
        result = self.session.post(
            'https://wechat.v2.traceint.com/index.php/usertask/ajaxdone.html',
            data={'id': task_id}).json()
        log_print(result)
        return True if result['code'] == 0 else False

    def hold_submit(self):
        # TODO Code is to be verified.
        data = self.session.get('https://wechat.v2.traceint.com/index.php/hold/ajaxsubmit/doit=confirm.html').json()
        token = data['data']['token']
        resp = self.session.post(self.api['HOLD_SUBMIT_URL'], data={'token': token})
        log_print(resp.json())

    def hold_cancel(self):
        # TODO Code is to be verified.
        data = self.session.post('https://wechat.v2.traceint.com/index.php/reserve/token.html',
                                 data={'type': 'hold_cancle'}).json()
        token = data['msg']
        resp = self.session.post(self.api['HOLD_CANCEL_URL'], data={'token': token})
        log_print(resp.json())

    def run(self) -> None:
        """
        :return: None
        """
        self.grab(self.lib_id, self.seat_coordinate)
        log_print("Test Flag")
        self.signin()
