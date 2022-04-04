#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sqlite3


def get_db():
    return sqlite3.connect('database.db')


def init_db():
    with open('schema.sql', 'r', encoding='utf-8') as f:
        get_db().executescript(f.read())
