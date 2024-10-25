import codecs
import email
import imaplib
import os
import sys
from abc import ABC, abstractmethod
from email.header import decode_header
from email.utils import parsedate_to_datetime

from MDLStore.utils import EmailUtils

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


class IMAPClientBase(ABC):
    def __init__(self, server, port, username, password, ssl=True):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.ssl = ssl
        self.client = None

    def connect(self):
        try:
            if self.ssl:
                self.client = imaplib.IMAP4_SSL(self.server, self.port)
            else:
                self.client = imaplib.IMAP4(self.server, self.port)
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def capability(self):
        """发送CAPABILITY命令并打印服务器的能力。"""
        typ, data = self.client.capability()
        if typ == 'OK':
            print("Capabilities:", data)
        else:
            print("Failed to get capabilities")

    def authenticate(self):
        pass

    @abstractmethod
    def login(self):
        pass

    # LIST 命令
    def get_mailbox_list(self):
        """获取并打印邮箱列表。"""
        mailboxes = []
        status, mailbox_list = self.client.list()
        # print(f"Source Mailbox list:{mailbox_list}")
        for mailbox in mailbox_list:
            parts = mailbox.decode().split(' "/" ')
            if len(parts) > 1:
                # 解码邮箱名称
                # print(f'原始文件夹名称：{parts[1]}')
                # print(('"Sent Messages"' == parts[1]))
                mailbox_name = self.decode_modified_utf7(parts[1])
                # print(f'邮箱名{mailbox_name}')
                mailboxes.append(mailbox_name)
            else:
                # print(parts[0])
                mailboxes.append(mailbox_name)
        return mailboxes

    @staticmethod
    def decode_modified_utf7(s):
        """将Modified UTF-7编码的字符串解码为unicode字符串。"""
        utf7_encoded = s.encode('ascii').replace(b'&', b'+').replace(b',', b'/')
        try:
            decoded_string = codecs.decode(utf7_encoded, 'utf-7')
        except Exception as e:
            print(f"解码失败: {e}")
            decoded_string = s  # 解码失败，返回原字符串
        return decoded_string

    def disconnect(self):
        if self.client:
            self.client.logout()
            self.client = None

    def search_emails(self, folder, criteria):
        if not self.client:
            raise Exception("Not connected to the server. Please connect first.")
        status, count = self.client.select(folder)
        print(f'文件夹选中状态{status},存在邮件{count}封')
        status, messages = self.client.uid('search', None, criteria)  # 使用UID来执行搜索
        # 检查是否成功获取到邮件UID列表
        if status != 'OK':
            print("No messages found!")
        else:
            # 邮件UID列表
            message_uids = messages[0].split()
            print(f"Total messages Found: {len(message_uids)}")
            print("Message UIDs:", message_uids)

        return messages[0].split()

        # 选择邮箱文件夹（例如'INBOX'）
        # status, response = self.client.select(folder)
        # print('status:', status)
        # # 搜索最新一封邮件
        # status, response = self.client.uid('search', None, criteria)
        # print('status:', status)
        # latest_email_id = response[0].split()
        # print(latest_email_id)
        # return latest_email_id

    def fetch_all_text(self, uid):
        result, data = self.client.uid('fetch', uid, '(RFC822)')
        if result == 'OK':
            # 解析邮件内容
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            # 假设raw_email是你从服务器获取的原始邮件数据
            with open('raw_email.eml', 'wb') as file:
                file.write(raw_email)
            # 假设msg是通过email.message_from_bytes(raw_email)得到的EmailMessage对象
            with open('parsed_email.eml', 'w', encoding='utf-8') as file:
                file.write(msg.as_string())

            # 解码邮件主题
            # subject, encoding = decode_header(msg['Subject'])[0]
            #
            # if isinstance(subject, bytes):
            #     subject = subject.decode(encoding or 'utf-8')

            # 解码邮件主题
            subject = msg['Subject']
            if subject is not None:
                # 尝试解码主题
                try:
                    subject, encoding = decode_header(subject)[0]
                    if isinstance(subject, bytes):
                        # 如果主题是字节序列，则解码为字符串
                        subject = subject.decode(encoding or 'utf-8')
                except Exception as e:
                    print(f"解码主题时出错: {e}")
                    subject = None  # 或者使用默认值或错误值
            else:
                print("没有找到主题")
                subject = None  # 或者使用默认值或错误值

            # 解码发件人
            from_header = decode_header(msg.get("From"))[0]
            if isinstance(from_header[0], bytes):
                from_sender = from_header[0].decode(from_header[1] or 'utf-8')
            else:
                from_sender = from_header[0]

            # 解码收件人
            to_header = decode_header(msg.get("To"))[0]
            if isinstance(to_header[0], bytes):
                to_recipient = to_header[0].decode(to_header[1] or 'utf-8')
            else:
                to_recipient = to_header[0]

            # 获取发送日期
            # date_header = msg.get("Date")
            # date_parsed = parsedate_to_datetime(date_header)

            # 获取发送日期
            date_header = msg['Date']
            # 检查date_header是否为None或空字符串
            if date_header:
                try:
                    date_parsed = parsedate_to_datetime(date_header)
                    # 接下来的代码逻辑...
                except Exception as e:
                    print(f"解析日期时发生错误: {e}")
                    # 可以设置date_parsed为None或其他默认值
                    date_parsed = None
            else:
                print("日期头部为空或不存在")
                # 可以设置date_parsed为None或其他默认值
                date_parsed = None

            # 打印信息
            print(f"UID: {uid.decode('utf-8')}")
            print(f"Subject: {subject}")
            print(f"From: {from_sender}")
            print(f"To: {to_recipient}")
            print(f"Date: {date_parsed}")

            # # 获取并打印邮件正文
            # if msg.is_multipart():
            #     for part in msg.walk():
            #         content_type = part.get_content_type()
            #         content_disposition = part.get("Content-Disposition")
            #         if content_type == "text/plain" and "attachment" not in content_disposition:
            #             # 打印text/plain类型的邮件正文
            #             print(part.get_payload(decode=True).decode())
            #         elif content_type == "text/html" and "attachment" not in content_disposition:
            #             # 如果你也想打印HTML内容，可以在这里处理
            #             pass
            # else:
            #     # 处理非multipart类型的邮件正文
            #     print(msg.get_payload(decode=True).decode())

    def saveEmails(self, folder, criteria, progress_callback=None, info_callback=None):
        """
        将目标文件夹中符合条件的邮件保存到本地。每封邮件保存为一个EML文件。按照邮箱文件夹结构保存.
        比如要备份的zinc@ruc.edu.cn中已发送的邮件。那么目标位置就是有一个zinc@ruc.edu.cn文件夹，
        内部有“已发送文件夹”，其中保存若干个符合条件的邮件
        :param progress_callback:
        :param info_callback:
        :param folder: 文件夹比如"收件箱","已发送"等
        :param criteria: SINCE date BEFORE date
        :return: 保存完毕返回True
        """
        folder = EmailUtils.encode_modified_utf7(folder)
        # print(f'新文件夹名{folder}')
        folder_select = f"\"{folder}\""
        print(f'选中的文件夹名{folder_select}')
        folder_select = folder_select.replace(',','/')
        self.client.select(folder_select, readonly=True)
        # print('搜索邮件')
        # 搜索邮件
        status, messages = self.client.search(None, criteria)
        if status != 'OK':
            print(f"Failed to search emails with criteria: {criteria}")
            return False

        # 处理每封邮件
        msg_nums = messages[0].split()
        # email_dir = os.path.join(self.username, folder)
        utf8_folder = EmailUtils.decode_modified_utf7(folder)
        email_dir = os.path.join(temp_dir, self.username, utf8_folder)
        os.makedirs(email_dir, exist_ok=True)

        total_count = len(msg_nums)
        print(f'共搜索到邮件{total_count}封')
        for i, num in enumerate(msg_nums):
            print(f'正在处理第{i+1}/{total_count}封')
            status, msg_data = self.client.fetch(num, '(RFC822)')
            if status != 'OK':
                print(f"Failed to fetch email number: {num}")
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            # msg_subject = msg.get('Subject', 'No_Subject').replace('/', '_')
            # msg_date = msg.get('Date', 'No_Date')
            msg_filename = f"email{str(num)}.eml"

            with open(os.path.join(email_dir, msg_filename), 'wb') as f:
                f.write(msg_data[0][1])

            if progress_callback and info_callback:
                progress_callback.emit(int(((i + 1) / total_count) * 100))
                info_callback.emit(f'已获取邮件{i}封/{total_count}封')

        print(f"Emails saved to {email_dir}")
        return True

    def select_folder(self, folder):
        try:
            folder = f"\"{folder}\""
            # 尝试选择指定的文件夹
            typ, data = self.client.select(folder)
            # 如果typ为'OK'，表示成功选择了文件夹
            if typ == 'OK':
                print("Successfully selected folder:", folder)
                return True
            else:
                print("Failed to select folder:", folder, "Response:", data)
                return False
        except imaplib.IMAP4.error as e:
            # 打印错误信息
            print("IMAP error occurred:", e)
            return False
        except Exception as e:
            # 处理其他可能的异常
            print("An error occurred:", e)
            return False


class GmailClient(IMAPClientBase):
    def login(self):
        self.client.login(self.username, self.password)


class NetEClient(IMAPClientBase):
    def login(self):
        self.client.login(self.username, self.password)
        imaplib.Commands['ID'] = ('AUTH')
        args = ("name", "your-name", "contact", self.username, "version", "1.0.0", "vendor", "myclient")
        typ, dat = self.client._simple_command('ID', '("' + '" "'.join(args) + '")')
        # print(self.client._untagged_response(typ, dat, 'ID'))


class NetE126Client(IMAPClientBase):
    def login(self):
        self.client.login(self.username, self.password)
        imap_id = ("name", "RPA robot", "version", "1.0.0", "vendor", "ins")
        typ, data = self.client.xatom('ID', '("' + '" "'.join(imap_id) + '")')


class NetERucClient(IMAPClientBase):
    def login(self):
        self.client.login(self.username, self.password)


class OutlookClient(IMAPClientBase):
    def login(self):
        self.client.login(self.username, self.password)


class QmailClient(IMAPClientBase):
    def login(self):
        self.client.login(self.username, self.password)


class SinaClient(IMAPClientBase):
    def login(self):
        self.client.login(self.username, self.password)


class Mail139Client(IMAPClientBase):
    def login(self):
        self.client.login(self.username, self.password)


class Mail189Client(IMAPClientBase):
    def login(self):
        self.client.login(self.username, self.password)


class SohuClient(IMAPClientBase):
    def login(self):
        self.client.login(self.username, self.password)


class IMAPClientFactory:
    @staticmethod
    def get_client(client_type_, *args, **kwargs):
        if client_type_ == 'gmail':
            return GmailClient(*args, **kwargs)
        elif client_type_ == 'netease':
            return NetEClient(*args, **kwargs)
        elif client_type_ == 'nete126':
            return NetE126Client(*args, **kwargs)
        elif client_type_ == 'rucmail':
            return NetERucClient(*args, **kwargs)
        elif client_type_ == 'qmail':
            return QmailClient(*args, **kwargs)
        elif client_type_ == 'outlook':
            return OutlookClient(*args, **kwargs)
        elif client_type_ == 'sina':
            return SinaClient(*args, **kwargs)
        elif client_type_ == 'mail139':
            return Mail139Client(*args, **kwargs)
        elif client_type_ == 'mail189':
            return Mail189Client(*args, **kwargs)
        elif client_type_ == 'sohu':
            return SohuClient(*args, **kwargs)
        else:
            raise ValueError("Unknown client type")


if __name__ == "__main__":
    # 根据某些运行时条件选择客户端类型
    client_type = 'gmail'
    print(f'client_type={client_type}')
    client = IMAPClientFactory.get_client(client_type, 'imap.gmail.com', 993, 'your_username@gmail.com',
                                          'your_password')
    # 在这里使用client进行操作
