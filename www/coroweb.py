#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio, os, inspect, logging, functools

from urllib import parse

from aiohttp import web

from apis import APIError

def get(path):
    '''
    Define decorator @get('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator

def post(path):
    '''
    Define decorator @post('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator

def get_required_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

def get_named_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)

def has_named_kw_args(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True

def has_var_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True

def has_request_arg(fn):
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == 'request':
            found = True
            continue
        if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
    return found

# 以下是个适配器，它把用户自定义参数的各种奇形怪状handler处理函数适配成了标准的 handler(request)调用
# RequestHandler的主要作用:
# 1. 构成标准的app.router.add_route的第三个参数(需要一个接受request的url处理函数)
# 2. 获取不同的函数的对应的参数
class RequestHandler(object):

    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)           # 是否有request参数
        self._has_var_kw_arg = has_var_kw_arg(fn)             # 是否有变长字典参数
        self._has_named_kw_args = has_named_kw_args(fn)       # 是否存在关键字参数
        self._named_kw_args = get_named_kw_args(fn)           # 所有关键字参数
        self._required_kw_args = get_required_kw_args(fn)     # 所有没有默认值的关键字参数

    async def __call__(self, request):
        kw = None
        # required_kw_args是named_kw_args的真子集，第三个条件多余
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            if request.method == 'POST':
                if not request.content_type:
                    return web.HTTPBadRequest('Missing Content-Type.')
                ct = request.content_type.lower()
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('JSON body must be object.')
                    kw = params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)
            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]
        # 如果没有在GET或POST取得参数，直接把match_info的所有参数提取到kw
        if kw is None:
            kw = dict(**request.match_info)
        else:
            # 如果没有变长字典参数且有关键字参数，把所有关键字参数提取出来，忽略所有变长字典参数
            if not self._has_var_kw_arg and self._named_kw_args:
                # remove all unamed kw:
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            # 把match_info的参数提取到kw，检查URL参数和HTTP方法得到的参数是否有重合
            for k, v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw args: %s' % k)
                kw[k] = v
        # 把request参数提取到kw
        if self._has_request_arg:
            kw['request'] = request
        # 检查没有默认值的关键字参数是否已赋值
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest('Missing argument: %s' % name)
        # 调用
        logging.info('call with args: %s' % str(kw))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)

# 把URL参数和GET、POST方法得到的参数彻底分离。
# GET、POST方法的参数必需是KEYWORD_ONLY
# 1. URL参数是POSITIONAL_OR_KEYWORD
# 2. REQUEST参数要位于最后一个POSITIONAL_OR_KEYWORD之后的任何地方
# http://www.qiangtaoli.com/bootstrap/?tag=Refactoring 的正确的写法是：
# @get('/{template}/')
# async def home(template, *, tag='', page='1', size='10'):
#     # 这里会传进去两个参数：template=bootstrap, tag=Refactoring
#    pass

@get('/{template}/')
async def home(template, *, tag='', page='1', size='10'):
    # 这里会传进去两个参数：template=bootstrap, tag=Refactoring
   pass

def add_static(app):
    # 假设当前目录'.'为/Users/sytu/workspace/python/learn-pylxf/py-blog/
    # >>> os.path.dirname(os.path.abspath('.'))
    # => '/Users/sytu/workspace/python/learn-pylxf/py-blog'
    # >>> os.path.join(os.path.dirname(os.path.abspath('www')), 'static') 拼接两个路径     'www'是当前路径下的www目录
    # => '/Users/sytu/workspace/python/learn-pylxf/py-blog/www/static'
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))

def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))
    # inspect.signature(fn).parameters.keys() returns the parameter of fn in as a list
    app.router.add_route(method, path, RequestHandler(app, fn))

def add_routes(app, module_name):
    # 在模块名字中搜索右起第一个'.'的下标, 若无返回-1:
    n = module_name.rfind('.')
    if n == (-1):
        # 动态导入一个模块
        # __import__(name, globals=None, locals=None, fromlist=(), level=0)
        # The function imports the module name, potentially using the given globals and locals to determine how to interpret the name in a package context. 
        # The fromlist gives the names of objects or submodules that should be imported from the module given by name. 
        # 由于不存在'.', 所以这个模块名就是要导入的模块, 不需要传入fromlist指定对象或子模块
        mod = __import__(module_name, globals(), locals())
    else:
        # 若存在'.', 则说明module_name形如xx.mod, mod存在于一个中pacakge中:
        # When the name variable is of the form package.module, 
        # normally, the top-level package (the name up till the first dot) is returned, not the module named by name.
        # However, when a non-empty fromlist argument is given, the module named by name is returned.
        # 由于要得到的是name如mod而不是包含它的package, 所以需要传入fromlist: [name]
        # 接下来 the module_name[:n] module 会被 __import__()返回      目前还不太清楚为什么要单单只传入package的名字, 可以测试一下
        # 由于传入了fromlist, the names to import are retrieved and assigned to their respective names.
        # 也就是说返回的是一个模块临时对象, 具有name属性, 该属性的值是name模块
        # 使用getattr将属性值得到
        name = module_name[n+1:]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    # 遍历获取模块中的url处理函数
    for attr in dir(mod):
        # 过滤掉_开头的成员
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)