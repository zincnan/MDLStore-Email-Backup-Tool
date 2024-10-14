import email
import os
import re
from email.header import decode_header
from email.policy import default
from email.utils import parsedate_to_datetime

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QLayout, QMessageBox
from bs4 import BeautifulSoup


class _Signals(QObject):
    # 搜索结束
    search_finished = pyqtSignal()
    # 读邮件内容
    read_email_ready = pyqtSignal(object)
    # 页面跳转
    jump_page = pyqtSignal(int)
    # 刷新磁盘视图
    flush_storage_infos = pyqtSignal()


APP_Signals = _Signals()


class UiUtils:
    @staticmethod
    def replace_or_insert_widget(placeholder, new_widget):
        """替换QWidget或将新部件插入到QFrame中"""
        layout = placeholder.layout()
        if layout is None:
            layout = QVBoxLayout(placeholder)
            placeholder.setLayout(layout)

        if isinstance(placeholder, QFrame):
            # 如果 placeholder 是 QFrame，确保其有一个布局，并将新部件添加进去
            layout = placeholder.layout()

            # 清除旧的部件
            while layout.count():
                old_widget = layout.takeAt(0).widget()
                if old_widget is not None:
                    old_widget.deleteLater()
            # 插入新的部件
            layout.addWidget(new_widget)
        elif isinstance(placeholder, QWidget):
            # 如果 placeholder 是 QWidget，替换它
            parent_layout = placeholder.parentWidget().layout()
            if parent_layout is not None:
                index = parent_layout.indexOf(placeholder)
                if index != -1:
                    # 先移除旧的部件
                    old_widget = parent_layout.takeAt(index).widget()
                    if old_widget is not None:
                        old_widget.deleteLater()
                    # 添加新的部件
                    parent_layout.insertWidget(index, new_widget)
                    new_widget.setParent(placeholder.parentWidget())
            else:
                print("Parent layout not found")
        else:
            print("Placeholder must be either QFrame or QWidget")

    @staticmethod
    def set_stretch_by_widget(layout, widget, stretch):
        """根据部件对象设置拉伸比例"""
        index = layout.indexOf(widget)
        if index != -1:
            layout.setStretch(index, stretch)

        # if isinstance(widget, QLayout):
        #     # QLayout 对象处理
        #     index = layout.indexOf(widget.itemAt(0).widget())
        #     if index != -1:
        #         layout.setStretch(index, stretch)
        # else:
        #     # QWidget 对象处理
        #     index = layout.indexOf(widget)
        #     if index != -1:
        #         layout.setStretch(index, stretch)


class EmailParser:
    """已被注释
    一个用来解码邮件内容的解析器，用来解析邮件头、邮件体、附件内容
    """

    def __init__(self, raw_email_data):
        self.raw_email = raw_email_data
        # self.msg = email.message_from_bytes(raw_email_data, policy=default)
        self.msg = email.message_from_bytes(raw_email_data, policy=default)

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
                        file_size = len(file_content) / 1024  # 计算文件大小
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
                        if isinstance(eml_content, list):
                            eml_content = ''.join([str(item) for item in eml_content])
                        file_size = len(eml_content.encode('utf-8'))  # 计算文件大小
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
                            eml_content = ''.join([str(item) for item in eml_content])
                        return eml_content.encode('utf-8')
                    else:
                        file_content = part.get_payload(decode=True)
                        return file_content
        return None

    def get_attachment_base64_by_filename(self, filename):
        """
        获取邮件中附件文件名为 filename 的附件文件的 Base64 编码内容。
        :param filename: 要查找的附件文件的名称
        :return: 附件文件的 Base64 编码字符串，如果未找到文件则返回 None
        """
        for part in self.msg.walk():
            content_disposition = part.get("Content-Disposition")
            if content_disposition and "attachment" in content_disposition:
                part_filename = part.get_filename()
                if part_filename == filename:
                    # 获取原始的 Base64 编码内容
                    base64_content = part.get_payload()  # 获取附件的Base64编码内容
                    return base64_content
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

    def extract_images(self):
        """提取内联图片，返回图片列表，列表项记录图片名称，cid和base64编码，无内联图片则返回空列表"""
        images = []

        for part in self.msg.walk():
            content_type = part.get_content_type()
            if content_type.startswith("image/"):
                cid = part.get("Content-ID")
                if cid:
                    cid = cid.strip("<>")
                    extension = content_type.split("/")[-1]  # 获取图片扩展名
                    image_base64 = part.get_payload()  # 直接获取邮件中已存在的 base64 编码数据
                    image_filename = f"图片_inline_{cid}.{extension}"

                    images.append({
                        "filename": image_filename,
                        "cid": cid,
                        "base64": image_base64
                    })

        if not images:
            # print("未找到任何内联图片。")
            pass
        else:
            # print(f"共提取了 {len(images)} 张内联图片。")
            pass
        return images

    # def extract_images(self):
    #     """提取内联图片，返回图片列表，列表项记录图片名称，cid和base64编码，无内联图片则返回空列表"""
    #     images = []
    #
    #     for part in self.msg.walk():
    #         content_type = part.get_content_type()
    #         if content_type.startswith("image/"):
    #             cid = part.get("Content-ID")
    #             if cid:
    #                 cid = cid.strip("<>")
    #                 extension = content_type.split("/")[-1]  # 获取图片扩展名
    #                 image_data = part.get_payload(decode=True)
    #                 image_base64 = base64.b64encode(image_data).decode('utf-8')
    #                 image_filename = f"图片_inline_{cid}.{extension}"
    #
    #                 images.append({
    #                     "filename": image_filename,
    #                     "cid": cid,
    #                     "base64": image_base64
    #                 })
    #
    #     if not images:
    #         print("未找到任何内联图片。")
    #     else:
    #         print(f"共提取了 {len(images)} 张内联图片。")
    #
    #     return images

    def decode_mime_words(self, s):
        """ 解码 MIME 字符串，正确处理各种编码 """
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


def replace_cid_with_base64(html_content, images):
    """
    替换HTML文档中的cid引用为base64编码
    :param html_content: 原始HTML文档
    :param images: 内联图片列表，包含cid和base64编码
    :return: 替换后的HTML文档
    """
    for image in images:
        cid = image['cid']
        base64_data = image['base64']
        # 创建 Base64 图片数据的 src 属性
        img_src = f"data:image/jpeg;base64,{base64_data}"
        # 替换 HTML 中的 cid 引用
        html_content = html_content.replace(f'src="cid:{cid}"', f'src="{img_src}"')

    return html_content


class MessageDialog:
    @staticmethod
    def show_error(message):
        """
        使用 QMessageBox 显示错误提示信息，并设置按钮为中文
        :param message: 要显示的错误信息
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("输入错误")

        # 设置标准按钮
        msg.setStandardButtons(QMessageBox.Ok)

        # 将按钮设置为中文
        button = msg.button(QMessageBox.Ok)
        button.setText("确定")

        msg.exec_()