#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

    id = IntegerField(primary_key=True, default=next_id, ddl='varchar(50)') #����Ϊid�� tableNameΪUser��������  
    email = StringField(ddl='varchar(50)')  
    password = StringField(ddl='varchar(50)') 
    admin=BooleanField()
    name = StringField(ddl='varchar(50)')  
    image=  StringField(ddl='varchar(500)')

# day-03:
# from orm import Model, StringField, IntegerField
# if __name__=="__main__": # ����orm
# #һ�����Դ�ǰ����˫�»��ߵķ�����������̳и����ʱ����Щ�������Զ����ã�����__init__  
#     # ����һ��User�� User����ӳ��users���е�һ��, ��ʾһ���û�
#     class User(Model): #��ȻUser��է��û�в������룬��ʵ���ϣ�User��̳�Model�࣬Model���ּ̳�dict�࣬����User���ʵ�����Դ���ؼ��ֲ���  
#         # ����������Ե��е�ӳ�䣺
#         # __table__, id, name, email, passwordΪ����������, ��������User����ͱ��ӳ���ϵ
#         __table__ = 'users'  
#         id = IntegerField('id',primary_key=True) #����Ϊid�� tableNameΪUser��������  
#         name = StringField('name')  
#         email = StringField('email')  
#         password = StringField('password')  
#     # ����ʵ������:
#     # user = User(id=123, name='Michael')
#     # �������ݿ�:
#     # user.insert()
#     # ��ѯ����User����:
#     # users = User.findAll()

#     #�����첽�¼��ľ��  
#     loop = asyncio.get_event_loop()  
   
#     #����ʵ��    
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
#         await destroy_pool()  #�ر�pool  
   
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