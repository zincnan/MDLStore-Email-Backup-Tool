# import os
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
#
# # 创建declarative base 基类实例
# BaseIndex = declarative_base()
#
# current_drive = 'E:/'
# MDLStore_Dir = os.path.join(current_drive, 'MDLStore')
# # MDLStore_Dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# # module_path = os.path.dirname(os.path.abspath(__file__))
# index_path = os.path.join(MDLStore_Dir, 'index')
#
# # print(f'路径{index_path}')
#
# if not os.path.exists(index_path):
#     os.makedirs(index_path)
#
# db_path = os.path.join(index_path, 'data.db')
# connection_string = f"sqlite:///{db_path}"
# # print("Connection string:", connection_string)
# # 创建数据库引擎
# engine = create_engine(connection_string, echo=False)  # echo=True 显示详细日志
#
# # 创建全局 Session 工厂
# IndexSession = sessionmaker(bind=engine)
#
#
# def setupIndexDatabase():
#     # # 创建所有表
#     BaseIndex.metadata.create_all(engine)
#     # Base.metadata.create_all(engine, tables=[EmailAccount.__table__])
#
#
# class IndexSessionManager:
#     _instance = None
#     _session = None
#
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(IndexSessionManager, cls).__new__(cls)
#             # 仅在第一次创建对象时初始化 Session
#             cls._session = IndexSession()
#         return cls._instance
#
#     def get_session(self):
#         """获取当前的 Session 实例。"""
#         return self._session
#
#     def refresh_session(self):
#         """刷新现有 Session，创建新的 Session 实例，可用于处理某些特定情况，如 Session 失效等。"""
#         self._session = IndexSession()


import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 创建declarative base 基类实例
BaseIndex = declarative_base()


# class DatabaseManager:
#     def __init__(self, drive):
#         self.drive = drive
#         self.engine = None
#         self.session_factory = None
#         self.initialize_database()
#
#     def initialize_database(self):
#         """初始化数据库，创建文件路径、引擎和Session工厂"""
#         MDLStore_Dir = os.path.join(f"{self.drive}:/", 'MDLStore')
#         index_path = os.path.join(MDLStore_Dir, 'index')
#         if not os.path.exists(index_path):
#             os.makedirs(index_path)
#
#         db_path = os.path.join(index_path, 'data.db')
#         connection_string = f"sqlite:///{db_path}"
#         self.engine = create_engine(connection_string, echo=False)
#         self.session_factory = sessionmaker(bind=self.engine)
#
#         # 初始化数据库表
#         BaseIndex.metadata.create_all(self.engine)
#
#     def get_session(self):
#         """获取新的Session实例"""
#         return self.session_factory()
#
#     def set_drive(self, new_drive):
#         """动态设置新的磁盘驱动器，并重新初始化数据库"""
#         self.drive = new_drive
#         self.initialize_database()


class DatabaseManager:
    def __init__(self, drive):
        self.drive = drive
        self.engine = None
        self.session_factory = None
        self.current_session = None
        self.initialize_database()

    def initialize_database(self):
        """初始化数据库，创建文件路径、引擎和Session工厂"""
        MDLStore_Dir = os.path.join(f"{self.drive}:/", 'MDLStore')
        index_path = os.path.join(MDLStore_Dir, 'index')
        if not os.path.exists(index_path):
            os.makedirs(index_path)

        db_path = os.path.join(index_path, 'data.db')
        connection_string = f"sqlite:///{db_path}"
        self.engine = create_engine(connection_string, echo=False)
        self.session_factory = sessionmaker(bind=self.engine)
        BaseIndex.metadata.create_all(self.engine)

    def get_session(self):
        """获取新的Session实例，并管理其生命周期"""
        if self.current_session:
            self.current_session.close()
        self.current_session = self.session_factory()
        return self.current_session

    def close_session(self):
        """关闭当前session"""
        if self.current_session:
            self.current_session.close()
            self.current_session = None

    def set_drive(self, new_drive):
        """动态设置新的磁盘驱动器，并重新初始化数据库"""
        self.drive = new_drive
        self.close_session()
        self.initialize_database()



