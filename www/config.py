#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Configuration
'''

import config_default

class Dict(dict):
    '''
    Simple dict but support access as x.y style.
    '''
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

def merge(defaults, override):
    r = {}
    for k, v in defaults.items():
        # defaults的k关键字也存在于override
        if k in override:
            # 且若defaults中k对应的v为一个字典, 用各自的关键字k所对应的v(两个字典)合并
            if isinstance(v, dict):
                r[k] = merge(v, override[k])  # 返回一个合并后的字典作为关键字k所对应的值
            # 若非字典, 直接赋值即可
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r

# 这个toDict的主要功能是添加一种点操作符取值方式a_dict.key，相当于a_dict['key']，这个功能不是必要的
def toDict(d):
    D = Dict()
    for k, v in d.items():
        D[k] = toDict(v) if isinstance(v, dict) else v
    return D

configs = config_default.configs

try:
    import config_override
    configs = merge(configs, config_override.configs)
except ImportError:
    pass

configs = toDict(configs)