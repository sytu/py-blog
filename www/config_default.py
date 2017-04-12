#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
生产环境的标准配置
'''

configs = {
    'db': {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'pyblog-data',
        'password': '28',
        'database': 'pyblog'
    },
    'session': {
        'secret': 'SyTuAcNh'
    }
}