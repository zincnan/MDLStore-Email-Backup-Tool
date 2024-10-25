import configparser
import email
import json
import os
import pickle
import shutil
import sys
import tempfile
import time
import traceback
import uuid
from typing import List

from MDLStore.cloudfile import CloudAttachmentDownloader
from MDLStore.database.config_database_setup import SessionManager
from MDLStore.database.entities import EmailInfo, Attachment, BackupTask
from MDLStore.database.index_database_setup import DatabaseManager
from MDLStore.database.service import EmailAccountManager, EmailInfoManager, AttachmentManager, BackupTaskManager
from MDLStore.indexes import FileInfo, IndexManager
from MDLStore.mailclients import IMAPClientFactory
from MDLStore.storage import FileWriter, StorageManager, PathDirUtil
from MDLStore.utils import ServerUtils, EmailUtils, EmailParser, CommonUtils

# module_path = os.path.dirname(os.path.abspath(__file__))

# 如果是打包后的exe，获取exe的所在目录
if getattr(sys, 'frozen', False):
    module_path = os.path.dirname(sys.executable)
else:
    # 如果是脚本运行，则获取脚本的所在目录
    module_path = os.path.dirname(os.path.abspath(__file__))


temp_dir = os.path.join(module_path, 'tempdata')

if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

ini_path = os.path.join(module_path, 'configs', 'history.ini')


def backupEmailToTmpArea(backup_task, email_account, progress_callback, info_callback):
    # for i in range(100):
    #     time.sleep(0.1)
    #     progress_callback.emit(i+1)
    #     info_callback.emit(f'已完成{i}个')
    # pass
    print(f'开始备份')
    # 解析备份任务
    folder_list = backup_task.folder_list  # 文件夹列表
    folder_list = pickle.loads(folder_list)
    print(f'文件夹列表{folder_list}')
    start_date = backup_task.start_date  # 邮件收件日期区间的开始
    end_date = backup_task.end_date  # 邮件收件日期区间的末尾
    # task_name = backup_task.task_name  # 备份任务名称
    criteria = EmailUtils.buildCriteria2(start_date, end_date)

    # 连接邮件服务器
    client_type = ServerUtils.get_client_type(email_account.username)
    client = IMAPClientFactory.get_client(client_type, email_account.server_address, email_account.port,
                                          email_account.username, email_account.password, email_account.ssl_encryption)
    connection = client.connect()
    if connection:
        client.login()
        for folder in folder_list:
            folder = folder.replace('"', '')
            client.saveEmails(folder, criteria, progress_callback, info_callback)

    else:
        print(f'任务失败')
        return None
    return True


# def extractEmailData(drive, backup_task, email_account, progress_callback, info_callback, drive_change=False):
#     """
#     解析备份任务，将对应邮件账户所属的邮件，按照备份任务的具体要求，保存在磁盘分区drive下的MDLStore文件夹内。数据源位于temp_dir
#     文件夹内，其中有若干个以邮箱地址为文件名的文件夹，属于email_account账户的邮件，就保存在该文件夹下，该文件夹下又是按照收件箱、已发送
#     等文件夹来保存邮件eml文件。需要按照backup_task的指示，将符合条件的邮件数据保存到目标位置。在目标位置的任务名
#     文件夹内有三个文件夹，分别是RFC2822、Attachment和CloudAttach，分别保存eml邮件文件和附件文件。注意在RFC2822文件夹内部，
#     邮件依然按照跟temp_dir文件夹中各个邮箱相同的文件夹嵌套结构来保存邮件。
#     """
#     # for i in range(100):
#     #     time.sleep(0.1)
#     #     progress_callback.emit(i+1)
#     #     info_callback.emit(f'已完成{i}个')
#     # 构建基本的目录路径
#     base_path = os.path.join(drive, 'MDLStore', backup_task.task_name)
#     os.makedirs(base_path, exist_ok=True)
#     rfc2822_path = os.path.join(base_path, 'RFC2822')
#     attachment_path = os.path.join(base_path, 'Attachment')
#     cloud_attach_path = os.path.join(base_path, 'CloudAttach')
#
#     # 确保目录存在
#     # for path in [rfc2822_path, attachment_path, cloud_attach_path]:
#     #     os.makedirs(path, exist_ok=True)
#
#     # 源数据位置
#     source_dir = os.path.join(temp_dir, email_account.username)  # 这里假设temp_dir中以邮箱用户名命名的文件夹
#
#     # 遍历temp_dir中的所有文件和文件夹
#     # print(f'source_dir=={source_dir}')
#     for root, dirs, files in os.walk(source_dir):
#         # print(f'root={root},dirs={dirs},files={files}')
#         for filename in files:
#             # print(f'filename{filename}')
#             if filename.endswith('.eml'):
#                 file_path = os.path.join(root, filename)
#                 with open(file_path, 'rb') as file:
#                     raw_email = file.read()
#                     # email_parser = EmailParser(file)
#                     # msg = email.message_from_file(file)
#                 # print(filename)
#                 # 使用EmailParser解析邮件
#                 email_parser = EmailParser(raw_email)
#                 # email_parser = EmailParser(msg)
#                 headers = email_parser.get_headers()
#                 email_date = email_parser.getDate(headers)
#                 subject = email_parser.getSubject(headers)
#                 From = email_parser.getFrom(headers)
#                 To = email_parser.getTo(headers)
#                 print(f'{filename}主题{subject},来自{From},给{To},日期{email_date}')
#
#                 # 检查日期范围
#                 if email_date and backup_task.start_date <= email_date <= backup_task.end_date:
#                     # 检查发件人
#                     if backup_task.sender and backup_task.sender not in email_parser.getFrom(headers):
#                         continue
#
#                     # 检查主题关键字
#                     if backup_task.subject_keywords and backup_task.subject_keywords not in email_parser.getSubject(
#                             headers):
#                         continue
#
#                     # 根据备份类型处理邮件
#                     if 'RFC2822' in backup_task.content_type:
#                         # shutil.copy(file_path, os.path.join(rfc2822_path, os.path.basename(root), filename))
#                         write = FileWriter()
#                         sub_folder = os.path.relpath(root, start=temp_dir)  # 获取文件相对于temp_dir的子目录路径
#                         target_folder = os.path.join('MDLStore', backup_task.task_name, 'RFC2822', sub_folder)  # 构建目标文件夹路径
#                         print(target_folder)
#                         print(file_path)
#                         result_path = write.copy_file(file_path, drive, target_folder, drive_change)
#                         print(result_path)
#                     if 'Attachments' in backup_task.content_type:
#                         keyword = backup_task.filename_keywords
#                         attachments = email_parser.get_attachments_by_keyword(keyword,)
#
#                     #
#                     # if 'CloudAttach' in backup_task.content_type:
#                     #     body_parts = email_parser.get_body()
#                     #     for body in body_parts:
#                     #         cloud_attachments = email_parser.get_cloud_attachments(body, backup_task.filename_keywords)
#                     #         if cloud_attachments:
#                     #             for attach in cloud_attachments:
#                     #                 # 保存或处理云附件逻辑
#                     #                 print('保存云附件')
#                     #                 pass


def extractEmailData(drive, backup_task, email_account, drive_change, progress_callback, info_callback):
    """
    解析备份任务，将对应邮件账户所属的邮件，按照备份任务的具体要求，保存在磁盘分区drive下的MDLStore文件夹内。数据源位于temp_dir
    文件夹内，其中有若干个以邮箱地址为文件名的文件夹，属于email_account账户的邮件，就保存在该文件夹下，该文件夹下又是按照收件箱、已发送
    等文件夹来保存邮件eml文件。需要按照backup_task的指示，将符合条件的邮件数据保存到目标位置。在目标位置的任务名
    文件夹内有三个文件夹，分别是RFC2822、Attachment和CloudAttach，分别保存eml邮件文件和附件文件。注意在RFC2822文件夹内部，
    邮件依然按照跟temp_dir文件夹中各个邮箱相同的文件夹嵌套结构来保存邮件。
    """
    print(f'开始提取{backup_task}')
    # 创建临时文件
    global root
    rfc2822_temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w+')
    attachment_temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w+')
    cloud_attach_temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w+')

    # 初始化临时文件中的列表
    rfc2822_list = []
    attachment_list = []
    cloud_attach_list = []

    # 源数据位置
    source_dir = os.path.join(temp_dir, email_account.username)

    # 遍历temp_dir中的所有文件和文件夹
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            if filename.endswith('.eml'):
                file_path = os.path.join(root, filename)
                print(f'解析邮件{filename}:180')
                with open(file_path, 'rb') as file:
                    raw_email = file.read()

                # 使用EmailParser解析邮件
                email_parser = EmailParser(raw_email)
                headers = email_parser.get_headers()
                email_date = email_parser.getDate(headers)
                subject = email_parser.getSubject(headers)
                From = email_parser.getFrom(headers)
                To = email_parser.getTo(headers)
                emlFileName = email_parser.getEmailFileName(headers)
                fileSize = email_parser.getSize()
                message_id = email_parser.getEmailMessageUID(headers)

                # 检查日期范围
                if email_date and backup_task.start_date <= email_date <= backup_task.end_date:
                    # 检查发件人
                    if backup_task.sender and backup_task.sender not in email_parser.getFrom(headers):
                        continue

                    # 检查主题关键字
                    if (backup_task.subject_keywords and backup_task.subject_keywords not in
                            email_parser.getSubject(headers)):
                        continue

                    # 根据备份类型处理邮件
                    if 'RFC2822' in backup_task.content_type:
                        rfc2822_list.append({'file_path': file_path, 'size': fileSize, 'filename': emlFileName})
                    if 'Attachment' in backup_task.content_type:
                        keyword = backup_task.filename_keywords
                        print(f'主题{subject}')
                        attachments = email_parser.get_attachments_by_keyword(keyword)
                        print(f'{filename}的全部附件:{attachments}')
                        for attachment in attachments:
                            attachment_list.append({'file_path': file_path, 'filename': attachment['filename'],
                                                    'size': attachment['file_size']})
                    if 'CloudAttach' in backup_task.content_type:
                        body_parts = email_parser.get_body()
                        len_body = len(body_parts)
                        if len_body >= 3:
                            html_index = int(len_body / 2) - 1
                        else:
                            html_index = len_body - 1
                        # print(f'{body_parts[html_index]}')

                        cloud_attachments = email_parser.get_cloud_attachments(body_parts[html_index],
                                                                               backup_task.filename_keywords)
                        if cloud_attachments:
                            for attach in cloud_attachments:
                                cloud_attach_list.append({'file_path': file_path, 'filename': attach['filename'],
                                                          'file_size': attach['file_size'],
                                                          'expire_time': attach['expire_time'],
                                                          'expired': attach['expired'],
                                                          'outside_link': attach['outside_link']})

    # 写入临时文件
    rfc2822_temp_file.write(json.dumps(rfc2822_list))
    attachment_temp_file.write(json.dumps(attachment_list))
    cloud_attach_temp_file.write(json.dumps(cloud_attach_list))

    # 关闭临时文件
    rfc2822_temp_file.close()
    attachment_temp_file.close()
    cloud_attach_temp_file.close()

    # 记录临时文件路径和数据大小
    # temp_files_info = {
    #     'RFC2822': {'path': rfc2822_temp_file.name, 'size': os.path.getsize(rfc2822_temp_file.name)},
    #     'Attachment': {'path': attachment_temp_file.name, 'size': os.path.getsize(attachment_temp_file.name)},
    #     'CloudAttach': {'path': cloud_attach_temp_file.name, 'size': os.path.getsize(cloud_attach_temp_file.name)}
    # }
    #
    # # 输出临时文件信息
    # print(temp_files_info)
    # return temp_files_info
    # 读取并打印每个临时文件的内容
    rfc2822_list = read_and_print_temp_file(rfc2822_temp_file.name)
    attachment_list = read_and_print_temp_file(attachment_temp_file.name)
    cloud_attach_list = read_and_print_temp_file(cloud_attach_temp_file.name)

    # 估算总附件数目和全文索引容量
    attachments_nums_estimated = len(cloud_attach_list)
    index_capacity = attachments_nums_estimated * 1014

    # 计算总备份数据量大小（单位KB）
    total_size = (sum(item['size'] for item in rfc2822_list) +
                  sum(item['size'] for item in attachment_list) +
                  sum(item['file_size'] for item in cloud_attach_list))
    # 加估算索引数据量的总容量
    total_size = total_size + index_capacity

    # 创建存储管理器
    storage_manager = StorageManager()
    # 寻找可用磁盘单位KB
    available_disk = storage_manager.get_available_disk(drive, total_size, drive_change)
    if available_disk is None:
        print(f'存储总量{total_size}请更换目标磁盘')
        return

    # 创建数据库索引管理器
    db_manager = DatabaseManager(available_disk)
    session = db_manager.get_session()
    email_info_manager = EmailInfoManager(session)
    attach_info_manager = AttachmentManager(session)
    # 创建全文索引管理器
    fulltext_manager = IndexManager(available_disk)

    # 迁移数据到目标位置
    write = FileWriter()
    convert = PathDirUtil()

    total_count_rfc = len(rfc2822_list)
    # 迁移EML文件
    for i, item in enumerate(rfc2822_list):
        if progress_callback and info_callback:
            progress_callback.emit(int(((i + 1) / total_count_rfc) * 100))
            info_callback.emit(f'备份邮件全文：已完成：{i + 1}封/{total_count_rfc}封')

        file_path = item['file_path']
        file_size = item['size']
        filename = item['filename']

        # sub_folder = os.path.relpath(root, start=temp_dir)  # 获取文件相对于temp_dir的子目录路径
        relative_path = os.path.relpath(file_path, start=temp_dir)
        # 提取所需的子目录部分
        sub_folder = os.path.join(os.path.splitdrive(relative_path)[1].split(os.sep)[0],
                                  relative_path.split(os.sep)[1])

        # target_folder = os.path.join('MDLStore', backup_task.task_name, 'RFC2822', sub_folder)  # 构建目标文件夹路径
        target_folder = os.path.join('MDLStore', backup_task.task_name, email_account.username, 'RFC2822', sub_folder)  # 构建目标文件夹路径
        # print(f'{file_path}{sub_folder}')
        result_path = write.copy_file(file_path, filename, available_disk, target_folder, drive_change)

        # 使用缓存为每封邮件添加数据库索引
        with open(file_path, 'rb') as file:
            raw_email = file.read()
        email_parser = EmailParser(raw_email)
        headers = email_parser.get_headers()
        email_uid = email_parser.getEmailMessageUID(headers)
        subject = email_parser.getSubject(headers)
        from_address = email_parser.getFrom(headers)
        to_addresses = email_parser.getTo(headers)
        cc_addresses = email_parser.getCc(headers)
        bcc_addresses = email_parser.getBcc(headers)
        date_time = email_parser.getDate(headers)
        task_name = backup_task.task_name
        mailbox = convert.extract_mailbox(result_path)

        body_text = email_parser.get_body_text()
        index_drive, index_path = convert.absolute_to_relative(result_path)

        # 测试用代码
        # if email_uid is None or email_uid == '':
        #     email_uid = str(uuid.uuid4())

        current_email = EmailInfo(
            email_address=email_account.username,
            email_uid=email_uid,
            subject=subject,
            from_address=from_address,
            to_addresses=to_addresses,
            cc_addresses=cc_addresses,
            bcc_addresses=bcc_addresses,
            received_date=date_time,
            task_name=task_name,
            mailbox=mailbox,
            eml_path=index_path,
            body_text=body_text
        )
        # print(current_email)
        # email_info_manager = EmailInfoManager(session)
        # email_info_manager.add_email_info(current_email)

        added_email_info = email_info_manager.add_unique_email_info(current_email)
        current_email_attachments = email_parser.get_attachments()
        for index_, attach_ in enumerate(current_email_attachments, start=0):
            attach_filename_ = attach_['filename']
            attachment_info = Attachment(
                email_id=added_email_info.email_id,
                filename=attach_filename_,
                attachment_type="Attach",
                file_path="None"
            )
            file_info_ = attach_info_manager.add_unique_attachment(attachment_info)

            file_content_ = email_parser.get_attachment_by_filename(attach_filename_)
            tem_dir_ = temp_dir.replace('\\', '/')
            # print(tem_dir_)
            drive_, target_folder_ = convert.absolute_to_relative(tem_dir_)
            result_path_ = write.write_file(file_content_, attach_filename_, drive_, target_folder_, False)

            current_file_ = FileInfo(
                attachment_id=str(file_info_.attachment_id),
                email_id=str(added_email_info.email_id),
                filename=attach_filename_,
                attachment_type="Attach",
                file_path="None",
                content=None
            )
            fulltext_manager.add_to_index(result_path_, current_file_)
            if os.path.exists(result_path_):
                os.remove(result_path_)

    # 解码并提取附件数据
    total_count_attach = len(attachment_list)
    print(f'共有直接附件{total_count_attach}个:380')
    print(f'附件信息列表{attachment_list}')
    for i, item in enumerate(attachment_list):

        if progress_callback and info_callback:
            if total_count_attach > 0:  # 确保不会除以零
                progress = int(((i + 1) / total_count_attach) * 100)
            else:
                progress = 100  # 如果 total_count_attach 为 0，直接设置进度为 100
            progress_callback.emit(progress)
            info_callback.emit(f'备份邮件附件：已完成{i + 1}个/{total_count_attach}个')

        file_path = item['file_path']
        filename = item['filename']
        file_size = item['size']
        with open(file_path, 'rb') as file:
            raw_email = file.read()
        # 使用EmailParser解析邮件
        email_parser = EmailParser(raw_email)
        file_content = email_parser.get_attachment_by_filename(filename)
        target_folder = os.path.join('MDLStore', backup_task.task_name, email_account.username, 'Attachments')

        result_path = write.write_file(file_content, filename, available_disk, target_folder, drive_change)

        # 为每个文件添加数据库索引和全文索引
        # 添加所属邮件信息
        headers = email_parser.get_headers()
        email_uid = email_parser.getEmailMessageUID(headers)
        subject = email_parser.getSubject(headers)
        from_address = email_parser.getFrom(headers)
        to_addresses = email_parser.getTo(headers)
        cc_addresses = email_parser.getCc(headers)
        bcc_addresses = email_parser.getBcc(headers)
        date_time = email_parser.getDate(headers)
        task_name = backup_task.task_name
        mailbox = convert.extract_mailbox(file_path)
        body_text = email_parser.get_body_text()
        index_drive, index_path = convert.absolute_to_relative(result_path)

        email_info = EmailInfo(
            email_address=email_account.username,
            email_uid=email_uid,
            subject=subject,
            from_address=from_address,
            to_addresses=to_addresses,
            cc_addresses=cc_addresses,
            bcc_addresses=bcc_addresses,
            received_date=date_time,
            task_name=task_name,
            mailbox=mailbox,
            eml_path=None,
            body_text=body_text
        )
        email_info = email_info_manager.add_unique_email_info(email_info)
        # print(email_info.id)
        # 添加附件文件信息
        attachment_info = Attachment(
            email_id=email_info.email_id,
            filename=filename,
            attachment_type="Attach",
            file_path=index_path
            # file_hash="123456789abcdef"  # 哈希值
        )
        file_info = attach_info_manager.add_unique_attachment(attachment_info)
        # 添加附件索引信息
        current_file = FileInfo(
            attachment_id=str(file_info.attachment_id),
            email_id=str(file_info.email_id),
            filename=file_info.filename,
            attachment_type=file_info.attachment_type,
            file_path=file_info.file_path,
            content=None
        )
        # print(result_path)
        fulltext_manager.add_to_index(result_path, current_file)

    # # 解码并下载云附件
    total_count_cloud_attach = len(cloud_attach_list)
    print(f'云附件列表{cloud_attach_list}')
    for i, item in enumerate(cloud_attach_list):

        file_path = item['file_path']
        filename = item['filename']
        file_size = item['file_size']
        expire_time = item['expire_time']
        expired = item['expired']
        outside_link = item['outside_link']
        print(f'获取状态{expired},{type(expired)}')
        # 通过outside_link获取云附件数据
        if expired:
            url = outside_link
            downloader = CloudAttachmentDownloader(url)
            cloud_utils = downloader.create_download_utils()
            url = cloud_utils.get_downloadUrl()
            target_folder = os.path.join('MDLStore', backup_task.task_name, email_account.username, 'CloudAttach')
            download_dir = os.path.join(f'{available_disk}:/', target_folder)
            os.makedirs(download_dir, exist_ok=True)
            download_path = os.path.join(download_dir, filename)
            print(f'直接下载链接{url}')
            status, abstract_path = downloader.download_large_file(url, download_path, cloud_utils.get_headers())
            print(f'下载完成{abstract_path}')
        else:
            abstract_path = None

        # 添加索引数据
        with open(file_path, 'rb') as file:
            raw_email = file.read()
        email_parser = EmailParser(raw_email)
        headers = email_parser.get_headers()
        email_uid = email_parser.getEmailMessageUID(headers)
        subject = email_parser.getSubject(headers)
        from_address = email_parser.getFrom(headers)
        to_addresses = email_parser.getTo(headers)
        cc_addresses = email_parser.getCc(headers)
        bcc_addresses = email_parser.getBcc(headers)
        date_time = email_parser.getDate(headers)
        task_name = backup_task.task_name
        mailbox = convert.extract_mailbox(file_path)
        # print(f"云附件的file_path={file_path}")
        body_text = email_parser.get_body_text()
        if abstract_path:
            index_drive, index_path = convert.absolute_to_relative(abstract_path)
        else:
            index_path = "None"
        email_info = EmailInfo(
            email_address=email_account.username,
            email_uid=email_uid,
            subject=subject,
            from_address=from_address,
            to_addresses=to_addresses,
            cc_addresses=cc_addresses,
            bcc_addresses=bcc_addresses,
            received_date=date_time,
            task_name=task_name,
            mailbox=mailbox,
            body_text=body_text,
            eml_path=None
        )
        email_info = email_info_manager.add_unique_email_info(email_info)

        attachment_info = Attachment(
            email_id=email_info.email_id,
            filename=filename,
            attachment_type="CloudAttach",
            file_path=index_path
            # file_hash="123456789abcdef"  # 哈希值
        )
        file_info = attach_info_manager.add_unique_attachment(attachment_info)
        # 添加全文索引
        current_file = FileInfo(
            attachment_id=str(file_info.attachment_id),
            email_id=str(file_info.email_id),
            filename=file_info.filename,
            attachment_type=file_info.attachment_type,
            file_path=file_info.file_path,
            content=None
        )
        if index_path:
            fulltext_manager.add_to_index(abstract_path, current_file)

        if progress_callback and info_callback:
            if total_count_cloud_attach > 0:  # 确保不会除以零
                progress = int(((i + 1) / total_count_cloud_attach) * 100)
            else:
                progress = 100  # 如果 total_count_attach 为 0，直接设置进度为 100，表示任务已完成

            progress_callback.emit(progress)
            info_callback.emit(f'备份邮件云附件：已完成{i + 1}个/{total_count_cloud_attach}个')

    # 清空临时文件和临时数据区（临时文件读取后已删除）
    delete_directory(source_dir)
    db_manager.close_session()


def read_and_print_temp_file(filename):
    """
    读取临时文件的内容
    :param filename:
    :return:
    """
    with open(filename, 'r') as temp_file:
        data = json.load(temp_file)
        # print(f"内容来自临时文件 {data}{filename}:")
    os.remove(filename)
    return data
    # print(data)


def delete_directory(directory_path):
    """
    删除整个目录及其所有内容
    :param directory_path:
    :return:
    """
    try:
        shutil.rmtree(directory_path)
        print(f"目录 {directory_path} 及其所有内容已被删除")
    except Exception as e:
        print(f"删除目录时出错: {e}")


# 调用函数删除目录


def long_running_task(task_id_lists: List[BackupTask], drive, drive_change, progress_callback,
                      detail_callback, info_callback):
    # 指定 ini 文件的位置
    ini_file = ini_path

    # 创建一个 ConfigParser 对象
    config = configparser.ConfigParser()

    # 如果文件已存在，则读取它
    if os.path.exists(ini_file):
        config.read(ini_file)
    config.clear()

    session = SessionManager().get_session()
    # BackupTaskManager(session)
    account_manager = EmailAccountManager(session)

    task_nums = len(task_id_lists)
    print(f'共有备份任务{task_nums}个')

    for index, task in enumerate(task_id_lists):
        current_task = task
        # print(current_task)
        # email_account_manager = EmailAccountManager(session)
        # email_account = email_account_manager.get_email_account_by_id(current_task.email_account_id)
        #
        # detail_callback.emit(f'当前备份的邮箱是:{email_account.username}')
        # # progress_percentage = int((index + 1) / task_nums * 100)
        # # progress_callback.emit(progress_percentage)
        # # detail_callback.emit(f'获取邮箱:{email_account.username}数据到本地···')
        # backupEmailToTmpArea(current_task, email_account, progress_callback, info_callback)
        # # detail_callback.emit(f'提取邮箱:{email_account.username}数据到目标位置···')
        # extractEmailData(drive, current_task, email_account, progress_callback, info_callback, drive_change)

        try:
            # 获取账户信息
            account = account_manager.get_email_account_by_id(task.email_account_id)
            detail_callback.emit(f'当前备份的邮箱是:{account.username}')
            # 执行备份到临时区域
            # print(f'参数{task, account}')
            backupEmailToTmpArea(task, account, progress_callback, info_callback)
            # 执行数据提取
            drive = drive
            extractEmailData(drive, task, account, drive_change, progress_callback, info_callback)
            # 如果成功，记录在 ini 文件中
            result = "Success"
        except Exception as e:
            # 如果发生错误，记录在 ini 文件中
            result = f"Failed: {str(e)}"
            traceback.print_exc()

        # 在 ini 文件中添加备份任务的结果
        task_section = f"Task_{task.task_id}"
        if not config.has_section(task_section):
            config.add_section(task_section)

        # 序列化 task 对象并存储为字节字符串
        serialized_task = pickle.dumps(task)

        # 将序列化后的 task 对象存储在 ini 文件中
        config.set(task_section, "task_data", serialized_task.hex())  # 将字节流转换为十六进制字符串存储
        config.set(task_section, "result", result)
        config.set(task_section, "drive", drive)

    # 将结果写入 ini 文件
    with open(ini_file, "w") as configfile:
        config.write(configfile)
    # print(f"备份任务结果记录在 {ini_file} 中")

    return "Task completed"
