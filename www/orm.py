#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__authur__ = 'Sytu Lin'

import asyncio, logging, aiomysql, sys

def log(sql, args=()):
    logging.info('SQL: %s' % (sql))
# sql (str) – sql statement
# args (list) – tuple or list of arguments for sql query
# 如: yield from cursor.execute("SELECT * FROM t1 WHERE id=%s", (5,))
# sql: "SELECT * FROM t1 WHERE id=%s"   MySQL的占位符是%s
# args: (5,) 


# @asyncio.coroutine
async def create_pool(loop, **kw): # 连接池里是链接, 需要的时候来直接来拿就可以拿去使用了, 不必每次都mysql.connector.connect()重新连接
    logging.info('start creating database connection pool')
    global __pool
    __pool = await aiomysql.create_pool(
    # 可参考 [aiomysql api reference](http://aiomysql.readthedocs.io/en/latest/connection.html?highlight=autocommit)
        host = kw.get('host', 'localhost'),
        port = kw.get('port', 3306),
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('charset', 'utf8'), 
        autocommit = kw.get('autocommit', True),  # 使得不用每次查询完conn.commit()提交事务
        maxsize = kw.get('maxsize', 10),
        minsize = kw.get('minsize', 1),
        loop = loop
    )


async def destroy_pool():  
    global __pool  
    if __pool is not None :  
        __pool.close()  #关闭进程池,The method is not a coroutine,就是说close()不是一个协程，所有不用yield from  
        await __pool.wait_closed() #但是wait_close()是一个协程，所以要用yield from,到底哪些函数是协程，上面Pool的链接中都有 

# 封装SELECT
async def select(sql, args, size=None):
    log(sql, args)
    global __pool
    # yield from 将会执行一个子协程，并直接返回调用的结果  
    # 下面的yield from从连接池中返回一个连接， 这个地方已经创建了进程池并和进程池连接了，进程池的创建被封装到了create_pool(loop, **kw)
    # with (yield from __pool) as conn: # 从连接池取得一个连接 
    async with __pool.get() as conn:  
        # 创造游标  
        async with conn.cursor(aiomysql.DictCursor) as cur:
        # cur = yield from conn.cursor(aiomysql.DictCursor) 
        # dict cursor会得到一个了列名与字段值映射的字典
        # fetchone()从dict cursor得到下一行协程 会得到类似如下结果
        # {'age': 20, 'DOB': datetime.datetime(1990, 2, 6, 23, 4, 56), 'name': 'bob'}
        # fetchall与fetchman一个dict cursor会得到一个字典组成的列表

        # 普通的cursor则会得到一个字段值组成的元组 
        # fetchone()从普通cursor得到下一行协程 会得到类似如下结果
        # ('1', 'sytu', 12345)
        # fetchall与fetchman一个dict cursor会得到一个元组组成的列表
            await cur.execute(sql.replace('?', '%s'), args or ()) # 将SQL语句参数的占位符?，替换为MySQL的占位符%s
            # 协程cursor.execute的第一个参数接受sql字符串, 第二个参数接受传给sql语句的作为sql参数args元组, 若不存在则传入一个空元组
            if size: # 若有向size传入一个指定返回查询行数的参数size
                rs = await cur.fetchmany(size)
                # fetchmany: Coroutine the next set of rows of a query result
                # The number of rows to fetch per call is specified by the parameter, 这里就是size
            else:
                rs = await cur.fetchall()
                # fetchall: Coroutine returns all rows of a query result set
    # yield from cur.close() 注释掉因为更新了async with ... as cur中的with也会自动关闭cursor
    #关闭游标. 但不用手动关闭conn，因为是在with语句里面，会自动关闭，因为是select，所以不需要提交事务(commit)
    logging.info('rows returned: %s' % len(rs)) # log查询结果的行数
    return rs # 返回一个含有row的字典


# 封装INSERT, UPDATE, DELETE  
async def execute(sql, args, autocommit=True):
    log(sql, args)
    global __pool
    async with  __pool.get() as conn: 
        if not autocommit:
            await conn.begin()
        try:
            cur = await conn.cursor() # 这几个操作只需要普通的cursor
            await cur.execute(sql.replace('?', '%s'), args)  # args 对于这几个sql操作不能少
            affected_num = cur.rowcount # rowcount: 返回被影响的行数
            await cur.close()
            logging.info('executed: %s rows' % affected_num)
            if not autocommit:
                await conn.commit()
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            raise
        return affected_num

# 这个函数主要是把查询字段计数 替换成sql识别的 values的参数 如:
# insert into  `User` (`password`, `email`, `name`, `id`) values (?,?,?,?)
def create_args_string(num):  
    return (','.join(['?' for i in range(num)])) 
    # print(create_args_string(4)) # => '?,?,?,?'


# ORM框架提供: 父类Model 和 属性类型StringField、IntegerField等

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



# 当用户定义一个class User(Model)时，Python解释器首先在当前类User的定义中查找metaclass，
# 如果没有找到，就继续在父类Model中查找metaclass，找到了就使用Model中定义的metaclass的ModelMetaclass来创建User类，
# 也就是说，metaclass可以隐式地继承到子类，但子类自己却感觉不到, 也不需要显式地设置metaclass。
# 子类如User的映射信息通过元类metaclass如ModelMetaClass读取出来

# ModelMetaclass元类定义了所有Model基类(继承ModelMetaclass)的子类实现的操作
# ModelMetaclass的工作主要是为一个数据库表映射成一个封装的类做准备：  
# 1. 读取具体子类(user)的映射信息  
# 2. 创造类的时候，排除对Model类的修改  
# 3. 在当前类中查找所有的类属性(attrs)，如果找到Field属性，就将其保存到__mappings__的dict中，同时从类属性中删除Field(防止实例属性遮住类的同名属性)  
# 4. 将数据库表名保存到__table__中等
# 5. 将数据库操作语句的基本样式保存为类属性

# 基类Model的元类的定义: 
class ModelMetaclass(type):  # 由于metaclass是类的模板，所以必须从 type类 派生
    # __new__控制__init__的执行，所以在其执行之前  
    # cls:代表要__init__的类，此参数在实例化时由Python解释器自动提供(例如下文的User和Model)  
    # bases：代表继承父类的集合  
    # attrs：类的属性集合  
    def __new__(cls, name, bases, attrs):
        if name=='Model':       # 排除掉对Model类的修改
            return type.__new__(cls, name, bases, attrs)

        # 获取table名称 
        tableName=attrs.get('__table__', None) or name   #r如果存在表名，则返回表名，否则返回 name; __table__是User等Model子类的类属性表示 表名
        logging.info('found table: %s (table: %s) ' %(name,tableName ))  

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

        # 从类属性attrs中删除该Field属性:
        for k in mappings.keys():
            attrs.pop(k)
        # 如将User类中的username, email, id, password属性删去. 否则，容易造成运行时错误,实例的属性会遮盖类的同名属性
        # 如果不删除这些同名属性, Model内的args.append(getattr(self, k, None)) 将
        # 得到args.append(IntegerField('id'))
        # args将不会由字段名k对应的字段值value组成列表, 而是由字段类型对象如IntegerField对象, StringField对象等组成列表
        # 原因就是self有两个同名的k

        # 将除主键外的其他属性变成`phone`, `name`这种形式，反引号``: mysql中sql传参数表名，字段名等要用反引号 注意: 字符串用单引号
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        # >>> fields = ['name',` 'phone']
        # >>> list(map(lambda f: '`%s`' % f, fields)) 
        # ['`name`', '`phone`']
        # fields中的元素会被map作为参数传递给lambda的参数f, f再被传递给%s, 生成的字符串作为元素构成一个新的列表

        attrs['__mappings__'] = mappings # 为Model的子类添加一个属性, 保存属性和列的映射关系 
        # mappings是刚才创造的项名与项值映射的字典: __mappings__ = {'username':<__main__.StringField object at 0x10a6884a8>, ....} 
        attrs['__table__'] = tableName  # 保存表名
        attrs['__primary_key__'] = primaryKey # 保存主键属性名
        attrs['__fields__'] = fields # 保存除主键外的属性名
        # 构造默认的SELECT, INSERT, UPDATE和DELETE语句:
        # 注意, `%s` for 表名或字段名, %s也就是不加反引号for字符串, 不加单引号是因为字符串自带了单引号
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName) 
        # 如: select id, name, phone from users  where由调用类对象的方法提供
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        # 如: insert into users (name, phone, id) values (?, ?, ?)
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        # 如: update users set name=?, phone=? where id=?
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        # 如: delete from users where id=?
        return type.__new__(cls, name, bases, attrs)
        # 这样，任何继承自Model的类（比如User），会自动通过ModelMetaclass扫描映射关系，并存储到自身的类属性如__table__、__mappings__中
# 完成metaclass中完成上述的定义就可以在Model中定义各种数据库的操作方法, 也就是说通过对象来操作数据库所需要的基础由metaclass提供


# 定义所有ORM映射的基类Model：
# Model类的任意子类可以映射一个数据库表  
# Model类可以看作是对所有数据库表操作的基本定义的映射  
# Model类可以理解为数据库表中的项映射成对象后该对象最基本的模型, 具有共有的特征和方法, 将被各种类型的项继承
# Model从dict继承，拥有字典的所有功能，同时实现特殊方法__getattr__和__setattr__，能够实现属性操作  
# 还定义各种操作数据库的方法，比如save，delete，find，findAll, update等等。
# 实现数据库操作的所有方法，定义为class方法，所有继承自Model都具有数据库操作方法  
class Model(dict, metaclass=ModelMetaclass): 
    def __init__(self, **kw): # kw是 obj(...)中接受的参数, 是项名和项值作为键值对组成的字典
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

    # 添加类方法，就可以让所有子类调用class类方法 执行查询
    # 类方法有类变量cls传入，从而可以用cls做一些相关的处理。并且有子类继承时，调用该类方法时，传入的类变量cls是子类，而非父类。  
    @classmethod 
    async def find(cls, pk):  
        # 这个类方法使得User类可以通过类方法实现主键查找. 
        # 如: user = yield from User.find('123') '123'会赋给pk
        # 仿佛查询: select id,name,phone from users where id=123

        ' find object by primary key. '
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1) 
        # select 是上面定义的一个协程用来创建游标执行传入的sql语句与其参数
        # '%s where `%s`=?' % (cls.__select__, cls.__primary_key__) 作为sql语句赋给select的参数sql
        # [pk]作为sql语句的参数传递给select的参数args
        # 1 作为select的size参数
        if len(rs) == 0: # 如果什么都没返回, 说明查询失败, find返回None
            return None
        return cls(**rs[0]) # 查询成功则返回一条记录，以dict的形式返回，因为cls的父类继承了dict类    
        # rs = [{'age': 20, 'DOB': datetime.datetime(1990, 2, 6, 23, 4, 56), 'name': 'bob'},]
        # rs[0] 得到dict, **dict 将列dict的键值对依次作为参数传入cls, 最后构造出一个字典然后被返回

    @classmethod  
    async def findAll(cls, where=None, args=None, **kw):  # 根据WHERE条件查找；
        sql = [cls.__select__]  
        if where:  
            sql.append('where')  
            sql.append(where)  
        if args is None:  
            args = []  
   
        orderBy = kw.get('orderBy', None)  
        if orderBy:  
            sql.append('order by')  
            sql.append(orderBy)  

        limit = kw.get('limit', None)  
        if limit is not None:  
            sql.append('limit')  
            if isinstance(limit, int):  
                sql.append('?')  
                args.append(limit)  
            elif isinstance(limit, tuple) and len(limit) ==2:  
                sql.append('?,?')  
                args.extend(limit)  
            else:  
                raise ValueError('Invalid limit value : %s ' % str(limit))  
   
        rs = await select(' '.join(sql),args) #返回的rs是一个元素是tuple的list  
        return [cls(**r) for r in rs]  # **r 是关键字参数，构成了一个cls类的列表，其实就是每一条记录对应的类实例  
     
    @classmethod  
    async def findNumber(cls, selectField, where=None, args=None): # 根据WHERE条件查找，但返回的是整数，适用于像select count(*)这样带有内置函数的SQL
        '''''find number by select and where.'''  
        sql = ['select %s __num__ from `%s`' %(selectField, cls.__table__)]  
        if where:  
            sql.append('where')  
            sql.append(where)  
        rs = await select(' '.join(sql), args, 1)  
        if len(rs) == 0:  
            return None  
        return rs[0]['__num__']  
      

    # 添加实例方法，就可以让所有子类调用实例方法执行相应的数据库修改操作
    async def save(self): # 向表添加一行数据
        # 这个实例方法可以把一个User实例存入数据库
        # 如: user = User(id=123, name='Michael'); yield from user.save()
        # 相当于把一行插入表: insert into users (name, id) values ('Michael', 1)
        args = list(map(self.getValueOrDefault, self.__fields__)) # map会把fields的元素(不为主键的段名)传递给getValueOrDefault
        # args是段值(包括默认值)组成的列表, 这些段值将要作为参数插入表. 将会依次替代VALUES(?,?,?)中的?
        args.append(self.getValueOrDefault(self.__primary_key__)) # 把主键对应的段值也添加进args列表
        rows = await execute(self.__insert__, args)
        if rows != 1: # execute执行正常的话将返回1作为被影响到(插入)的行数, 若不为1则插入失败
            logging.warn('failed to insert record: affected rows: %s' % rows)

    async def update(self): # 修改数据库中已经存入的一行数据  
        args = list(map(self.getValue, self.__fields__))  #获得的value是User实例的属性值(项值), args是其组成的列表 
        args.append(self.getValue(self.__primary_key__))  
        rows = await execute(self.__update__, args)  
        if rows != 1:  
            logging.warning('failed to update record: affected rows: %s'%rows)  
  
    async def remove(self):  # 删表中的一行数据
        args = [self.getValue(self.__primary_key__)]  # 删除一行只需要主键列对应的项值
        rows = await execute(self.__delete__, args)  
        # args会通过execute赋给delete from `%s` where `%s`=?'中的?
        if rows != 1:  
            logging.warning('failed to delete by primary key: affected rows: %s' %rows)  

# from orm import Model, StringField, IntegerField
if __name__=="__main__": # 测试orm
#一个类自带前后都有双下划线的方法，在子类继承该类的时候，这些方法会自动调用，比如__init__  
    # 定义一个User类 User对象映射users表中的一行, 表示一个用户
    class User(Model): #虽然User类乍看没有参数传入，但实际上，User类继承Model类，Model类又继承dict类，所以User类的实例可以传入关键字参数  
        # 定义类的属性到列的映射：
        # __table__, id, name, email, password为三个类属性, 用来描述User对象和表的映射关系
        __table__ = 'users'  
        id = IntegerField('id',primary_key=True) #主键为id， tableName为User，即类名  
        name = StringField('name')  
        email = StringField('email')  
        password = StringField('password')  
    # 创建实例例子:
    # user = User(id=123, name='Michael')
    # 存入数据库:
    # user.insert()
    # 查询所有User对象:
    # users = User.findAll()

    #创建异步事件的句柄  
    loop = asyncio.get_event_loop()  
   
    #创建实例    
    async def test():  
        await create_pool(loop=loop, host='localhost', port=3306, user='root', password='28', db='test')  
        user = User(id=3, name='mary', email='759@gmail.com', password='12345')  
        r = await User.findAll()  
        print(r)  
        await user.save()  
        #ield from user.update()  
        #yield from user.delete()  
        # r = yield from User.find(8)  
        # print(r)  
        # r = yield from User.findAll()  
        # print(1, r)  
        # r = yield from User.findAll(name='sly')  
        # print(2, r)  
        await destroy_pool()  #关闭pool  
   
    loop.run_until_complete(test())  
    loop.close()  
    if loop.is_closed():  
        sys.exit(0) 

# mysql> create database test;
# mysql> use test
# mysql> create table users (
# -> id bigint,
# -> name varchar(100),
# -> email varchar(100),
# -> password varchar(100)
# -> );