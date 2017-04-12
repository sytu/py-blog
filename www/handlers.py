import asyncio, inspect, logging

def get(path):
    '''
    Define decorator @get('/path')
    '''
    def decorator(func):
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
        def wrapper(*args, **kw):
            return func(*args, *kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator

class RequestHandler(object):
    def __init__(self, app, fn):
        self.__app = app
        self.__fn = fn

    @asyncio.coroutine
    def __call__(self, request):
        kw = ...
        r = yield from self.__fn(**kw)
        return r

def add_route(app, fn):
    method = fn.getattr(fn, '__method__', None)
    path = fn.getattr(fn, '__route__', None)
    if method is None or path is None:
        raise ValueError('@GET or @POST not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgenertorfunction(fn):
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
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)






































































