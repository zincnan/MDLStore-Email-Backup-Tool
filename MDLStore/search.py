import math
from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy import and_, desc
from sqlalchemy.orm import joinedload

from MDLStore.database.entities import EmailInfo, Attachment
from MDLStore.database.index_database_setup import DatabaseManager
from MDLStore.database.service import EmailInfoManager
from MDLStore.indexes import IndexManager


# def singleton(cls):
#     instances = {}
#
#     def getinstance(*args, **kwargs):
#         if cls not in instances:
#             instances[cls] = cls(*args, **kwargs)
#         return instances[cls]
#
#     return getinstance

@dataclass
class EmailSearchCriteria:
    email_id: Optional[int] = None  # 如果你也需要按email_id搜索，可以添加此字段
    email_address: Optional[str] = None
    email_uid: Optional[int] = None
    subject: Optional[str] = None
    from_address: Optional[str] = None
    to_addresses: Optional[str] = None
    cc_addresses: Optional[str] = None
    bcc_addresses: Optional[str] = None
    received_date_start: Optional[date] = None  # 使用date类型，匹配EmailInfo中的定义
    received_date_end: Optional[date] = None
    task_name: Optional[str] = None
    mailbox: Optional[str] = None
    body_text: Optional[str] = None
    eml_path: Optional[str] = None


@dataclass
class AttachmentSearchCriteria:
    attachment_id: Optional[int] = None  # 可选，如果你需要通过附件ID搜索
    email_id: Optional[int] = None  # 通常用于与特定邮件关联的搜索
    filename: Optional[str] = None  # 附件文件名
    attachment_type: Optional[str] = None  # 附件类型，例如Attach或CloudAttach
    file_path: Optional[str] = None  # 文件存储路径


class MailSearcher:
    def __init__(self, drive):
        self.drive = drive
        self.db_manager = DatabaseManager(self.drive)
        # self.session = self.db_manager.get_session()
        self.fulltext_manager = IndexManager(self.drive)

    def get_drive(self):
        return self.drive

    def search_emails_and_attachments(self, email_criteria=None, attachment_criteria=None):
        """
        根据给定的邮件和附件标准进行搜索。
        :param email_criteria: 包含邮件搜索标准的字典
        :param attachment_criteria: 包含附件搜索标准的字典
        :return: 符合条件的邮件和其附件信息,result是一个email对象，符合entity定义
        """
        session = self.db_manager.get_session()
        query = session.query(EmailInfo).options(joinedload(EmailInfo.attachments))

        if email_criteria:
            query = self.apply_email_criteria(query, email_criteria.__dict__)
            # print(query)

        if attachment_criteria:
            query = self.apply_attachment_criteria(query, attachment_criteria.__dict__)
            # print(query)
        query = query.order_by(desc(EmailInfo.received_date))
        results = query.all()
        session.close()
        # print(f'搜索结果{results}')
        return results

    def search_emails_and_attachments_paged(self, email_criteria=None, attachment_criteria=None, total_count=None,
                                            page=1, page_size=10):
        """
        根据给定的邮件和附件标准进行分页搜索，并返回总记录数和总页数。
        :param email_criteria: 包含邮件搜索标准的字典
        :param attachment_criteria: 包含附件搜索标准的字典
        :param page: 当前页码，默认第1页
        :param page_size: 每页显示的记录数，默认10条
        :return: 一个包含当前页的邮件和其附件信息，总记录数及总页数的字典
        """
        session = self.db_manager.get_session()
        query = session.query(EmailInfo).options(joinedload(EmailInfo.attachments))

        if email_criteria:
            query = self.apply_email_criteria(query, email_criteria.__dict__)

        if attachment_criteria:
            query = self.apply_attachment_criteria(query, attachment_criteria.__dict__)

        if total_count is None:
            # 先计算总记录数
            total_count = query.count()

            # 计算总页数
        total_pages = math.ceil(total_count / page_size) if page_size else 0

        # 添加排序
        query = query.order_by(desc(EmailInfo.received_date))

        # 应用分页
        query = query.limit(page_size).offset((page - 1) * page_size)

        # 执行查询并获取结果
        results = query.all()
        session.close()

        # 返回包含查询结果，总记录数和总页数的字典
        # return {
        #     "results": results,
        #     "total_count": total_count,
        #     "total_pages": total_pages
        # }
        return results, total_count, total_pages

    def search__with_fulltext(self, email_criteria=None, attachment_criteria=None, keyword=None, page=1, page_size=10):
        results = self.search_emails_and_attachments(email_criteria, attachment_criteria)
        file_path_list = []
        email_id_list = []
        for email in results:
            # file_path_list.append(email.eml_path)
            email_id_list.append(email.email_id)
            for attachment in email.attachments:
                file_path_list.append(attachment.file_path)
        # print(file_path_list)
        result_list, total_num, page_num = self.fulltext_manager.search_file_paged(content_keyword=keyword,
                                                                                   file_path_list=file_path_list,
                                                                                   page=page, page_size=page_size)

        session = self.db_manager.get_session()
        eml_info_manager = EmailInfoManager(session)

        email_info_list = []
        for file_info in result_list:
            email_id = file_info['email_id']
            # print(email_id)
            # print(type(email_id))
            email = eml_info_manager.get_email_info_by_id(email_id)
            # print(email)
            if email.email_id in email_id_list:
                info_item = {
                    "email": email,
                    'file': file_info
                }
                email_info_list.append(info_item)
            else:
                total_num = total_num - 1
        session.close()

        return email_info_list, total_num

    def search_all_with_fulltext2(self, email_criteria=None, attachment_criteria=None, keyword=None):
        results = self.search_emails_and_attachments(email_criteria, attachment_criteria)
        file_path_list = []
        email_id_list = []

        for email in results:
            email_id_list.append(email.email_id)
            for attachment in email.attachments:
                file_path_list.append(attachment.file_path)

        # 执行全文搜索，返回所有匹配结果
        result_list = self.fulltext_manager.search_file(query_phrase=keyword, file_path_list=file_path_list)

        session = self.db_manager.get_session()
        eml_info_manager = EmailInfoManager(session)

        # 使用字典来收集邮件和对应的附件信息
        email_info_dict = {}

        for file_info in result_list:
            email_id = file_info['email_id']
            email = eml_info_manager.get_email_info_by_id(email_id)

            if email.email_id in email_id_list:
                if email.email_id not in email_info_dict:
                    # 如果字典中还没有这个邮件的记录，初始化一个新的字典项
                    email_info_dict[email.email_id] = {
                        "email": email,
                        "files": []  # 初始化一个空列表来存放多个 file_info
                    }
                # 将 file_info 添加到文件列表中
                email_info_dict[email.email_id]["files"].append(file_info)

        session.close()

        # 将字典转换为列表返回
        email_info_list = list(email_info_dict.values())

        return email_info_list


    @staticmethod
    def apply_email_criteria(query, criteria):
        conditions = []
        for key, value in criteria.items():
            if value is not None:
                if key in ['subject', 'from_address', 'to_addresses', 'cc_addresses', 'bcc_addresses', 'body_text']:
                    conditions.append(getattr(EmailInfo, key).ilike(f'%{value}%'))  # case-insensitive partial match
                elif key == 'received_date_start':
                    conditions.append(EmailInfo.received_date >= value)
                elif key == 'received_date_end':
                    conditions.append(EmailInfo.received_date <= value)
                else:
                    conditions.append(getattr(EmailInfo, key) == value)
        # print(*conditions)
        if conditions:
            query = query.filter(and_(*conditions))
        return query

    @staticmethod
    def apply_attachment_criteria(query, criteria):
        conditions = []
        for key, value in criteria.items():
            if value is not None and hasattr(Attachment, key):
                if key in ['filename']:
                    conditions.append(getattr(Attachment, key).ilike(f'%{value}%'))  # case-insensitive partial match
                else:
                    conditions.append(getattr(Attachment, key) == value)

        if conditions:
            query = query.join(Attachment, EmailInfo.email_id == Attachment.email_id).filter(and_(*conditions))
        return query
