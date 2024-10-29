import codecs
import hashlib
import os
import re
import uuid
from datetime import date, timedelta
import email
from email import policy
from email.message import Message
from email.policy import default, strict
from email.utils import parsedate_to_datetime
from email.header import decode_header

from bs4 import BeautifulSoup

from MDLStore.cloudfile import CloudFileParser



class ServerUtils:
    # 一个字典，用来存储邮箱域和对应的IMAP服务器地址
    imap_servers = {
        'gmail.com': 'imap.gmail.com',
        'qq.com': 'imap.qq.com',
        '163.com': 'imap.163.com',
        '126.com': 'imap.126.com',
        'ruc.edu.cn': 'imap.ruc.edu.cn',
        'outlook.com': 'outlook.office365.com',
        'sina.com': 'imap.sina.com',
        '139.com': 'imap.139.com',
        '189.com': 'imap.189.com',
        'sohu.com': 'imap.sohu.com',
    }

    @classmethod
    def get_imap_server(cls, email):
        """
        根据提供的邮箱地址返回对应的IMAP服务器地址。
        :param email: 完整的邮箱地址，如 'zinc_s@139.com'
        :return: 对应的IMAP服务器地址，如果不支持则返回 None
        """
        domain = email.split('@')[-1] if '@' in email else None
        # 返回对应的IMAP服务器地址，如果字典中没有则返回 None
        return cls.imap_servers.get(domain, None)

    @classmethod
    def get_client_type(cls, mail_address):
        if not isinstance(mail_address, str) or '@' not in mail_address:
            raise ValueError("Invalid email address")

        domain = mail_address.split('@')[-1].lower()

        if domain == 'gmail.com':
            return 'gmail'
        elif domain in ['163.com']:
            return 'netease'
        elif domain == '126.com':
            return 'nete126'
        elif domain == 'ruc.edu.cn':
            return 'rucmail'
        elif domain in ['qq.com']:
            return 'qmail'
        elif domain in ['outlook.com']:
            return 'outlook'
        elif domain == 'sina.com':
            return 'sina'
        elif domain == '139.com':
            return 'mail139'
        elif domain == '189.cn':
            return 'mail189'
        elif domain == 'sohu.com':
            return 'sohu'
        else:
            # raise ValueError("Unknown client type")
            return 'None'

    @classmethod
    def get_imap_port(cls, ssl=True):
        if ssl:
            return 993
        else:
            return 143

    @classmethod
    def get_cloud_file_provider(cls, outside_link):
        """
        根据外部链接返回云附件服务提供商的名称
        :param outside_link:
        :return: 返回名称
        """
        pass


class EmailUtils:

    @classmethod
    def buildCriteria(cls, date_start, date_end):
        """
        根据日期范围构建IMAP搜索条件字符串
        :param date_start: 例如 start_date = date(2023, 1, 1)
        :param date_end: 例如 end_date = date(2023, 12, 31)
        :return: IMAP搜索条件字符串
        """
        # 检查输入参数是否为 date 类型
        if not isinstance(date_start, date) or not isinstance(date_end, date):
            raise ValueError("date_start 和 date_end 必须是 datetime.date 类型")

        # 将日期转换为 IMAP 所需的 DD-MMM-YYYY 格式
        start_date_imap = date_start.strftime('%d-%b-%Y')
        end_date_imap = date_end.strftime('%d-%b-%Y')

        # 构建搜索条件字符串
        criteria = f'SINCE {start_date_imap} BEFORE {end_date_imap}'
        return criteria

    @classmethod
    def buildCriteria2(cls, date_start=None, date_end=None):
        """
        根据日期范围构建IMAP搜索条件字符串
        :param date_start: 例如 start_date = date(2023, 1, 1)
        :param date_end: 例如 end_date = date(2023, 12, 31)
        :return: IMAP搜索条件字符串
        """
        # 检查输入参数是否为 date 类型或 None
        if date_start and not isinstance(date_start, date):
            raise ValueError("date_start 必须是 datetime.date 类型或 None")
        if date_end and not isinstance(date_end, date):
            raise ValueError("date_end 必须是 datetime.date 类型或 None")

        # 构建搜索条件字符串
        criteria = []
        date_end = date_end + timedelta(days=1)

        # 如果提供了 start_date，添加 SINCE 条件
        if date_start:
            start_date_imap = date_start.strftime('%d-%b-%Y')
            criteria.append(f'SINCE {start_date_imap}')

        # 如果提供了 end_date，添加 BEFORE 条件
        if date_end:
            end_date_imap = date_end.strftime('%d-%b-%Y')
            criteria.append(f'BEFORE {end_date_imap}')

        # 如果都没有提供，则返回 'ALL' 以搜索全部邮件
        if not criteria:
            return 'ALL'

        # 使用空格连接条件，返回搜索条件字符串
        return ' '.join(criteria)

    @classmethod
    def encode_modified_utf7(cls, s):
        """将unicode字符串编码为Modified UTF-7编码的字符串。"""
        # 首先使用utf-7编码，然后进行必要的替换
        utf7_encoded = codecs.encode(s, 'utf-7')

        # 替换'+', '/' 为'&', ','
        # 注意：标准UTF-7中的'+'在Modified UTF-7中用'&'表示
        modified_utf7 = utf7_encoded.replace(b'+', b'&').replace(b'/', b',')

        # 对于直接ASCII表示的部分，不需要额外的编码
        # 但在实际的Modified UTF-7编码过程中，可能需要处理特定字符的替换
        # 以下转换是为了确保兼容性和遵循IMAP的Modified UTF-7编码规范
        # ASCII部分不需要进行Base64编码，因此可能需要对结果进行调整，以确保它符合实际使用的Modified UTF-7规则

        # 解码为ASCII以进行输出
        try:
            # 尝试将bytes对象解码回ASCII字符串，因为Modified UTF-7的主要目的是ASCII兼容
            modified_utf7 = modified_utf7.decode('ascii')
        except UnicodeDecodeError as e:
            print(f"编码失败: {e}")
            modified_utf7 = s  # 编码失败，返回原字符串

        return modified_utf7

    @classmethod
    def decode_modified_utf7(cls, s):
        """将Modified UTF-7编码的字符串解码为unicode字符串。"""
        utf7_encoded = s.encode('ascii').replace(b'&', b'+').replace(b',', b'/')
        try:
            decoded_string = codecs.decode(utf7_encoded, 'utf-7')
        except Exception as e:
            print(f"解码失败: {e}")
            decoded_string = s  # 解码失败，返回原字符串
        return decoded_string

    @classmethod
    def generate_unique_filename(cls, directory, receive_date, subject, extension):
        """
        生成唯一的文件名。如果文件名冲突，则在名称后面添加数字编号（两位）。
        :param directory: 文件保存的目标目录
        :param receive_date: 邮件日期
        :param subject: 邮件主题
        :param extension: 文件扩展名
        :return: 唯一的文件名
        """
        # 创建初始文件名
        base_filename = f"{receive_date} - {subject}".replace('/', '_').replace('\\', '_').replace(':', '-')
        unique_filename = f"{base_filename}.{extension}"
        counter = 1

        # 检查文件是否存在，如果存在则生成新的文件名
        while os.path.exists(os.path.join(directory, unique_filename)):
            unique_filename = f"{base_filename}_{counter:02d}.{extension}"
            counter += 1

        return unique_filename

def decode_filename(filename):
    """
    解码附件的文件名
    :param filename: 编码后的文件名
    :return: 解码后的文件名
    """
    decoded_header = decode_header(filename)
    decoded_str = ''
    for text, charset in decoded_header:
        if charset:  # 如果存在编码，则使用相应的编码解码
            try:
                decoded_str += text.decode(charset)
            except (UnicodeDecodeError, AttributeError):
                decoded_str += text.decode('utf-8', errors='ignore')  # 如果解码失败，尝试使用UTF-8解码
        else:
            decoded_str += text if isinstance(text, str) else text.decode('utf-8', errors='ignore')
    return decoded_str
class EmailParser:
    """已被注释
    一个用来解码邮件内容的解析器，用来解析邮件头、邮件体、附件内容
    """

    def __init__(self, raw_email_data):
        self.raw_email = raw_email_data
        self.msg = email.message_from_bytes(raw_email_data, policy=policy.default)
        # self.msg = email.message_from_bytes(raw_email_data, policy=strict)

    def get_headers(self):
        """
        获取邮件头信息
        :return: 字典，包含邮件头的键值对
        """
        headers_ = {}
        # print(self.msg.items())
        try:
            for header, value in self.msg.items():
                headers_[header] = value
        except IndexError as e:
            # print(f"Error processing headers: {e}")
            headers_ = self.get_headers_for_except()
            # 可以选择记录有问题的header或者做其他的错误处理
        except Exception as e:
            print(f"Unexpected error when fetching headers: {e}")
        return headers_

    def get_headers_for_except(self):
        """
        获取邮件头信息
        :return: 字典，包含邮件头的键值对
        """
        headers_ = {}
        try:
            for header, value in self.msg.raw_items():
                try:
                    headers_[header] = str(value)
                except Exception as e:
                    print(f"Error parsing header {header}: {e}")
                    headers_[header] = value
        except IndexError as e:
            print(f"Index error when fetching headers: {e}")
        except Exception as e:
            print(f"Unexpected error when fetching headers: {e}")
        return headers_

    # def get_body(self):
    #     """
    #     获取邮件正文内容
    #     :return: 邮件正文字符串
    #     """
    #     if self.msg.is_multipart():
    #         parts = []
    #         for part in self.msg.walk():
    #             content_type = part.get_content_type()
    #             disposition = part.get('Content-Disposition')
    #
    #             if content_type == 'text/plain' and disposition is None:
    #                 parts.append(part.get_payload(decode=True).decode(part.get_content_charset()))
    #             elif content_type == 'text/html' and disposition is None:
    #                 parts.append(part.get_payload(decode=True).decode(part.get_content_charset()))
    #
    #         return '\n'.join(parts)
    #     else:
    #         return self.msg.get_payload(decode=True).decode(self.msg.get_content_charset())

    # def get_body(self):
    #     """
    #     获取邮件正文内容,(正确版本)
    #     :return: 包含邮件正文内容的列表
    #     """
    #     parts = []
    #     if self.msg.is_multipart():
    #         for part in self.msg.walk():
    #             content_type = part.get_content_type()
    #             disposition = part.get('Content-Disposition')
    #
    #             if content_type == 'text/plain' and disposition is None:
    #                 parts.append(part.get_payload(decode=True).decode(part.get_content_charset()))
    #             elif content_type == 'text/html' and disposition is None:
    #                 parts.append(part.get_payload(decode=True).decode(part.get_content_charset()))
    #     else:
    #         parts.append(self.msg.get_payload(decode=True).decode(self.msg.get_content_charset()))
    #
    #     return parts

    def get_body(self):
        """
        获取邮件正文内容
        :return: 包含邮件正文内容的列表
        """
        parts = []
        if self.msg.is_multipart():
            for part in self.msg.walk():
                content_type = part.get_content_type()
                disposition = part.get('Content-Disposition')

                # 检查是否为嵌套邮件或明确标记为附件的部分
                if content_type == 'message/rfc822' or (
                        disposition is not None and 'attachment' in disposition.lower()):
                    continue  # 跳过这些部分

                # 处理纯文本和HTML内容，确保它们不是附件
                if (content_type == 'text/plain' or content_type == 'text/html') and (
                        disposition is None or 'attachment' not in disposition.lower()):
                    parts.append(part.get_payload(decode=True).decode(part.get_content_charset()))
        else:
            # 非多部分邮件，直接获取有效载荷
            parts.append(self.msg.get_payload(decode=True).decode(self.msg.get_content_charset()))

        return parts

    def get_body_text(self):
        body_parts = self.get_body()
        len_body = len(body_parts)
        if len_body == 0:
            return ""
        if len_body >= 3:
            html_index = int(len_body / 2) - 1
        else:
            html_index = len_body - 1
        combined_str = ''.join(body_parts[:html_index + 1])
        soup = BeautifulSoup(combined_str, 'html.parser')  # 使用内建的 html.parser
        clean_text = soup.get_text(separator=' ', strip=True)  # 获取所有标签去除后的纯文本内容
        return clean_text

    # def get_attachments(self, download_folder=None):
    #     """
    #     获取邮件附件内容
    #     :param download_folder: 保存附件的文件夹，如果为 None，则不保存文件，只返回文件内容
    #     :return: 附件信息列表，每个元素为包含文件名和文件内容的字典
    #     """
    #     attachments_ = []
    #     for part in self.msg.walk():
    #         content_disposition = part.get("Content-Disposition")
    #         if content_disposition and "attachment" in content_disposition:
    #             filename = part.get_filename()
    #             if filename:
    #                 print(filename)
    #                 file_content = part.get_payload(decode=True)
    #                 file_size = len(file_content)  # 计算文件大小
    #                 attachments_.append({'filename': filename, 'file_size': file_size})
    #                 if download_folder:
    #                     with open(os.path.join(download_folder, filename), 'wb') as f:
    #                         f.write(file_content)
    #     return attachments_

    def get_attachments(self, download_folder=None):
        """
        获取邮件附件内容
        :param download_folder: 保存附件的文件夹，如果为 None，则不保存文件，只返回文件内容
        :return: 附件信息列表，每个元素为包含文件名和文件内容的字典
        """
        attachments_ = []
        for part in self.msg.walk():
            content_disposition = part.get("Content-Disposition")
            if content_disposition and "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    decoded_filename = decode_filename(filename)
                    print(f"Decoded filename: {decoded_filename}")
                    if filename.endswith('.eml'):
                        eml_content = part.get_payload()
                        if isinstance(eml_content, list):
                            eml_content = ''.join([str(item) for item in eml_content])
                        file_size = len(eml_content.encode('utf-8')) / 1024  # 计算文件大小
                        attachments_.append({'filename': filename, 'file_size': file_size})
                        if download_folder:
                            with open(os.path.join(download_folder, filename), 'wb') as f:
                                f.write(eml_content.encode('utf-8'))
                    else:
                        # 处理普通附件
                        file_content = part.get_payload(decode=True)
                        file_size = len(file_content) / 1024 # 计算文件大小
                        attachments_.append({'filename': filename, 'file_size': file_size})
                        if download_folder:
                            with open(os.path.join(download_folder, filename), 'wb') as f:
                                f.write(file_content)
        return attachments_

    def get_attachments_by_keyword(self, keyword, download_folder=None):
        """
        获取文件名中包含指定关键字的附件
        :param keyword: 关键字
        :param download_folder: 保存附件的文件夹，如果为 None，则不保存文件，只返回文件内容
        :return: 附件信息列表，每个元素为包含文件名和文件大小的字典
        """
        attachments_ = []
        for part in self.msg.walk():
            content_disposition = part.get("Content-Disposition")
            if content_disposition and "attachment" in content_disposition:
                filename = part.get_filename()
                if filename and keyword in filename:
                    if filename.endswith('.eml'):
                        eml_content = part.get_payload()
                        # if isinstance(eml_content, list):
                        #     # eml_content = ''.join([str(item) for item in eml_content])
                        #     # 如果是列表，那么创建一个空字符串来存储转换后的内容
                        #     result = ''
                        #     # 遍历列表中的每个元素
                        #     for item in eml_content:
                        #         # 将每个元素转换为字符串，并添加到 result 字符串中
                        #         print(item.get('Message-ID'))
                        #         result += str(item)
                        #     # 最后，将拼接好的字符串赋值回 eml_content
                        #     eml_content = result
                        eml_content = self.process_eml_content(eml_content)
                        file_size = len(eml_content.encode('utf-8')) / 1024  # 计算文件大小
                        attachments_.append({'filename': filename, 'file_size': file_size})
                        if download_folder:
                            with open(os.path.join(download_folder, filename), 'wb') as f:
                                f.write(eml_content.encode('utf-8'))
                    else:
                        # if filename and (keyword is None or keyword in filename):
                        file_content = part.get_payload(decode=True)
                        file_size = len(file_content) / 1024  # 计算文件大小
                        attachments_.append({'filename': filename, 'file_size': file_size})
                        if download_folder:
                            filepath = os.path.join(download_folder, filename)
                            with open(filepath, 'wb') as f:
                                f.write(file_content)
        return attachments_

    def getFrom(self, headers_):
        """
        获取发件人
        :param headers_: 邮件头部字典
        :return: 无则返回NONE
        """
        return headers_.get("From", None)

    def getTo(self, headers_):
        """
        :param headers_:
        :return:
        """
        return headers_.get("To", None)

    def getEmailMessageUID(self, headers_):
        """
        获取邮件的唯一标识message-ID
        :param headers_:
        :return: 无则返回NONE
        """
        message_ID = headers_.get("Message-ID", None)
        if message_ID:
            return message_ID
        else:
            return headers_.get("Message-Id", None)


    def getSubject(self, headers_):
        """
        获取邮件主题
        :param headers_:
        :return:
        """
        # return headers_.get("Subject", None)
        subject = headers_.get("Subject", None)
        return self.decode_mime_words(subject)

    def getCc(self, headers_):
        """
        获取抄送人
        :param headers_: 邮件头字典
        :return: 抄送人，如果不存在则返回None
        """
        return headers_.get("Cc", None)

    def getBcc(self, headers_):
        """
        获取密送人
        :param headers_: 邮件头字典
        :return: 密送人，如果不存在则返回None
        """
        return headers_.get("Bcc", None)

    def getDateTime(self, headers_):
        """
        获取日期和时间
        :param headers_: 邮件头字典
        :return: 日期和时间的datetime对象，如果不存在则返回None
        """
        date_str = headers_.get("Date", None)
        if date_str:
            return parsedate_to_datetime(date_str)
        return None

    def getDate(self, headers_):
        """
        只获取日期
        :param headers_:
        :return:
        """
        datetime_obj = self.getDateTime(headers_)
        if datetime_obj:
            return datetime_obj.date()
        return None

    def getSize(self):
        """
        获取当前邮件的大小KB
        :return:
        """
        return len(self.raw_email) / 1024

    def getAttachmentSize(self):
        pass

    def get_attachment_by_filename(self, filename):
        """
        获取当前邮件中附件文件名为filename的附件文件数据。
        :param filename:
        :return: 文件数据，是经过base64或者其他编码从MIME中解析出来的文件数据。没有filename文件则返回None
        """
        for part in self.msg.walk():
            content_disposition = part.get("Content-Disposition")
            if content_disposition and "attachment" in content_disposition:
                part_filename = part.get_filename()
                if part_filename == filename:
                    if filename.endswith(".eml"):
                        eml_content = part.get_payload()
                        if isinstance(eml_content, list):
                            # eml_content = ''.join([str(item) for item in eml_content])
                            eml_content = self.process_eml_content(eml_content)
                        return eml_content.encode('utf-8')
                    else:
                        file_content = part.get_payload(decode=True)
                        return file_content
        return None

    # def get_cloud_attachments(self, body_, keyword=None):
    #     """
    #     获取邮件正文HTML中嵌入的云附件的外部链接
    #     :param body_: 解码后的邮件正文
    #     :param keyword: 文件名关键字
    #     :return: 一个字典列表。每一项表示一个符合条件的云附件，没有则返回None
    #     """
    #     if body_ is None:
    #         return None
    #
    #     patterns = {
    #         "163": r'https://mail\.163\.com/large-attachment-download/index\.html\?p=.*',
    #         "126": r'https://mail\.163\.com/large-attachment-download/index\.html\?p=.*',
    #         "QQ": r'https://mail\.qq\.com/cgi-bin/ftnExs_download\?k=.*',
    #         "Gmail": r'https://drive\.google\.com/file/d/.*',
    #         "Outlook": r'https://1drv\.ms/.*',
    #         "189": r'https://download\.cloud\.189\.cn/file/downloadFile\.action\?dt=.*',
    #         "RUC": r'https://edisk\.qiye\.163\.com/api/biz/attachment/download\?identity=.*',
    #         "Sina": r'https://mail\.sina\.com\.cn/filecenter/download\.php\?id=.*'
    #     }
    #
    #     # 搜索并提取链接
    #     # for provider, pattern in patterns.items():
    #     #     matches = re.findall(pattern, body_)
    #     #     if matches:
    #     #         cloud_attachments = [{"provider": provider, "url": match} for match in matches]
    #     #
    #     #         return cloud_attachments
    #     #
    #     # return None
    #
    #     cloud_attachments = []
    #     for provider, pattern in patterns.items():
    #         matches = re.findall(pattern, body_)
    #         for match in matches:
    #             cloud_attachments.append({"provider": provider, "url": match})
    #
    #     # return cloud_attachments if cloud_attachments else None
    #     if cloud_attachments:
    #
    #         return cloud_attachments
    #     else:
    #         return None

    def get_cloud_attachments(self, body_, keyword=None):
        """
        获取邮件正文HTML中嵌入的云附件的外部链接
        :param body_: 解码后的邮件正文
        :param keyword: 文件名关键字
        :return: 一个字典列表。每一项表示一个符合条件的云附件，没有则返回None
        """
        if body_ is None:
            return None

        patterns = {
            "163": r'https://mail\.163\.com/large-attachment-download/index\.html\?p=.*',
            "126": r'https://mail\.163\.com/large-attachment-download/index\.html\?p=.*',
            "QQ": r'https://mail\.qq\.com/cgi-bin/ftnExs_download\?k=.*',
            "Gmail": r'https://drive\.google\.com/(file/d/|open\?id=).*',
            "Outlook": r'https://1drv\.ms/.*',
            "189": r'https://download\.cloud\.189\.cn/file/downloadFile\.action\?dt=.*',
            "RUC": r'https://edisk\.qiye\.163\.com/api/biz/attachment/download\?identity=.*',
            "Sina": r'https://mail\.sina\.com\.cn/filecenter/download\.php\?id=.*'
        }

        cloud_attachments = []
        print(f'匹配云附件类型')
        for provider, pattern in patterns.items():
            if re.search(pattern, body_):
                print(f'当前匹配的provider是{provider}')
                parser_ = CloudFileParser.create_parser(provider)
                file_infos = parser_.get_cloud_file_info(body_)
                for file_info in file_infos:
                    if keyword is None or keyword.lower() in file_info.get('filename', '').lower():
                        cloud_attachments.append(file_info)
                break

        return cloud_attachments if cloud_attachments else None

    def getEmailFileName(self, headers_):
        # 获取主题
        subject = self.getSubject(headers_)
        if subject is None:
            subject = "NoSubject"

        # 获取日期和时间，假设返回的是 datetime 对象
        date_time = self.getDateTime(headers_)
        if date_time is None:
            date_time_str = "NoDate"
        else:
            # 格式化日期和时间为字符串，例如 '20210730_123501'
            date_time_str = date_time.strftime("%Y%m%d_%H%M%S")

        # 生成一个随机UUID
        # random_uuid = uuid.uuid4()
        from_ = self.getFrom(headers_)
        if from_ is None:
            from_ = "NoFrom"

        # 组合文件名并清理特殊字符
        file_name = f"{subject}_{date_time_str}_{from_}"
        # 移除或替换文件名中的特殊字符
        file_name = re.sub(r'[^\w\-_\.]', '_', file_name)  # 保留字母、数字、下划线、破折号和点，其他字符替换为下划线
        file_name = f'{file_name}.eml'

        return file_name

    def save_email(self, save_path):
        """
        保存当前邮件到指定的文件路径。
        :param save_path: 要保存邮件的完整文件路径。
        """
        try:
            # 确保目标文件夹存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 打开文件并写入邮件内容
            with open(save_path, 'wb') as file:
                file.write(self.raw_email)
            print("邮件已成功保存到：", save_path)
        except Exception as e:
            print(f"保存邮件时出错：{e}")

    def decode_mime_words(self, s):
        """ 解码 MIME 字符串，正确处理各种编码 """
        if s is None:
            return ''
        decoded_words = []
        for word, encoding in decode_header(s):
            if encoding is not None:
                try:
                    word = word.decode(encoding)
                except LookupError:
                    # 如果遇到未知编码，尝试使用常见的编码
                    try:
                        word = word.decode('utf-8')
                    except UnicodeDecodeError:
                        word = word.decode('iso-8859-1', errors='ignore')
            elif isinstance(word, bytes):
                # 尝试 UTF-8 解码，或者您可以使用其他编码
                try:
                    word = word.decode('utf-8')
                except UnicodeDecodeError:
                    word = word.decode('iso-8859-1', errors='ignore')
            decoded_words.append(word)
        return ''.join(decoded_words)

    def clean_message_id(self, message_id):
        """
        清理不符合RFC标准的Message-ID，移除不必要的方括号。
        例如 '[abc123]@example.com' -> 'abc123@example.com'
        """
        # 使用正则表达式去除多余的方括号，并保留实际的内容
        cleaned_message_id = re.sub(r'\[([^\]]+)\]', r'\1', message_id)
        return cleaned_message_id

    def process_eml_content(self, eml_content):
        result = ''
        if isinstance(eml_content, list):
            # 遍历列表中的每个元素
            for item in eml_content:
                try:
                    # 手动从头部字段中获取 Message-ID
                    if isinstance(item, Message):
                        # 获取 Message 的所有头部
                        for header, value in item.raw_items():
                            if header.lower() == 'message-id':
                                print(header, value)
                                # 清理不合规的 Message-ID
                                cleaned_message_id = self.clean_message_id(value)
                                # 替换清理后的 Message-ID
                                item.replace_header('Message-ID', cleaned_message_id)
                                break
                except Exception as e:
                    print(f"Error retrieving Message-ID: {e}")

                # 将每个元素转换为字符串，并添加到 result 字符串中
                try:
                    result += str(item)
                except Exception as e:
                    print(f"Error converting item to string: {e}")

            # 最后，将拼接好的字符串赋值回 eml_content
            eml_content = result

        return eml_content




class CommonUtils:

    @staticmethod
    def calculate_file_hash(filename, chunk_size=8192):
        """计算文件的SHA256哈希值"""
        sha256 = hashlib.sha256()
        with open(filename, 'rb') as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def generate_hash_id(input_string):
        # 使用 SHA-256 生成哈希
        sha256 = hashlib.sha256()
        sha256.update(input_string.encode('utf-8'))

        hash_int = int(sha256.hexdigest()[:16], 16)  # 取前 16 个十六进制字符

        return hash_int


