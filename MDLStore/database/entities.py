import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, PickleType, Date, DateTime, Float
from sqlalchemy.orm import relationship

from MDLStore.database.config_database_setup import Base
from MDLStore.database.index_database_setup import BaseIndex


class BackupHistory(Base):
    __tablename__ = 'backup_history'

    # 字段定义
    history_id = Column(Integer, primary_key=True, autoincrement=True)  # 历史记录唯一标识符，自增主键
    backup_task_id = Column(Integer, ForeignKey('backup_tasks.task_id'), nullable=False)  # 与之对应的备份任务标识符，外键
    backup_exec_time = Column(DateTime, nullable=False)  # 备份任务开始执行的时间
    exec_result = Column(String, nullable=False)  # 备份任务执行结果，"Success" 或 "Failed"
    backup_file_size = Column(Float)  # 成功备份的数据大小，单位MB
    backup_location = Column(String, nullable=False)  # 备份数据存储位置

    # 关联备份任务对象
    backup_task = relationship("BackupTask", back_populates="backup_histories")

    def __repr__(self):
        return (f"<BackupHistory(history_id={self.history_id}, backup_task_id={self.backup_task_id},"
                f" backup_exec_time='{self.backup_exec_time}', exec_result='{self.exec_result}', "
                f"backup_file_size={self.backup_file_size}, backup_location='{self.backup_location}')>")


class BackupTask(Base):
    __tablename__ = 'backup_tasks'
    # 定义字段
    task_id = Column(Integer, primary_key=True, autoincrement=True)  # 备份任务标识符，自动递增
    email_account_id = Column(Integer, ForeignKey('email_accounts.account_id'), nullable=False)  # 关联的邮箱账户ID
    folder_list = Column(PickleType, nullable=False)  # 要备份的邮箱文件夹列表，使用PickleType来存储Python列表
    start_date = Column(Date)  # 邮件收件日期区间的开始
    end_date = Column(Date)  # 邮件收件日期区间的末尾
    content_type = Column(String, nullable=False)  # 备份内容类型，用逗号隔开：'RFC2822'表示直接复制这封邮件全文，
    # 'Attachments'表示启用了文件名关键字，只备份附件，, 'CloudAttach'表明启用文件名关键字，备份云附件。
    sender = Column(String)  # 发件人过滤条件
    subject_keywords = Column(String)  # 主题关键字过滤条件
    filename_keywords = Column(String)  # 文件名关键字过滤条件
    task_name = Column(String) # 备份任务名称

    backup_histories = relationship("BackupHistory", order_by=BackupHistory.history_id, back_populates="backup_task")
    email_account = relationship("EmailAccount", back_populates="backup_tasks")

    def __repr__(self):
        return (f"<BackupTask(task_id={self.task_id}, email_account_id={self.email_account_id},"
                f" folder_list={self.folder_list}, start_date={self.start_date}, "
                f"end_date={self.end_date}, content_type='{self.content_type}', "
                f"sender='{self.sender}', subject_keywords='{self.subject_keywords}', "
                f"filename_keywords='{self.filename_keywords}',task_name='{self.task_name}')>")

    def __eq__(self, other):
        if isinstance(other, BackupTask):
            return (self.task_id == other.task_id and
                    self.email_account_id == other.email_account_id and
                    self.folder_list == other.folder_list and
                    self.start_date == other.start_date and
                    self.end_date == other.end_date and
                    self.content_type == other.content_type and
                    self.sender == other.sender and
                    self.subject_keywords == other.subject_keywords and
                    self.filename_keywords == other.filename_keywords and
                    self.task_name == other.task_name)
        return False

    def __hash__(self):
        return hash((self.task_id, self.email_account_id, self.folder_list,
                     self.start_date, self.end_date, self.content_type,
                     self.sender, self.subject_keywords, self.filename_keywords, self.task_name))


class EmailAccount(Base):
    __tablename__ = 'email_accounts'
    account_id = Column(Integer, primary_key=True, autoincrement=True)
    server_address = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    ssl_encryption = Column(Boolean, nullable=False)
    remarks = Column(String)

    backup_tasks = relationship("BackupTask", order_by=BackupTask.task_id, back_populates="email_account")

    def __repr__(self):
        return (f"<EmailAccount(account_id={self.account_id}, server_address='{self.server_address}', "
                f"port={self.port}, username='{self.username}', ssl_encryption={self.ssl_encryption}, remarks='{self.remarks}')>")


# class Attachment(BaseIndex):
#     __tablename__ = 'attachments'
#
#     # 字段定义
#     attachment_id = Column(Integer, primary_key=True, autoincrement=True)  # 附件标识符，自增主键
#     email_id = Column(Integer, ForeignKey('email_info.email_id'), nullable=False)  # 所属邮件标识符，外键
#     filename = Column(String, nullable=False)  # 附件文件名（带格式）
#     attachment_type = Column(String, nullable=False)  # 附件类型，区分直接附件和云附件
#     file_path = Column(String, nullable=True)  # 文件存储路径，相对路径
#
#     # 关系定义
#     email = relationship("EmailInfo", back_populates="attachments")
#
#     def __repr__(self):
#         return (f"<Attachment(attachment_id={self.attachment_id}, email_id={self.email_id}, "
#                 f"filename='{self.filename}', attachment_type='{self.attachment_type}', "
#                 f"file_path='{self.file_path}')>")
class Attachment(BaseIndex):
    __tablename__ = 'attachments'

    # 字段定义
    attachment_id = Column(Integer, primary_key=True, autoincrement=True)  # 附件标识符，自增主键
    email_id = Column(Integer, ForeignKey('email_info.email_id'), nullable=False)  # 所属邮件标识符，外键
    filename = Column(String, nullable=False)  # 附件文件名（带格式）
    attachment_type = Column(String, nullable=False)  # 附件类型，区分直接附件和云附件Attach or CloudAttach
    file_path = Column(String, nullable=True)  # 文件存储路径，相对路径
    # file_hash = Column(String, nullable=True)  # 文件哈希值，用于去重

    # 关系定义
    email = relationship("EmailInfo", back_populates="attachments")

    def __repr__(self):
        return (f"<Attachment(attachment_id={self.attachment_id}, email_id={self.email_id}, "
                f"filename='{self.filename}', attachment_type='{self.attachment_type}', "
                f"file_path='{self.file_path}')>")


class EmailInfo(BaseIndex):
    __tablename__ = 'email_info'

    # 字段定义
    email_id = Column(Integer, primary_key=True, autoincrement=True)  # 邮件标识符，自增主键
    email_address = Column(String, nullable=False)  # 用户邮箱地址
    email_uid = Column(Integer, nullable=False)  # 邮件唯一标识符
    subject = Column(String, nullable=True)  # 邮件主题
    from_address = Column(String, nullable=True)  # 发件人邮箱地址
    to_addresses = Column(String, nullable=True)  # 收件人邮箱，以逗号分隔
    cc_addresses = Column(String, nullable=True)  # 抄送人邮箱，以逗号分隔
    bcc_addresses = Column(String, nullable=True)  # 密送人邮箱，以逗号分隔
    received_date = Column(Date, nullable=True)  # 邮件收件日期
    task_name = Column(String, nullable=True)  # 备份任务名
    mailbox = Column(String, nullable=False) # 所属邮箱文件夹
    body_text = Column(String, nullable=True) # 正文文本
    eml_path = Column(String, nullable=True)  # EML文件存储路径

    attachments = relationship("Attachment", order_by=Attachment.attachment_id, back_populates="email")

    def __repr__(self):
        return (f"<EmailInfo(email_id={self.email_id}, email_address='{self.email_address}',"
                f" email_uid={self.email_uid}, subject='{self.subject}', "
                f"from_address='{self.from_address}', to_addresses='{self.to_addresses}', "
                f"cc_addresses='{self.cc_addresses}', bcc_addresses='{self.bcc_addresses}', "
                f"received_date={self.received_date}, task_name={self.task_name}，eml_path='{self.eml_path}')>")




# def test():
#     # 确保配置文件夹存在
#     if not os.path.exists(config_path):
#         os.makedirs(config_path)
#     # 数据库文件完整路径
#     db_path = os.path.join(config_path, 'email_accounts.db')
#
#     # 创建连接字符串，使用绝对路径
#     connection_string = f"sqlite:///{db_path}"
#     print("Connection string:", connection_string)
#
#     # 创建数据库引擎
#     engine = create_engine(connection_string, echo=True)  # echo=True 显示详细日志
#
#
#
#     # 创建 Session 类
#     Session = sessionmaker(bind=engine)
#     session = Session()
#
#     # 示例：添加一个新的邮件账户
#     new_account = EmailAccount(
#         server_address="imap.example.com",
#         port=993,
#         username="user@example.com",
#         password="password",
#         ssl_encryption=True,
#         remarks="Main email account"
#     )
#     session.add(new_account)
#     session.commit()
#
#     # 查询并显示所有账户
#     accounts = session.query(EmailAccount).all()
#     for account in accounts:
#         print(account)
#
#     # 关闭 Session
#     session.close()


# if __name__ == "__main__":
#     test()
