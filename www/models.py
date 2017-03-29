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
# ����next_id�ṩ����id��Ψһ��ȱʡֵ. ��ȱʡֵ�еĴ���ʱ�䲿��created_at��ȱʡֵ���Ժ���time.time
# time.time() ��ǰʱ��, ���봢�����ʽ, �Ǹ�float
# uuid.uuid4().hex:  uuid4: generate a random Universally Unique Identifier(ͨ��Ψһʶ����) .hex: as a 32-character hexadecimal string
# next_id() 
# => 
# '0014907853922050bc4276fa5274c12ab887dafb4727430000' # bc4 ��ʼ��uuid, ֮ǰ�Ǵ���ʱ��


class User(Model): #��ȻUser��է��û�в������룬��ʵ���ϣ�User��̳�Model�࣬Model���ּ̳�dict�࣬����User���ʵ�����Դ���ؼ��ֲ���  
    # ����������Ե��е�ӳ�䣺
    # __table__, id, name, email, passwordΪ����������, ��������User����ͱ��ӳ���ϵ
    __table__ = 'users'  

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)') #����Ϊid�� tableNameΪUser��������  
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
