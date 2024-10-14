import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 创建declarative base 基类实例
Base = declarative_base()

module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# module_path = os.path.dirname(os.path.abspath(__file__))

# 获取程序当前运行的目录
# if getattr(sys, 'frozen', False):
#     # 如果是打包后的可执行文件，则使用sys._MEIPASS获取真实的目录路径
#     module_path = os.path.dirname(sys.executable)
# else:
#     # 如果是普通的脚本运行，使用__file__获取路径
#     module_path = os.path.dirname(os.path.abspath(__file__))
print(f'config_database:20;module_path={module_path}')

config_path = os.path.join(module_path, 'configs')

if not os.path.exists(config_path):
    os.makedirs(config_path)

db_path = os.path.join(config_path, 'config.db')
connection_string = f"sqlite:///{db_path}"
# print("Connection string:", connection_string)
# 创建数据库引擎
engine = create_engine(connection_string, echo=False)  # echo=True 显示详细日志

# 创建全局 Session 工厂
Session = sessionmaker(bind=engine)


def setupConfigDatabase():
    if not os.path.exists(config_path):
        os.makedirs(config_path)
    print(f'数据库已创建{connection_string}')
    # # 创建所有表
    Base.metadata.create_all(engine)
    # Base.metadata.create_all(engine, tables=[EmailAccount.__table__])


class SessionManager:
    _instance = None
    _session = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            # 仅在第一次创建对象时初始化 Session
            cls._session = Session()
        return cls._instance

    def get_session(self):
        """获取当前的 Session 实例。"""
        return self._session

    def refresh_session(self):
        """刷新现有 Session，创建新的 Session 实例，可用于处理某些特定情况，如 Session 失效等。"""
        self._session = Session()
