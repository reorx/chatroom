#!/usr/bin/env python
# -*- coding: utf-8 -*-

TEMPLATE_PATH = 'templates'


CONNS = {
    'mongodb': {
        'master': {
            'username': 'None',
            'keep_time': 7200,
            'host': '127.0.0.1',
            'database': 'chatroom',
            'password': 'None',
            'port': 27017
        }
    },
}

UNLOG_URLS = [
    '/favicon.ico',
    '/static'
]

COOKIE_SECRET = 'P0UTa5iuRaaVlV8QZF2uVR7hHwTOSkQhg2Fol18OKwc='
