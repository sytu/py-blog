import orm
from models import User, Blog, Comment

import asyncio, sys
from aiohttp import web


loop = asyncio.get_event_loop()  


#创建实例    
async def test():
    await orm.create_pool(loop=loop, host='localhost', port=3306, user='pyblog-data', password='28', db='pyblog')  

    # 创建一位用户:
    new_user = User(name='sytu', email='imsytu@163.com', password='123456', image='about:about')
    await new_user.save()  
    r = await User.findAll()  
    print(r)  
    # =>
    # [{'created_at': 1490792489.37803, 'password': '123456', 'id': '001490793039689bb93e162417848c2823adf1909195208000', 'email': 'imsytu@163.com', 'admin': 0, 'image': 'about:about', 'name': 'sytu'}]

    # 修改一位用户:
    update_user = User(name='sytu', email='imsytu@163.com', password='99997', image='about:xxxxxx', id='001490793039689bb93e162417848c2823adf1909195208000', admin='0', created_at='1490792489.37803') # 需要传入用户的id(主键), admin, created_at, 很不方便需要重构
    await update_user.update() 
    r = await User.findAll()  
    print(r) 
    # => 
    # [{'admin': 0, 'password': '99998', 'name': 'sytu', 'created_at': 1490792489.37803, 'id': '001490793039689bb93e162417848c2823adf1909195208000', 'image': 'about:xxxxxx', 'email': 'imsytu@163.com'}]

    # attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)

    # 删除一位用户
    remove_user = User(name='sytu', email='imsytu@163.com', password='9999', image='about:xxxxxx', id='001490793039689bb93e162417848c2823adf1909195208000') # 需要传入用户的id(主键)
    await remove_user.remove() 
    r = await User.findAll()  
    print(r)  
    # =>
    # []
    
    await orm.destroy_pool()  # 关闭pool  


loop.run_until_complete(test())  
loop.close()  
if loop.is_closed():  
    sys.exit(0) 

# users表类似于:
# => 
# mysql> select * from users;
# +----------------------------------------------------+----------------+----------+-------+------+-------------+------------------+
# | id                                                 | email          | password | admin | name | image       | created_at       |
# +----------------------------------------------------+----------------+----------+-------+------+-------------+------------------+
# | 001490793039689bb93e162417848c2823adf1909195208000 | imsytu@163.com | 123456   |     0 | sytu | about:blank | 1490792489.37803 |
# +----------------------------------------------------+----------------+----------+-------+------+-------------+------------------+








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
#         # yield from user.update()  
#         # yield from user.remove()  
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