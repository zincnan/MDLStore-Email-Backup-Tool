from sqlalchemy import and_, func

from MDLStore.database.entities import EmailAccount, BackupTask, BackupHistory, EmailInfo, Attachment


class EmailAccountManager:
    def __init__(self, session):
        self.session = session

    # def add_email_account(self, server_address, port, username, password, ssl_encryption, remarks=None):
    #     """添加一个新的邮件账户"""
    #     new_account = EmailAccount(
    #         server_address=server_address,
    #         port=port,
    #         username=username,
    #         password=password,
    #         ssl_encryption=ssl_encryption,
    #         remarks=remarks
    #     )
    #     self.session.add(new_account)
    #     self.session.commit()
    #     return new_account

    def add_email_account(self, email_account):
        """添加一个新的邮件账户"""
        self.session.add(email_account)
        self.session.commit()
        return email_account

    def get_email_account_by_id(self, account_id):
        """根据ID获取邮件账户"""
        return self.session.query(EmailAccount).filter(EmailAccount.account_id == account_id).one_or_none()

    def update_email_account(self, updated_account):
        """更新邮件账户信息"""
        if updated_account is not None and updated_account.account_id:
            account = self.session.query(EmailAccount).filter(
                EmailAccount.account_id == updated_account.account_id).one_or_none()
            if account:
                # 更新发现的账户与提供的账户的字段匹配
                account.server_address = updated_account.server_address
                account.port = updated_account.port
                account.username = updated_account.username
                account.password = updated_account.password
                account.ssl_encryption = updated_account.ssl_encryption
                account.remarks = updated_account.remarks
                self.session.commit()
                return account
        return None

    def delete_email_account(self, account_id):
        """删除邮件账户"""
        account = self.session.query(EmailAccount).filter(EmailAccount.account_id == account_id).one_or_none()
        if account:
            self.session.delete(account)
            self.session.commit()
            return True
        return False

    def list_email_accounts(self, page_number=1, page_size=10):
        """分页查询邮件账户"""
        query = self.session.query(EmailAccount)
        result = query.offset((page_number - 1) * page_size).limit(page_size).all()
        return result

    def get_email_account_by_mail(self, email):
        """根据邮箱地址获取邮件账户"""
        return self.session.query(EmailAccount).filter(EmailAccount.username == email).one_or_none()

    def delete_email_account_by_mail(self, email):
        """根据邮箱地址删除邮件账户"""
        account = self.session.query(EmailAccount).filter(EmailAccount.username == email.username).one_or_none()
        if account:
            self.session.delete(account)
            self.session.commit()
            return True
        return False

    def get_all_email_account(self):
        """
        获取全部邮箱账户数据
        :return: 返回一个邮箱账户对象列表
        """
        return self.session.query(EmailAccount).all()


class BackupTaskManager:
    def __init__(self, session):
        self.session = session

    # def add_backup_task(self, email_account_id, folder_list, start_date, end_date, content_type, sender=None, subject_keywords=None, filename_keywords=None, task_name=None):
    #     """添加一个新的备份任务"""
    #     new_task = BackupTask(
    #         email_account_id=email_account_id,
    #         folder_list=folder_list,
    #         start_date=start_date,
    #         end_date=end_date,
    #         content_type=content_type,
    #         sender=sender,
    #         subject_keywords=subject_keywords,
    #         filename_keywords=filename_keywords,
    #         task_name=task_name
    #     )
    #     self.session.add(new_task)
    #     self.session.commit()
    #     return new_task

    def add_backup_task(self, backup_task):
        """添加一个新的备份任务，参数是一个BackupTask对象"""
        if backup_task and isinstance(backup_task, BackupTask):
            self.session.add(backup_task)
            self.session.commit()
            return backup_task
        return None  # 添加失败

    def get_backup_task_by_id(self, task_id):
        """根据任务ID获取备份任务"""
        return self.session.query(BackupTask).filter(BackupTask.task_id == task_id).one_or_none()

    # def update_backup_task(self, task_id, **kwargs):
    #     """更新备份任务信息"""
    #     task = self.session.query(BackupTask).filter(BackupTask.task_id == task_id).one_or_none()
    #     if task:
    #         for key, value in kwargs.items():
    #             setattr(task, key, value)
    #         self.session.commit()
    #         return task
    #     return None
    def update_backup_task(self, updated_task):
        """更新备份任务信息"""
        if updated_task is not None and updated_task.task_id:
            task = self.session.query(BackupTask).filter(BackupTask.task_id == updated_task.task_id).one_or_none()
            if task:
                # 更新发现的任务与提供的任务的字段匹配
                task.email_account_id = updated_task.email_account_id
                task.folder_list = updated_task.folder_list
                task.start_date = updated_task.start_date
                task.end_date = updated_task.end_date
                task.content_type = updated_task.content_type
                task.sender = updated_task.sender
                task.subject_keywords = updated_task.subject_keywords
                task.filename_keywords = updated_task.filename_keywords
                task.task_name = updated_task.task_name
                self.session.commit()
                return task
        return None

    def delete_backup_task(self, task_id):
        """删除备份任务"""
        task = self.session.query(BackupTask).filter(BackupTask.task_id == task_id).one_or_none()
        if task:
            self.session.delete(task)
            self.session.commit()
            return True
        return False

    def list_backup_tasks(self, page_number=1, page_size=10):
        """分页查询备份任务"""
        query = self.session.query(BackupTask)
        result = query.offset((page_number - 1) * page_size).limit(page_size).all()
        return result

    def get_all_backup_tasks(self):
        """
        获取全部的备份任务
        :return: 返回备份任务列表
        """
        return self.session.query(BackupTask).all()

    def check_tasks_with_same_name(self, task_name):
        """
        检查是否有同名任务
        :return: 存在同名则返回True，否则返回False
        """
        try:
            # 查询是否存在相同 task_name 的任务
            result = self.session.query(BackupTask).filter(BackupTask.task_name == task_name).first()
            return result is not None
        except Exception as e:
            # 打印错误信息
            import traceback
            print(f"发生错误: {e}")
            traceback.print_exc()
            return False


class BackupHistoryManager:
    def __init__(self, session):
        self.session = session

    # def add_backup_history(self, backup_task_id, backup_exec_time, exec_result, backup_file_size=None, backup_location=""):
    #     """添加一个新的备份历史记录"""
    #     new_history = BackupHistory(
    #         backup_task_id=backup_task_id,
    #         backup_exec_time=backup_exec_time,
    #         exec_result=exec_result,
    #         backup_file_size=backup_file_size,
    #         backup_location=backup_location
    #     )
    #     self.session.add(new_history)
    #     self.session.commit()
    #     return new_history

    def add_backup_history(self, backup_history):
        """添加一个新的备份历史记录，参数是一个BackupHistory对象"""
        if backup_history and isinstance(backup_history, BackupHistory):
            self.session.add(backup_history)
            self.session.commit()
            return backup_history
        return None

    def get_backup_history_by_id(self, history_id):
        """根据历史记录ID获取备份历史"""
        return self.session.query(BackupHistory).filter(BackupHistory.history_id == history_id).one_or_none()

    def update_backup_history(self, updated_history):
        """更新备份历史记录信息"""
        if updated_history is not None and updated_history.history_id:
            history = self.session.query(BackupHistory).filter(
                BackupHistory.history_id == updated_history.history_id).one_or_none()
            if history:
                history.backup_task_id = updated_history.backup_task_id
                history.backup_exec_time = updated_history.backup_exec_time
                history.exec_result = updated_history.exec_result
                history.backup_file_size = updated_history.backup_file_size
                history.backup_location = updated_history.backup_location
                self.session.commit()
                return history
        return None

    def delete_backup_history(self, history_id):
        """删除备份历史记录"""
        history = self.session.query(BackupHistory).filter(BackupHistory.history_id == history_id).one_or_none()
        if history:
            self.session.delete(history)
            self.session.commit()
            return True
        return False

    def list_backup_histories(self, page_number=1, page_size=10):
        """分页查询备份历史记录"""
        query = self.session.query(BackupHistory)
        result = query.offset((page_number - 1) * page_size).limit(page_size).all()
        return result


class EmailInfoManager:
    def __init__(self, session):
        self.session = session

    def add_email_info(self, email_info):
        """添加一个新的邮件信息，参数是一个EmailInfo对象"""
        if email_info and isinstance(email_info, EmailInfo):
            self.session.add(email_info)
            self.session.commit()
            return email_info
        return None  # 可以选择返回错误信息或抛出异常，表明输入参数有误

    # def add_unique_email_info(self, email_info):
    #     """增加去重判断"""
    #     if email_info and isinstance(email_info, EmailInfo):
    #         if self.check_exist(email_info):
    #             return email_info
    #         else:
    #             self.session.add(email_info)
    #             self.session.commit()
    #             return email_info
    #
    #     return None
    def add_unique_email_info(self, email_info):
        """
        增加去重判断，并在特定条件下更新 eml_path。
        """
        if email_info and isinstance(email_info, EmailInfo):
            existing_email_info = self.session.query(EmailInfo) \
                .filter(
                and_(
                    EmailInfo.email_uid == email_info.email_uid,
                    EmailInfo.task_name == email_info.task_name,
                    EmailInfo.mailbox == email_info.mailbox
                )
            ).first()

            # 如果邮件数据已存在
            if existing_email_info:
                # 检查是否需要更新 eml_path
                # if existing_email_info.eml_path == '' and email_info.eml_path:
                if (existing_email_info.eml_path is None or existing_email_info.eml_path == '') and email_info.eml_path:
                    existing_email_info.eml_path = email_info.eml_path
                    self.session.commit()
                return existing_email_info
            else:
                # 如果邮件数据不存在，添加新邮件
                self.session.add(email_info)
                self.session.commit()
                return email_info

        return None

    def get_email_info_by_id(self, email_id):
        """根据邮件ID获取邮件信息"""
        return self.session.query(EmailInfo).filter(EmailInfo.email_id == email_id).one_or_none()

    def update_email_info(self, updated_email_info):
        """更新邮件信息"""
        if updated_email_info and updated_email_info.email_id:
            email_info = self.session.query(EmailInfo).filter(
                EmailInfo.email_id == updated_email_info.email_id).one_or_none()
            if email_info:
                email_info.email_address = updated_email_info.email_address
                email_info.email_uid = updated_email_info.email_uid
                email_info.subject = updated_email_info.subject
                email_info.from_address = updated_email_info.from_address
                email_info.to_addresses = updated_email_info.to_addresses
                email_info.cc_addresses = updated_email_info.cc_addresses
                email_info.bcc_addresses = updated_email_info.bcc_addresses
                email_info.received_date = updated_email_info.received_date
                email_info.task_name = updated_email_info.task_name
                email_info.eml_path = updated_email_info.eml_path
                self.session.commit()
                return email_info
        return None

    def delete_email_info(self, email_id):
        """删除邮件信息"""
        email_info = self.session.query(EmailInfo).filter(EmailInfo.email_id == email_id).one_or_none()
        if email_info:
            self.session.delete(email_info)
            self.session.commit()
            return True
        return False

    def list_email_infos(self, page_number=1, page_size=10):
        """分页查询邮件信息"""
        query = self.session.query(EmailInfo)
        result = query.offset((page_number - 1) * page_size).limit(page_size).all()
        return result

    def check_exist(self, email_info):
        """
        判断当前邮件数据是否已存在(同任务名同ID)
        """
        result = self.session.query(EmailInfo) \
            .filter(and_(EmailInfo.email_uid == email_info.email_uid,
                         EmailInfo.task_name == email_info.task_name,
                         EmailInfo.mailbox == email_info.mailbox)
                    ).first()
        return result is not None


class AttachmentManager:
    def __init__(self, session):
        self.session = session

    def add_attachment(self, attachment):
        """添加一个新的附件信息，参数是一个Attachment对象"""
        if attachment and isinstance(attachment, Attachment):
            self.session.add(attachment)
            self.session.commit()
            return attachment
        return None  # 可以选择返回错误信息或抛出异常，表明输入参数有误

    def add_unique_attachment(self, attachment):
        """添加一个唯一的附件信息，若数据库中已存在完全相同的对象，则返回已存在的对象，若不存在则添加"""
        if attachment and isinstance(attachment, Attachment):
            existing_attachment = self.session.query(Attachment).filter(
                and_(
                    Attachment.email_id == attachment.email_id,
                    Attachment.filename == attachment.filename,
                    Attachment.attachment_type == attachment.attachment_type
                    # Attachment.file_path == attachment.file_path
                )
            ).first()
            if existing_attachment:
                if existing_attachment.file_path == "None" and attachment.file_path:
                    existing_attachment.file_path = attachment.file_path
                    self.session.commit()
                return existing_attachment
            else:
                self.session.add(attachment)
                self.session.commit()
                return attachment

            # if self.check_exist(attachment):
            #     return attachment
            # else:
            #     self.session.add(attachment)
            #     self.session.commit()
            #     return attachment
        else:
            return None

    def get_attachment_by_id(self, attachment_id):
        """根据附件ID获取附件信息"""
        return self.session.query(Attachment).filter(Attachment.attachment_id == attachment_id).one_or_none()

    def update_attachment(self, updated_attachment):
        """更新附件信息"""
        if updated_attachment and updated_attachment.attachment_id:
            attachment = self.session.query(Attachment).filter(
                Attachment.attachment_id == updated_attachment.attachment_id).one_or_none()
            if attachment:
                attachment.email_id = updated_attachment.email_id
                attachment.filename = updated_attachment.filename
                attachment.attachment_type = updated_attachment.attachment_type
                attachment.file_path = updated_attachment.file_path
                attachment.file_hash = updated_attachment.file_hash
                self.session.commit()
                return attachment
        return None

    def delete_attachment(self, attachment_id):
        """删除附件信息"""
        attachment = self.session.query(Attachment).filter(Attachment.attachment_id == attachment_id).one_or_none()
        if attachment:
            self.session.delete(attachment)
            self.session.commit()
            return True
        return False

    def list_attachments(self, page_number=1, page_size=10):
        """分页查询附件信息"""
        query = self.session.query(Attachment)
        result = query.offset((page_number - 1) * page_size).limit(page_size).all()
        return result

    def check_exist(self, attachment):
        existing_attachment = self.session.query(Attachment).filter(
            and_(
                Attachment.email_id == attachment.email_id,
                Attachment.filename == attachment.filename,
                Attachment.attachment_type == attachment.attachment_type,
                Attachment.file_path == attachment.file_path
            )
        ).first()
        return existing_attachment is not None


class StatisticManager:
    def __init__(self, session):
        self.session = session

    def get_statistic_info(self, taskname):
        """
        获取该备份任务的统计信息。对于每个邮箱账户（即 email_address），
        统计该账户下备份的邮件数量、直接附件数量、云附件数量。

        :param taskname: 备份任务名
        :return: 返回每个邮箱账户的统计信息
        """
        # 统计每个邮箱账户的邮件数量
        email_counts = self.session.query(
            EmailInfo.email_address,  # 改为 email_address
            func.count(EmailInfo.email_id).label('email_count')
        ).filter(EmailInfo.task_name == taskname).group_by(EmailInfo.email_address).subquery()

        # 统计每个邮箱账户的直接附件数量 (attachment_type == 'Attach')
        attachment_counts = self.session.query(
            EmailInfo.email_address,  # 改为 email_address
            func.count(Attachment.attachment_id).label('attachment_count')
        ).join(Attachment, Attachment.email_id == EmailInfo.email_id) \
            .filter(EmailInfo.task_name == taskname, Attachment.attachment_type == 'Attach') \
            .group_by(EmailInfo.email_address).subquery()

        # 统计每个邮箱账户的云附件数量 (attachment_type == 'CloudAttach')
        cloud_attachment_counts = self.session.query(
            EmailInfo.email_address,  # 改为 email_address
            func.count(Attachment.attachment_id).label('cloud_attachment_count')
        ).join(Attachment, Attachment.email_id == EmailInfo.email_id) \
            .filter(EmailInfo.task_name == taskname, Attachment.attachment_type == 'CloudAttach') \
            .group_by(EmailInfo.email_address).subquery()

        # 将邮件数、附件数和云附件数组合在一起进行查询
        statistics = self.session.query(
            email_counts.c.email_address,
            email_counts.c.email_count,
            func.coalesce(attachment_counts.c.attachment_count, 0).label('attachment_count'),
            func.coalesce(cloud_attachment_counts.c.cloud_attachment_count, 0).label('cloud_attachment_count')
        ).outerjoin(attachment_counts, email_counts.c.email_address == attachment_counts.c.email_address) \
            .outerjoin(cloud_attachment_counts, email_counts.c.email_address == cloud_attachment_counts.c.email_address) \
            .all()

        # 格式化结果
        result = []
        for stat in statistics:
            result.append({
                "邮箱账户": stat.email_address,
                "邮件数量": stat.email_count,
                "直接附件数量": stat.attachment_count,
                "云附件数量": stat.cloud_attachment_count
            })

        return result

    def get_all_statistic_info(self):
        """
        获取所有备份任务的统计信息。对于每个邮箱账户，统计该账户下备份的邮件数量、直接附件数量、云附件数量。
        :return: 返回每个邮箱账户的统计信息
        """
        # 统计每个邮箱账户的邮件数量
        email_counts = self.session.query(
            EmailInfo.email_address,  # 基于 email_address 统计
            func.count(EmailInfo.email_id).label('email_count')
        ).group_by(EmailInfo.email_address).subquery()

        # 统计每个邮箱账户的直接附件数量 (attachment_type == 'Attach')
        attachment_counts = self.session.query(
            EmailInfo.email_address,
            func.count(Attachment.attachment_id).label('attachment_count')
        ).join(Attachment, Attachment.email_id == EmailInfo.email_id) \
            .filter(Attachment.attachment_type == 'Attach') \
            .group_by(EmailInfo.email_address).subquery()

        # 统计每个邮箱账户的云附件数量 (attachment_type == 'CloudAttach')
        cloud_attachment_counts = self.session.query(
            EmailInfo.email_address,
            func.count(Attachment.attachment_id).label('cloud_attachment_count')
        ).join(Attachment, Attachment.email_id == EmailInfo.email_id) \
            .filter(Attachment.attachment_type == 'CloudAttach') \
            .group_by(EmailInfo.email_address).subquery()

        # 将邮件数、附件数和云附件数组合在一起进行查询
        statistics = self.session.query(
            email_counts.c.email_address,
            email_counts.c.email_count,
            func.coalesce(attachment_counts.c.attachment_count, 0).label('attachment_count'),
            func.coalesce(cloud_attachment_counts.c.cloud_attachment_count, 0).label('cloud_attachment_count')
        ).outerjoin(attachment_counts, email_counts.c.email_address == attachment_counts.c.email_address) \
            .outerjoin(cloud_attachment_counts, email_counts.c.email_address == cloud_attachment_counts.c.email_address) \
            .all()

        # 格式化结果
        result = []
        for stat in statistics:
            result.append({
                "邮箱账户": stat.email_address,
                "邮件数量": stat.email_count,
                "直接附件数量": stat.attachment_count,
                "云附件数量": stat.cloud_attachment_count
            })

        return result

