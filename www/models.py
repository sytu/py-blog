#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, uuid

from orm import Model, StringField, IntegerField, FloatField, BooleanField, TextField

def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)
# 函数next_id提供主键id的唯一的缺省值. 该缺省值中的创建时间部分created_at的缺省值来自函数time.time
# time.time() 当前时间, 以秒储存的形式, 是个float
# uuid.uuid4().hex:  uuid4: generate a random Universally Unique Identifier(通用唯一识别码) .hex: as a 32-character hexadecimal string
# next_id() 
# => 
# '0014907853922050bc4276fa5274c12ab887dafb4727430000' # bc4 开始是uuid, 之前是创建时间

class User(Model): #虽然User类乍看没有参数传入，但实际上，User类继承Model类，Model类又继承dict类，所以User类的实例可以传入关键字参数  
    # 定义类的属性到列的映射：
    # __table__, id, name, email, password为三个类属性, 用来描述User对象和表的映射关系
    __table__ = 'users'  

    id = IntegerField(primary_key=True, default=next_id, ddl='varchar(50)') #主键为id， tableName为User，即类名  
    email = StringField(ddl='varchar(50)')  
    password = StringField(ddl='varchar(50)') 
    admin=BooleanField()
    name = StringField(ddl='varchar(50)')  
    image=  StringField(ddl='varchar(500)')

# day-03:
# from orm import Model, StringField, IntegerField
# if __name__=="__main__": # 测试orm
# #一个类自带前后都有双下划线的方法，在子类继承该类的时候，这些方法会自动调用，比如__init__  
#     # 定义一个User类 User对象映射users表中的一行, 表示一个用户
#     class User(Model): #虽然User类乍看没有参数传入，但实际上，User类继承Model类，Model类又继承dict类，所以User类的实例可以传入关键字参数  
#         # 定义类的属性到列的映射：
#         # __table__, id, name, email, password为三个类属性, 用来描述User对象和表的映射关系
#         __table__ = 'users'  
#         id = IntegerField('id',primary_key=True) #主键为id， tableName为User，即类名  
#         name = StringField('name')  
#         email = StringField('email')  
#         password = StringField('password')  
#     # 创建实例例子:
#     # user = User(id=123, name='Michael')
#     # 存入数据库:
#     # user.insert()
#     # 查询所有User对象:
#     # users = User.findAll()

#     #创建异步事件的句柄  
#     loop = asyncio.get_event_loop()  
   
#     #创建实例    
#     async def test():  
#         await create_pool(loop=loop, host='localhost', port=3306, user='root', password='28', db='test')  
#         user = User(id=3, name='mary', email='759@gmail.com', password='12345')  
#         r = await User.findAll()  
#         print(r)  
#         await user.save()  
#         #ield from user.update()  
#         #yield from user.delete()  
#         # r = yield from User.find(8)  
#         # print(r)  
#         # r = yield from User.findAll()  
#         # print(1, r)  
#         # r = yield from User.findAll(name='sly')  
#         # print(2, r)  
#         await destroy_pool()  #关闭pool  
   
#     loop.run_until_complete(test())  
#     loop.close()  
#     if loop.is_closed():  
#         sys.exit(0) 

# mysql> create database test;
# mysql> use test
# mysql> create table users (
# -> id bigint,
# -> name varchar(100),
# -> email varchar(100),
# -> password varchar(100)
# -> );