#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Models for user, blog, comment.
'''

__author__ = 'Sytu Lin'

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

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)') #主键为id， tableName为User，即类名  
    email = StringField(ddl='varchar(50)')  
    password = StringField(ddl='varchar(50)') 
    admin=BooleanField()
    name = StringField(ddl='varchar(50)')  
    image=  StringField(ddl='varchar(500)')
    created_at = FloatField(default=time.time)

class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')  
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    created_at = StringField(default=time.time)

class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    blog_id = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = StringField(default=time.time)
