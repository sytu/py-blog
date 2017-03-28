import logging; logging.basicConfig(level=logging.INFO)
import asyncio, time, os, json
from datetime import datetime
from aiohttp import web

def log(sql, args):
    logging.info('SQL: %s' % (sql))
# sql (str) – sql statement
# args (list) – tuple or list of arguments for sql query
# 如: yield from cursor.execute("SELECT * FROM t1 WHERE id=%s", (5,))
# sql: "SELECT * FROM t1 WHERE id=%s"   MySQL的占位符是%s
# args: (5,) 


@asyncio.coroutine
def create_pool(loop, **kw): # 连接池里是链接, 需要的时候来直接来拿就可以拿去使用了, 不必每次都mysql.connector.connect()重新连接
    logging.info('start creating database connection pool')
    global __pool
    __pool = yield from aiomysql.create_pool(
    # 可参考 [aiomysql api reference](http://aiomysql.readthedocs.io/en/latest/connection.html?highlight=autocommit)
        host = kw.get('host', 'localhost'),
        port = kw.get('port', 3306),
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('charset', 'utf-8'), 
        autocommit = kw.get('autocommit', True),  # 使得不用每次查询完conn.commit()提交事务
        maxsize = kw.get('maxsize', 10),
        minsize = kw.get('minsize', 1),
        loop = loop
    )


# 封装SELECT
@asyncio.coroutine
def select(sql, args, size=None):
    log(sql, args)
    global __pool
    # yield from 将会调用一个子协程，并直接返回调用的结果 
    # 下面的yield from从连接池中返回一个连接， 这个地方已经创建了进程池并和进程池连接了，进程池的创建被封装到了create_pool(loop, **kw)
    with (yield from __pool) as conn: # 从连接池取得一个连接 
        # 创造游标  
        cur = yield from conn.cursor(aiomysql.DictCursor) 
        # dict cursor: A cursor which returns results as a dictionary
        # fetchone()从dict cursor得到下一行协程 会得到类似如下结果
        # {'age': 20, 'DOB': datetime.datetime(1990, 2, 6, 23, 4, 56), 'name': 'bob'}
        yield from cur.execute(sql.replace('?', '%s'), args or ()) # 将SQL语句的占位符?，替换为MySQL的占位符%s
        # 协程cursor.execute的第一个参数接受sql字符串, 第二个参数接受传给sql语句的作为sql参数args元组, 若不存在则传入一个空元组
    if size: # 若有向size传入一个指定返回查询行数的参数size
        rs = yield from cur.fetchmany(size)
        # fetchmany: Coroutine the next set of rows of a query result, returning a list of tuples
        # The number of rows to fetch per call is specified by the parameter, 这里就是size
        # ex: fetchmany(2) => [(1, 100, "abc'def"), (2, None, 'dada')]
    else:
        rs = yield from cur.fetchall()
        # fetchall: Coroutine returns all rows of a query result set:
    yield from cur.close()
    #关闭游标. 但不用手动关闭conn，因为是在with语句里面，会自动关闭，因为是select，所以不需要提交事务(commit)
    logging.info('rows returned: %s', % len(rs)) # log查询结果的行数
    return rs # 返回一个含有row的字典


# 封装INSERT, UPDATE, DELETE  
@asyncio.coroutine
def execute(sql, args, autocommit=True):
    log(sql, args)
    global __pool
    with (yield from __pool) as conn: 
        try:
            cur = conn.cursor() # 这几个操作只需要普通的cursor
            yield from cur.execute(sql.replace('?', '%s'), args)  # args 对于这几个sql操作不能少
            affected_num = cur.rowcount # rowcount: 返回被影响的行数
            yield from cur.close()
            logging.info('executed: %s rows' % affected_num)
        except BaseException as e:
            raise
        return affected_num

# 这个函数主要是把查询字段计数 替换成sql识别的 values的参数 如:
# insert into  `User` (`password`, `email`, `name`, `id`) values (?,?,?,?)
def create_args_string(num):  
    return (','.join(['?' for i in range(num)])) 
    # print(create_args_string(4)) # => '?,?,?,?''


# ORM框架提供: 父类Model 和 属性类型StringField、IntegerField等

# 当用户定义一个class User(Model)时，Python解释器首先在当前类User的定义中查找metaclass，
# 如果没有找到，就继续在父类Model中查找metaclass，找到了就使用Model中定义的metaclass的ModelMetaclass来创建User类，
# 也就是说，metaclass可以隐式地继承到子类，但子类自己却感觉不到, 也不需要显式地设置metaclass。
# 子类如User的映射信息通过元类metaclass如ModelMetaClass读取出来

# ModelMetaclass元类定义了所有Model基类(继承ModelMetaclass)的子类实现的操作
# ModelMetaclass的工作主要是为一个数据库表映射成一个封装的类做准备：  
# 1. 读取具体子类(user)的映射信息  
# 2. 创造类的时候，排除对Model类的修改  
# 3. 在当前类中查找所有的类属性(attrs)，如果找到Field属性，就将其保存到__mappings__的dict中，同时从类属性中删除Field(防止实例属性遮住类的同名属性)  
# 4. 将数据库表名保存到__table__中  

# 基类Model的元类的定义: 
class ModelMetaclass(type):  # 由于metaclass是类的模板，所以必须从 type类 派生
    # __new__控制__init__的执行，所以在其执行之前  
    # cls:代表要__init__的类，此参数在实例化时由Python解释器自动提供(例如下文的User和Model)  
    # bases：代表继承父类的集合  
    # attrs：类的方法集合  
    def __new__(cls, name, bases, attrs):
            if name=='Model':       # 排除掉对Model类的修改
                return type.__new__(cls, name, bases, attrs)
            # 获取table名称 
            table_name=attrs.get('__table__', None) or name   #r如果存在表名，则返回表名，否则返回 name; __table__是User等Model子类的类属性表示 表名
            logging.info('found table: %s (table: %s) ' %(name,table_name ))  

            # 获取所有的Field和主键名:
            mappings = dict() # 定义一个空字典
            fields = []     # 定义一个空列表, 保存的将是除主键外的属性名
            primaryKey = None

            # attrs的items()存储的是类对象所有的属性与其值组成的元组作为元素的列表
            # 例子: attrs.items() = [('__module__', '__main__'), ('__qualname__', 'User'), ('name', <__main__.StringField object at 0x10a688470>)
            # , ('email', <__main__.StringField object at 0x10a6884a8>), ('id', <__main__.IntegerField object at 0x10a688438>), ('password', <__main__.StringField object at 0x10a6884e0>)]
            for k, v in attrs.items(): # k是类对象所有的属性其中包括字段名如name, v是该属性对应的值其中包括字段值如StringField类对象
                if isinstance(v, Field): # 若属性对应的值是Field的实例, 说明是v字段值, 其k就是个字段名
                    logging.info('found mapping: %s ==> %s' % (k, v)) # found mapping: email ==> <StringField:email>
                    mappings[k] = v # 向mappings字典添加一个以字段名为key, 字段值为value的键值对. 创造字段与字段值映射的集合
                                    # 类似mappings['email'] = <__main__.StringField object at 0x10a6884a8>
                    if v.primary_key:  # 若该字段是主键 由于一个表只能有一个主键，而且必须有一个主键 所有这里if内部在正确时最多只会执行一次
                        # 找到主键:
                        if primaryKey: # 若主键已存在
                            raise RuntimeError('Duplicate primary key for field: %s' % k) # 当再出现一个主键的时候就报错, 因为一个表只能有一个主键
                        primaryKey = k # 主键只能被设置一次
                    else:
                        fields.append(k) # 将不是主键的字段的名字如name, phone添加到fields列表
            if not primaryKey: # 如果主键不存在也将会报错，在这个表中没有找到主键，一个表只能有一个主键，而且必须有一个主键  
                raise RuntimeError('Primary key not found.')

            for k in mappings.keys():
                attrs.pop(k)

            escaped_fields = list(map(lambda f: '`%s`' % f, fields))
            attrs['__mappings__'] = mappings # 保存属性和列的映射关系
            attrs['__table__'] = tableName
            attrs['__primary_key__'] = primaryKey # 主键属性名
            attrs['__fields__'] = fields # 除主键外的属性名
            # 构造默认的SELECT, INSERT, UPDATE和DELETE语句:
            attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
            attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
            attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
            attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
            return type.__new__(cls, name, bases, attrs)
# 定义所有ORM映射的基类Model：
# Model 可以理解为数据库表中的项映射成对象后该对象最基本的模型, 具有共有的特征和方法, 将被各种类型的项继承
# Model从dict继承，拥有字典的所有功能，同时实现特殊方法__getattr__和__setattr__，能够实现属性操作  
# 还定义各种操作数据库的方法，比如save，delete，find，findAll, update等等。
# 实现数据库操作的所有方法，定义为class方法，所有继承自Model都具有数据库操作方法  
class Model(dict, metaclass=ModelMetaclass): 
    def __init__(self, **kw): # kw是 Object(...)中接受的参数, 是键值对组成的字典
        super(Model, self).__init__(**kw) # super(Model, self) == dict

    def __getattr__(self, key): # obj['id'] 或 obj.id 会被调用
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value): # u['email'] = 'xxx@163.com' 或 u.email =... 会被调用
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None) # getattr是个内置函数, 用来得到对象属性的值

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None: # 若属性没有对应的值
            field = self.__mappings__[key]
            if field.default is not None: # 若项有默认值, 则使用默认值
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

# 数据表中各项的类
class Field(object):

    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self): # 打印时使用的字符串格式   
        return '<%s, %s : %s>' % (self.__class__.__name__, self.column_type, self.name) # 如 <StringField, varchar(100) : username> 分别 项类型名, 字段类型, 字段名

# 定义数据库中五个存储类型:
class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'): # ddl为项的数据类型, 此处初始化为100字节的可变字符
        super().__init__(name, ddl, primary_key, default) #  调用Field类中的__init__    StringField, self将会隐式地传递给super
class IntegerField(Field):
    def __init__(self, name):
        super(IntegerField, self).__init__(name, 'bigint')
# 布尔类型不可以作为主键  
class BooleanField(Field):  
    def __init__(self, name=None, default=False):  
        super().__init__(name,'Boolean',False, default)  
# 不知道这个column type是否可以自己定义 先自己定义看一下  
class IntegerField(Field):  
    def __init__(self, name=None, primary_key=False, default=0):  
        super().__init__(name, 'int', primary_key, default)  
class FloatField(Field):  
    def __init__(self, name=None, primary_key=False,default=0.0):  
        super().__init__(name, 'float', primary_key, default)  
class TextField(Field):  
    def __init__(self, name=None, default=None):  
        super().__init__(name,'text',False, default)


# from orm import Model, StringField, IntegerFieldq
# 定义一个User对象 User对象映射users表中的一行, 表示一个用户
class User(Model):
    # 定义类的属性到列的映射：
    # __table__, id, name为三个类属性, 用来描述User对象和表的映射关系
    __table__ = 'users'  
    id = IntegerField(primary_key=True)
    name = StringField()

# 创建实例:
# user = User(id=123, name='Michael')
# 存入数据库:
# user.insert()
# 查询所有User对象:
# users = User.findAll()




























































# day02
def index(request):
    return web.Response(body=b'<h1>Welcome to my site!</h1>', content_type='text/html')

@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 8000)
    logging.info('server started running at http://127.0.0.1:8000')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()