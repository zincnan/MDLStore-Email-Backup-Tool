import datetime
import hashlib
import http.client
import json
import math
import os
import re
import urllib.parse
import zlib

from bs4 import BeautifulSoup


class CloudFileParser:
    def __init__(self, provider_):
        """
        一个用来提取当前页面，所有该运营商的云附件的解析器
        初始化 CloudFileParser 类，根据 provider 创建具体的解析器实例
        :param provider_: 云附件提供商
        """
        self.provider = provider_

    @staticmethod
    def create_parser(provider_):
        parsers = {
            "QQ": QQCloudFileParser,
            "163": NeteaseCloudFileParser,
            "126": NeteaseCloudFileParser,
            "Gmail": GmailCloudFileParser,
            "Outlook": OutlookCloudFileParser,
            "189": Cloud189FileParser,
            "RUC": RUCCloudFileParser,
            "Sina": SinaCloudFileParser
        }
        parser_class = parsers.get(provider_)
        if parser_class:
            return parser_class()
        else:
            raise ValueError("Unsupported provider")

    def get_cloud_file_info(self, html):
        """
        获取页面中全部的该运营商的云附件信息
        :param html:
        :return:一个列表，列表项目为字典，表示一个云附件的信息，字典结构如下 {
            "filename": "example_filename_ruc",
            "file_size": "example_size_ruc",
            "expire_time": "2024-08-04 23:48",
            "expired": False,
            "outside_link": self.url
        }
        """
        raise NotImplementedError("This method should be overridden in subclasses")


class QQCloudFileParser(CloudFileParser):
    def __init__(self):
        super().__init__("QQ")

    def get_cloud_file_info(self, html):
        """
        实现QQ云附件的解析逻辑
        :param html: 邮件正文的HTML内容
        :return: 包含文件名、链接等信息的字典列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        cloud_file_info_list = []

        # 查找所有包含云附件链接的部分
        attach_divs = soup.find_all('div', class_='bigatt_bt')
        for attach_div in attach_divs:
            file_info = {}
            file_link_tag = attach_div.find('a', href=True)
            if file_link_tag:
                file_info['outside_link'] = file_link_tag['href']

                # 提取文件名、文件大小和过期时间
                title = attach_div.get('title', '')
                filename_match = re.search(r'^(.+?)\s*[\r\n]', title)
                file_size_match = re.search(r'文件大小：([\d.]+[KM])', title)
                # expire_time_match = re.search(r'到期时间：([^\s]+)', title)  # 精确到日期
                # expire_time_match = re.search(r'到期时间：([^\s]+ [^\s]+)', title)
                expire_time_match = re.search(r'到期时间：([^\s]+ [^\s]+|无限期)', title)

                file_info['filename'] = filename_match.group(1) if filename_match else 'Unknown'
                size_str = file_size_match.group(1) if file_size_match else 'Unknown'
                # file_info['file_size'] = file_size_match.group(1) if file_size_match else 'Unknown'
                file_info['file_size'] = self._convert_to_kb(size_str)
                expire_date_time_str = expire_time_match.group(1) if expire_time_match else 'Unknown'
                # file_info['expire_time'] = expire_time_match.group(1) if expire_time_match else 'Unknown'
                file_info['expire_time'] = expire_date_time_str
                is_expired = self._is_expired(expire_date_time_str)
                file_info['expired'] = is_expired
                cloud_file_info_list.append(file_info)

        return cloud_file_info_list

    def _convert_to_kb(self, size_str):
        # 提取数字部分和单位部分
        size_str = size_str.strip()
        if size_str.endswith('K'):
            size = float(size_str[:-1])
            unit = 'K'
        elif size_str.endswith('M'):
            size = float(size_str[:-1])
            unit = 'M'
        elif size_str.endswith('G'):
            size = float(size_str[:-1])
            unit = 'G'
        else:
            raise ValueError("Unknown unit in size string")

        # 根据单位转换为K字节
        if unit == 'K':
            return size  # 已经是K字节
        elif unit == 'M':
            return size * 1024  # 1M = 1024K
        elif unit == 'G':
            return size * 1024 * 1024  # 1G = 1024 * 1024K

    def _is_expired(self, date_str):
        """
        判断日期是否已经过期
        :param date_str: 日期时间字符串，格式为 实例'2024年08月22日 17:33'
        :return: 如果过期返回 False，否则返回 True
        """
        if date_str == '无限期':
            return True
        # print(date_str)
        date_format = '%Y年%m月%d日 %H:%M'
        # 将日期字符串转换为 datetime 对象
        target_date = datetime.datetime.strptime(date_str, date_format)
        # 获取当前日期和时间
        current_date = datetime.datetime.now()

        # 比较两个日期和时间
        return target_date > current_date


class NeteaseCloudFileParser(CloudFileParser):
    def __init__(self):
        super().__init__("163/126")

    def _convert_to_kb(self, size_str):
        """
        将文件大小转换为KB
        """
        size_str = size_str.lower()
        if 'k' in size_str:
            return float(size_str.replace('k', '').strip())
        elif 'm' in size_str:
            return float(size_str.replace('m', '').strip()) * 1024
        elif 'g' in size_str:
            return float(size_str.replace('g', '').strip()) * 1024 * 1024
        return 0

    def _is_expired(self, date_str):
        """
        判断日期是否已经过期
        :param date_str: 日期时间字符串，格式为 实例'2024年08月22日 17:33'
        :return: 如果过期返回 False，否则返回 True
        """
        date_str = date_str[:-1]
        if date_str == '无限期':
            return True
        # print(date_str)
        date_format = '%Y年%m月%d日 %H:%M'
        # 将日期字符串转换为 datetime 对象
        target_date = datetime.datetime.strptime(date_str, date_format)
        # 获取当前日期和时间
        current_date = datetime.datetime.now()

        # 比较两个日期和时间
        return target_date > current_date

    def get_cloud_file_info(self, html):
        """
        解析网易云附件的HTML，提取所有云附件的信息，包括文件名、过期时间、文件大小和下载链接
        :param html: 邮件正文的HTML内容
        :return: 包含文件名、过期时间、文件大小和下载链接的字典列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        cloud_file_info_list = []

        # 查找所有云附件的相关部分
        cloud_attach_items = soup.find_all('div', style=lambda
            value: value and 'clear:both;height:36px;padding:6px 4px' in value)
        for item in cloud_attach_items:
            cloud_file_info = {}

            # 获取文件名和下载链接
            file_name_tag = item.find('a', download=True)
            if file_name_tag:
                cloud_file_info['filename'] = file_name_tag.get('filename', '').strip()
                cloud_file_info['outside_link'] = file_name_tag.get('href', '')

            # 获取文件大小和过期时间
            file_size_tag = item.find('span', style=lambda value: value and 'color:#bbb' in value)
            if file_size_tag:
                file_size_text = file_size_tag.get_text(strip=True)
                size_expiry_parts = file_size_text.split(',')
                if len(size_expiry_parts) == 2:
                    size_str = size_expiry_parts[0].strip().replace('(', '')
                    cloud_file_info['file_size'] = self._convert_to_kb(size_str)

                    expire_time_text = size_expiry_parts[1].strip().replace('到期)', '')
                    date_format = '%Y年%m月%d日 %H:%M'

                    # 解析过期时间
                    try:
                        expire_date = datetime.datetime.strptime(expire_time_text, date_format)
                        cloud_file_info['expire_time'] = expire_date.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        cloud_file_info['expire_time'] = expire_time_text

                    ttt = cloud_file_info['expire_time']
                    cloud_file_info['expired'] = self._is_expired(ttt)

            cloud_file_info_list.append(cloud_file_info)

        return cloud_file_info_list


class GmailCloudFileParser(CloudFileParser):
    def __init__(self):
        super().__init__("Gmail")

    from bs4 import BeautifulSoup

    def get_cloud_file_info(self, html):
        """
        解析Gmail云附件的HTML，提取文件名、文件大小、过期时间和下载链接
        :param html: 邮件正文的HTML内容
        :return: 包含文件名、文件大小、过期时间、过期状态和外部链接的字典列表
        """
        print(f'获取gmail云附件信息')
        soup = BeautifulSoup(html, 'html.parser')
        cloud_file_info_list = []

        # 查找包含云附件信息的 div 元素
        attachment_divs = soup.find_all('div', class_='gmail_chip gmail_drive_chip')
        for div in attachment_divs:
            file_info = {}

            # 提取文件名
            filename_tag = div.find('span', dir='ltr')
            if filename_tag:
                file_info['filename'] = filename_tag.get_text(strip=True)
            else:
                file_info['filename'] = "Unknown"

            # 提取外部链接
            link_tag = div.find('a', href=True)
            if link_tag:
                file_info['outside_link'] = link_tag['href']
            else:
                file_info['outside_link'] = "No Link"
            # 设置其他固定信息
            file_info['file_size'] = self.get_file_size(file_info['outside_link'])  # 设为固定值 0
            file_info['expire_time'] = 'No Expiry'
            file_info['expired'] = True

            # 添加至列表
            cloud_file_info_list.append(file_info)

        return cloud_file_info_list

    @staticmethod
    def get_file_size(url):
        # Gmail邮箱特殊处理，因网络连接问题不下载Gmail云附件。
        return 0


class OutlookCloudFileParser(CloudFileParser):
    def __init__(self):
        super().__init__("Outlook")

    def get_cloud_file_info(self, html):
        """
        实现Outlook云附件的解析逻辑
        :param html: 邮件正文的HTML内容
        :return: 包含文件名、链接等信息的字典列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        cloud_file_info_list = []

        # 查找所有包含云附件链接的部分
        link_tags = soup.find_all('a', href=True)
        for link_tag in link_tags:
            if '1drv.ms' in link_tag['href']:
                cloud_file_info = {
                    "filename": link_tag.get_text(strip=True).replace('\r', '').replace('\n', ''),
                    "file_size": 0,  # 无法从HTML中直接获取文件大小
                    "expire_time": "NoExpire",  # 无法从HTML中直接获取过期时间
                    "expired": True,  # 无法从HTML中直接获取是否过期
                    "outside_link": link_tag['href']
                }
                cloud_file_info_list.append(cloud_file_info)

        return cloud_file_info_list


class Cloud189FileParser(CloudFileParser):
    def __init__(self):
        super().__init__("189")

    def get_cloud_file_info(self, html):
        """
        解析天翼云盘附件的HTML，提取文件名、过期时间和文件大小
        :param html: 邮件正文的HTML内容
        :return: 包含文件名、下载链接、文件大小和过期时间的字典列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        cloud_file_info_list = []

        # 查找所有包含附件信息的 div 标签
        cloud_attach_divs = soup.find_all('div', style=lambda value: value and 'clear:both' in value)

        for attach_div in cloud_attach_divs:
            cloud_file_info = {}

            # 获取文件名和下载链接
            file_name_tag = attach_div.find('a', href=True)
            if file_name_tag:
                cloud_file_info['filename'] = file_name_tag.text.strip()
                cloud_file_info['outside_link'] = file_name_tag['href']

                # 获取过期时间（从链接中提取）
                expired_match = re.search(r'expired=(\d+)', cloud_file_info['outside_link'])
                if expired_match:
                    expire_timestamp = int(expired_match.group(1)) / 1000  # 转换为秒
                    expire_time = datetime.datetime.fromtimestamp(expire_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    cloud_file_info['expire_time'] = expire_time
                    cloud_file_info['expired'] = self._is_expired(expire_time)

                # 获取文件大小（从 alt 属性中提取）
                filesize_match = re.search(r'\((\d+)\)', file_name_tag.get('alt', ''))
                if filesize_match:
                    file_size_bytes = int(filesize_match.group(1))
                    file_size_kb = file_size_bytes / 1024
                    file_size_kb_rounded = math.ceil(file_size_kb * 100) / 100
                    cloud_file_info['file_size'] = file_size_kb_rounded
                else:
                    cloud_file_info['file_size'] = '未知大小'  # 如果无法获取文件大小

            cloud_file_info_list.append(cloud_file_info)

        return cloud_file_info_list

    def _is_expired(self, date_str):
        """
        判断日期是否已经过期
        :param date_str: 日期时间字符串，格式实例为'2024-08-04 13:56:45'
        :return: 如果过期返回 False，否则返回 True
        """
        date_format = '%Y-%m-%d %H:%M:%S'
        # 将日期时间字符串转换为 datetime 对象
        target_date = datetime.datetime.strptime(date_str, date_format)

        # 获取当前日期和时间
        current_date = datetime.datetime.now()

        # 比较两个日期和时间
        return target_date > current_date


class RUCCloudFileParser(CloudFileParser):
    def __init__(self):
        super().__init__("RUC")

    def get_cloud_file_info(self, html):
        """
        解析 HTML 并提取出所有 RUC 邮箱云附件的信息
        :param html: 邮件正文的HTML内容
        :return: 返回一个包含所有云附件信息的列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        cloud_file_info_list = []

        # 查找所有附件的div标签
        cloud_attach_items = soup.find_all('div', style=lambda value: value and 'width: 392px' in value)

        for item in cloud_attach_items:
            # 每个附件的字典信息
            cloud_file_info = {}

            # 获取文件名和下载链接
            file_name_tag = item.find('a', download=True)
            if file_name_tag:
                cloud_file_info['filename'] = file_name_tag.get_text(strip=True)
                cloud_file_info['outside_link'] = file_name_tag.get('href', '')

            # 获取文件大小和过期时间
            file_info_tag = item.find('div', style=lambda value: value and 'opacity: 0.4' in value)
            if file_info_tag:
                file_info_text = file_info_tag.get_text(strip=True)
                size_expiry_parts = file_info_text.split('|')
                if len(size_expiry_parts) == 2:
                    size_str = size_expiry_parts[0].strip()
                    cloud_file_info['file_size'] = self._convert_to_kb(size_str)

                    expire_time_str = size_expiry_parts[1].replace('过期时间：', '').strip()
                    cloud_file_info['expire_time'] = expire_time_str
                    cloud_file_info['expired'] = self._is_expired(expire_time_str)

            # 将每个附件信息添加到列表
            cloud_file_info_list.append(cloud_file_info)

        return cloud_file_info_list

    def _convert_to_kb(self, size_str):
        """
        将文件大小转换为KB
        """
        size_str = size_str.lower()
        if 'k' in size_str:
            return float(size_str.replace('k', '').strip())
        elif 'm' in size_str:
            return float(size_str.replace('m', '').strip()) * 1024
        elif 'g' in size_str:
            return float(size_str.replace('g', '').strip()) * 1024 * 1024
        return 0

    def _is_expired(self, date_str):
        """
        判断日期是否已经过期
        :param date_str: 日期时间字符串，格式为 实例'2024年8月4日 23:48'
        :return: 如果过期返回 False，否则返回 True
        """
        # print(date_str)
        date_format = '%Y年%m月%d日 %H:%M'
        # 将日期字符串转换为 datetime 对象
        target_date = datetime.datetime.strptime(date_str, date_format)
        # 获取当前日期和时间
        current_date = datetime.datetime.now()

        # 比较两个日期和时间
        return target_date > current_date


class SinaCloudFileParser(CloudFileParser):
    def __init__(self):
        super().__init__("Sina")

    def get_cloud_file_info(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        attachments = []
        # 查找所有附件的容器
        att_containers = soup.find_all('div', style=lambda value: value and 'margin-top: 20px' in value)

        for container in att_containers:
            files = container.find_all('div', style=lambda value: value and 'margin-bottom: 2px' in value)
            for file in files:
                file_info = {}
                file_name_span = file.find('span', style=lambda value: value and 'font-weight: bold' in value)
                if file_name_span:
                    # 提取文件名和大小
                    full_text = file_name_span.text.strip()
                    size_match = re.search(r'\((.*?)\)', full_text)
                    if size_match:
                        file_size_str = size_match.group(1)
                        # file_info['file_size'] = size_match.group(1)
                        file_info['file_size'] = self._convert_to_kb(file_size_str)
                        file_info['filename'] = full_text[:full_text.rfind('(')].strip()

                expire_info_div = container.find('div', style=lambda value: value and 'font-size: 13px' in value)
                if expire_info_div:
                    expire_text = expire_info_div.text.strip()
                    expire_time = re.search(r'有效时间到：(.*?)\)', expire_text)
                    if expire_time:
                        file_info['expire_time'] = expire_time.group(1)
                        # file_info['expired'] = False
                        file_info['expired'] = self._is_expired(file_info['expire_time'])

                download_link = file.find('a', href=True)
                if download_link:
                    file_info['outside_link'] = download_link['href']

                if file_info:
                    attachments.append(file_info)

        return attachments

    # def get_cloud_file_info(self, html):
    #     """
    #     实现Sina云附件的解析逻辑
    #     :param html: 邮件正文的HTML内容
    #     :return: 包含文件名、链接等信息的字典列表
    #     """
    #     soup = BeautifulSoup(html, 'html.parser')
    #     attachment_infos = []
    #
    #     att_containers = soup.find_all('div', id='att_container')
    #     for att_container in att_containers:
    #         filename_and_size = att_container.find('span', style=lambda
    #             value: value and 'font-weight: bold' in value and 'font-family: Times New Roman,Georgia,Serif' in value)
    #         filename, file_size = "", ""
    #         if filename_and_size:
    #             filename_and_size_text = filename_and_size.text
    #             parts = filename_and_size_text.split('(')
    #             filename = parts[0].strip() if parts else ""
    #             file_size = parts[1].rstrip(')').strip() if len(parts) > 1 else ""
    #
    #         download_link = ""
    #         download_link_tag = att_container.find('a', text='下载')
    #         if download_link_tag and 'href' in download_link_tag.attrs:
    #             download_link = download_link_tag['href']
    #
    #         expire_info = att_container.find('div',
    #                                          text=lambda text: text and '来自中转站' in text and '有效时间到' in text)
    #         expire_time_str, expired = "", None
    #         if expire_info:
    #             expire_time_str = expire_info.text.split('到：')[-1].strip(') ').strip()
    #             try:
    #                 expire_time = datetime.datetime.strptime(expire_time_str, "%Y-%m-%d %H:%M:%S")
    #                 now = datetime.datetime.now()
    #                 expired = now > expire_time
    #             except ValueError as e:
    #                 print(f"Error parsing date: {e}")
    #                 expired = None
    #
    #         attachment_infos.append({
    #             "filename": filename,
    #             "file_size": file_size,
    #             "expire_time": expire_time_str,
    #             "expired": expired,
    #             "outside_link": download_link
    #         })
    #
    #     return attachment_infos

    # def get_cloud_file_info(self, html):
    #     """
    #     实现Sina云附件的解析逻辑
    #     :param html: 邮件正文的HTML内容
    #     :return: 包含文件名、链接等信息的字典列表
    #     """
    #     soup = BeautifulSoup(html, 'html.parser')
    #     attachment_infos = []
    #
    #     att_containers = soup.find_all('div', id='att_container')
    #     for att_container in att_containers:
    #         filename_and_size = att_container.find('span', style=lambda
    #             value: 'font-weight: bold' in value and 'font-family: Times New Roman,Georgia,Serif' in value)
    #         filename, file_size = "", ""
    #         if filename_and_size:
    #             filename_and_size_text = filename_and_size.text
    #             parts = filename_and_size_text.split('(')
    #             filename = parts[0].strip() if parts else ""
    #             file_size = parts[1].rstrip(')').strip() if len(parts) > 1 else ""
    #
    #         download_link = ""
    #         download_link_tag = att_container.find('a', text='下载')
    #         if download_link_tag and 'href' in download_link_tag.attrs:
    #             download_link = download_link_tag['href']
    #
    #         expire_info = att_container.find('div',
    #                                          text=lambda text: text and '来自中转站' in text and '有效时间到' in text)
    #         expire_time_str, expired = "", None
    #         if expire_info:
    #             # expire_time_str = expire_info.text.split('到：')[-1].strip()
    #             expire_time_str = expire_info.text.split('到：')[-1].strip(') ').strip()
    #             try:
    #                 expire_time = datetime.datetime.strptime(expire_time_str, "%Y-%m-%d %H:%M:%S")
    #                 now = datetime.datetime.now()
    #                 expired = now > expire_time
    #             except ValueError as e:
    #                 print(f"Error parsing date: {e}")
    #                 expired = None
    #
    #         # attachment_infos.append({
    #         #     "filename": filename,
    #         #     "file_size": file_size,
    #         #     "expire_time": expire_time_str,
    #         #     "expired": expired,
    #         #     "outside_link": download_link
    #         # })
    #         attachment_infos.append({
    #             "filename": filename,
    #             "file_size": self._convert_to_kb(file_size),
    #             "expire_time": expire_time_str,
    #             "expired": self._is_expired(expire_time_str),
    #             "outside_link": download_link
    #         })
    #
    #     return attachment_infos

    def _convert_to_kb(self, size_str):
        # 提取数字部分和单位部分
        size_str = size_str.strip()
        if size_str.endswith('K'):
            size = float(size_str[:-1])
            unit = 'K'
        elif size_str.endswith('M'):
            size = float(size_str[:-1])
            unit = 'M'
        elif size_str.endswith('G'):
            size = float(size_str[:-1])
            unit = 'G'
        else:
            raise ValueError("Unknown unit in size string")

        # 根据单位转换为K字节
        if unit == 'K':
            return size  # 已经是K字节
        elif unit == 'M':
            return size * 1024  # 1M = 1024K
        elif unit == 'G':
            return size * 1024 * 1024  # 1G = 1024 * 1024K

    def _is_expired(self, date_str):
        """
        判断日期是否已经过期
        :param date_str: 日期时间字符串，格式实例为'2024-08-04 13:56:45'
        :return: 如果过期返回 False，否则返回 True
        """
        date_format = '%Y-%m-%d %H:%M:%S'
        # 将日期时间字符串转换为 datetime 对象
        target_date = datetime.datetime.strptime(date_str, date_format)

        # 获取当前日期和时间
        current_date = datetime.datetime.now()

        # 比较两个日期和时间
        return target_date > current_date


class CloudAttachmentDownloader:
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

    def __init__(self, outside_link):
        self.outside_link = outside_link
        self.provider = self.get_cloud_file_provider(outside_link)
        # self.downloader = self.create_downloader()

    @staticmethod
    def get_cloud_file_provider(outside_link):
        """
        根据外部链接返回云附件服务提供商的名称
        :param outside_link: 外部链接
        :return: 返回名称
        """
        for provider, pattern in CloudAttachmentDownloader.patterns.items():
            if re.match(pattern, outside_link):
                return provider
        raise ValueError("Unsupported provider")

    def create_download_utils(self):
        if self.provider == "163" or self.provider == "126":
            return NeteaseDownloader(self.outside_link)
        elif self.provider == "QQ":
            return QQDownloader(self.outside_link)
        elif self.provider == "Gmail":
            return GmailDownloader(self.outside_link)
        elif self.provider == "Outlook":
            return OutlookDownloader(self.outside_link)
        elif self.provider == "189":
            return Cloud189Downloader(self.outside_link)
        elif self.provider == "RUC":
            return RUCDownloader(self.outside_link)
        elif self.provider == "Sina":
            return SinaDownloader(self.outside_link)
        else:
            raise ValueError("Unsupported provider")

    # @staticmethod
    # def get_download_url(download_url):
    #     pass
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
    def download_large_file(download_url, filename, headers={}):
        def generate_new_filename(filename_):
            base_name, extension = os.path.splitext(filename_)
            i = 1
            new_filename = f"{base_name}_{i}{extension}"
            while os.path.exists(new_filename):
                i += 1
                new_filename = f"{base_name}_{i}{extension}"
            return new_filename

        # 检查目标文件是否存在
        if os.path.exists(filename):
            print(f"File '{filename}' already exists. Checking for duplicates...")
            new_filename = generate_new_filename(filename)
            # 计算现有文件的哈希值
            existing_file_hash = CloudAttachmentDownloader.calculate_file_hash(filename)
        else:
            new_filename = filename
            existing_file_hash = None

        # 解析URL
        parsed_url = urllib.parse.urlparse(download_url)

        # 提取主机名和请求路径
        host = parsed_url.netloc
        path = f"{parsed_url.path}?{parsed_url.query}"

        # 创建HTTPS连接
        conn = http.client.HTTPSConnection(host)

        # 打印请求调试信息
        # print(f"Host: {host}")
        # print(f"Path: {path}")
        # if headers:
        #     print(f"Headers: {headers}")

        # 发送GET请求
        conn.request("GET", path, headers=headers)

        # 获取响应
        response = conn.getresponse()
        print(f"Response status: {response.status}, reason: {response.reason}")

        if response.status == 200:
            # 创建一个临时文件来保存下载的数据
            temp_filename = new_filename + '.tmp'
            with open(temp_filename, 'wb') as temp_file:
                while True:
                    # 逐块读取响应数据
                    chunk = response.read(8192)  # 8 KB块大小
                    if not chunk:
                        break
                    temp_file.write(chunk)
            if not os.path.exists(temp_filename) or os.path.getsize(temp_filename) == 0:
                print("Downloaded file is empty or does not exist.")
                os.remove(temp_filename)
                return False, None
            # 计算下载文件的哈希值
            downloaded_file_hash = CloudAttachmentDownloader.calculate_file_hash(temp_filename)
            # 关闭连接
            conn.close()
            # 比较哈希值
            if existing_file_hash == downloaded_file_hash:
                print(f"File '{filename}' is identical to the downloaded file. Skipping download.")
                os.remove(temp_filename)
                return True, filename
            else:
                # 重命名临时文件为目标文件
                os.rename(temp_filename, new_filename)
                print(f"File downloaded successfully and saved as '{filename}'")
                return True, new_filename
        else:
            print(f"Failed to download file. HTTP status code: {response.status}, reason: {response.reason}")
            return False, None

    def handle_redirect(self, source_url, headers=None):
        """
        使用 http.client 处理 URL 重定向，返回最终的重定向 URL
        :param source_url: 源 URL
        :param headers: 请求头字典
        :return: 最终重定向的 URL
        """
        # 默认请求头
        if headers is None:
            headers = {}

        # 解析初始 URL
        parsed_url = urllib.parse.urlparse(source_url)
        conn = None

        try:
            # 建立连接
            if parsed_url.scheme == 'https':
                conn = http.client.HTTPSConnection(parsed_url.netloc)
            else:
                conn = http.client.HTTPConnection(parsed_url.netloc)

            # 构造路径，考虑到URL中可能包含查询参数
            path = parsed_url.path
            if parsed_url.query:
                path += '?' + parsed_url.query

            # 发送请求
            conn.request("GET", path, headers=headers)

            # 获取响应
            response = conn.getresponse()

            # 如果响应状态码是 3xx 表示有重定向
            if 300 <= response.status < 400:
                # 获取重定向的 URL
                redirect_url = response.getheader('Location')
                if not redirect_url:
                    raise Exception("重定向但未找到 Location 头")

                # 解析可能的相对重定向 URL
                redirect_url = urllib.parse.urljoin(source_url, redirect_url)

                # 打印重定向信息
                print(f"Redirected to: {redirect_url}")

                # 递归调用处理新的重定向 URL
                return self.handle_redirect(redirect_url, headers)
            else:
                # 如果没有重定向，返回当前 URL
                return source_url

        except Exception as e:
            print(f"An error occurred: {e}")
            return None

        finally:
            if conn:
                conn.close()


class NeteaseDownloader:
    def __init__(self, outside_link):
        self.outside_link = outside_link

    def get_downloadUrl(self):
        url = self.outside_link
        parsed_url = urllib.parse.urlparse(url)
        # 提取查询参数
        query_params = urllib.parse.parse_qs(parsed_url.query)
        # 获取file参数的值
        file_value = query_params.get('file', [None])[0]
        # print(file_value)
        url = 'https://mail.163.com/filehub/bg/dl/prepare'
        # 解析URL
        parsed_url = urllib.parse.urlparse(url)

        # 提取主机名和路径
        host = parsed_url.netloc
        path = parsed_url.path

        # 请求载荷
        payload = {
            "linkKey": f"{file_value}"
        }
        json_payload = json.dumps(payload)

        # 请求头
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }

        # 创建HTTPS连接
        conn = http.client.HTTPSConnection(host)

        # 发送POST请求
        conn.request("POST", path, body=json_payload, headers=headers)
        # 获取响应
        response = conn.getresponse()
        data = response.read()
        # 打印响应状态和数据
        # print("Status:", response.status)
        # print("Reason:", response.reason)
        # print("Response data:", data.decode('utf-8'))
        result = data.decode()
        result = json.loads(result)
        download_url = result['data']['downloadUrl']
        # 关闭连接
        conn.close()
        return download_url

    def get_headers(self):
        return {}


class QQDownloader:
    def __init__(self, outside_link):
        self.cookie = None
        self.outside_link = outside_link

    def get_downloadUrl(self):
        url = self.outside_link
        parsed_url = urllib.parse.urlparse(url)
        # 提取主机名和请求路径
        host = parsed_url.netloc
        path = f"{parsed_url.path}?{parsed_url.query}"

        # 创建HTTPS连接
        conn = http.client.HTTPSConnection(host)

        # 发送GET请求
        conn.request("GET", path)
        # 获取响应
        response = conn.getresponse()
        redirect = response.getheader('Location')
        # print(redirect)
        conn.close()

        parsed_url = urllib.parse.urlparse(redirect)
        host = parsed_url.netloc
        path = f"{parsed_url.path}?{parsed_url.query}"

        conn = http.client.HTTPSConnection(host)
        conn.request('GET', path)
        response = conn.getresponse()
        # print(response.status)
        data = response.read()
        # print(data.decode())
        html_page = data.decode()

        pattern = r'var url = "(https://[^\"]+)"'
        match = re.search(pattern, html_page)
        if match:
            file_url = match.group(1)
            # print("Extracted URL:", file_url)
        self.cookie = response.getheader('Set-Cookie')
        print(f'旧cookie={self.cookie}')

        conn.close()
        file_url = file_url.replace("\\x26", "&")
        file_url, cookies = RedirectHandler().handle_redirect(file_url, None)
        print(f'新cookie={cookies}')
        self.cookie = cookies_str = '; '.join([f'{key}={value}' for key, value in cookies.items()])

        return file_url

    def get_headers(self, new_cookie=None):
        if new_cookie is None:
            cookie = self.cookie
        else:
            cookie = new_cookie
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            # 'Cookie': 'mail5k=6c9e1d58',
            'Cookie': f'{cookie}'
        }
        return headers


class GmailDownloader:
    def __init__(self, outside_link):
        self.outside_link = outside_link
        self.fileinfo = self.get_fileinfo()

    def get_fileinfo(self):
        # print(self.outside_link)
        # url = self.outside_link
        return 1

    def get_headers(self):
        return {}

    def get_downloadUrl(self):
        """
        解析器中处理所有的重定向
        :return:
        """
        url = self.outside_link
        downloader = CloudAttachmentDownloader(url)
        download_url = downloader.handle_redirect(url)
        url = download_url
        parsed_url = urllib.parse.urlparse(url)
        # 提取主机名和请求路径
        host = parsed_url.netloc
        path = f"{parsed_url.path}?{parsed_url.query}"

        # 创建HTTPS连接
        conn = http.client.HTTPSConnection(host)
        # 发送GET请求
        conn.request("GET", path)

        html = conn.getresponse().read()
        download_url = self.extract_download_link(html)
        print(f'下载链接初始:{download_url}')
        t = downloader.handle_redirect(download_url)
        return t

    @staticmethod
    def extract_download_link(html_content):
        # 确保输入为字符串
        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8')

        # 调整模式，支持转义符
        pattern = r"https://drive\.usercontent\.google\.com/uc\?id\\u003d([-\w]+)\\u0026export\\u003ddownload"

        # 查找所有符合条件的链接
        matches = re.findall(pattern, html_content)

        # 返回第一个匹配项的格式化链接
        if matches:
            file_id = matches[0]
            return f"https://drive.usercontent.google.com/uc?id={file_id}&export=download"

        return None



class OutlookDownloader:
    def __init__(self, outside_link):
        self.outside_link = outside_link

    def get_token(self):
        payload = {
            "appId": "5cbed6ac-a083-4e14-b191-b4ba07653de2"
        }
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "Appid": "1141147648",
            "Cache-Control": "private",
            "Referer": "https://onedrive.live.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Forcecache": "1"
        }

        # 创建连接
        conn = http.client.HTTPSConnection("api-badgerp.svc.ms")
        # 发送请求
        conn.request("POST", "/v1.0/token", json.dumps(payload), headers)

        # 获取响应
        response = conn.getresponse()
        data = response.read()

        result = data.decode()
        k = json.loads(result)
        # print(f'token=={k["token"]}')
        # 关闭连接
        conn.close()
        return k["token"]

    def driveitem(self, token):

        # 定义主机和路径
        host = 'my.microsoftpersonalcontent.com'
        path = ('/_api/v2.0/shares/u!aHR0cHM6Ly8xZHJ2Lm1zL2IvYy9iNGQ0'
                'ODI4MTAxMDY3ZDhhL0VZcDlCZ0dCZ3RRZ2dMUkFBUUF'
                'BQUFBQlQtYmpXRFRFLVdVbVVmQ25UVV96OFE/driveitem?%24select=id%2CparentReference')

        # 创建HTTPS连接
        conn = http.client.HTTPSConnection(host)

        # 定义请求头
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-cn',
            'Authorization': f'Badger {token}',
            'Cache-Control': 'no-cache',
            'Content-Length': '0',
            'Content-Type': 'text/plain;charset=UTF-8',
            'Origin': 'https://onedrive.live.com',
            'Pragma': 'no-cache',
            'Prefer': 'autoredeem',
            'Referer': 'https://onedrive.live.com/',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # 定义请求体为空
        body = ''

        # 发送POST请求
        conn.request('POST', path, body=body, headers=headers)

        # 获取响应
        response = conn.getresponse()
        data = response.read()

        # 检查并处理压缩的响应数据
        encoding = response.getheader('Content-Encoding')

        if encoding == 'gzip':
            data = zlib.decompress(data, zlib.MAX_WBITS | 16)
        elif encoding == 'deflate':
            data = zlib.decompress(data)

        # 打印响应状态和数据
        print(response.status, response.reason)
        print(data.decode('utf-8'))

        host = 'my.microsoftpersonalcontent.com'
        path = ('/_api/v2.0/drives/b4d4828101067d8a/items/B4D4828101067D8A!320?'
                '%24select=*%2CsharepointIds%2CwebDavUrl%2CcontainingDrivePolicyScenarioViewpoint&'
                '%24expand=thumbnails&ump=1')
        body = ''

        # 发送POST请求
        conn.request('POST', path, body=body, headers=headers)

        # 获取响应
        response = conn.getresponse()
        data = response.read()

        # 检查并处理压缩的响应数据
        encoding = response.getheader('Content-Encoding')

        if encoding == 'gzip':
            data = zlib.decompress(data, zlib.MAX_WBITS | 16)
        elif encoding == 'deflate':
            data = zlib.decompress(data)

        # 打印响应状态和数据
        print(response.status, response.reason)
        print(data.decode('utf-8'))

        conn.close()

    def get_headers(self):
        return {}


class Cloud189Downloader:
    def __init__(self, outside_link):
        self.outside_link = outside_link

    def get_downloadUrl(self):
        url = self.outside_link

        parsed_url = urllib.parse.urlparse(url)
        # 提取主机名和请求路径
        host = parsed_url.netloc
        path = f"{parsed_url.path}?{parsed_url.query}"

        conn = http.client.HTTPSConnection(host)
        conn.request('GET', path)
        response = conn.getresponse()
        # print(f'{response.status} {response.reason}')

        redirect_url = response.getheader('Location')

        response.close()

        # parsed_url = urllib.parse.urlparse(redirect_url)
        # # 提取主机名和请求路径
        # host = parsed_url.netloc
        # path = f"{parsed_url.path}?{parsed_url.query}"
        # conn = http.client.HTTPSConnection(host)
        # conn.request('GET', path)
        # response = conn.getresponse()
        # # print(f'{response.status} {response.reason}')
        # conn.close()

        return redirect_url

    def get_headers(self):
        return {}


class RUCDownloader:
    def __init__(self, outside_link):
        self.outside_link = outside_link

    def get_downloadUrl(self):
        url = self.outside_link
        parsed_url = urllib.parse.urlparse(url)
        # 提取主机名和请求路径
        host = parsed_url.netloc
        path = f"{parsed_url.path}?{parsed_url.query}"

        conn = http.client.HTTPSConnection(host)
        conn.request('GET', path)
        response = conn.getresponse()
        # print(f'{response.status} {response.reason}')

        redirect_url = response.getheader('Location')

        response.close()
        return redirect_url

    def get_headers(self):
        return {}


class SinaDownloader:
    def __init__(self, outside_link):
        self.outside_link = outside_link

    def get_downloadUrl(self):
        url = self.outside_link
        parsed_url = urllib.parse.urlparse(url)
        # 提取主机名和请求路径
        host = parsed_url.netloc
        path = f"{parsed_url.path}?{parsed_url.query}"

        conn = http.client.HTTPSConnection(host)
        conn.request('POST', path)
        response = conn.getresponse()
        redirect_url = response.getheader('Location')

        return redirect_url

    def get_headers(self):
        return {}


# if __name__ == "__main__":
#     provider = "RUC"
#     parser = CloudFileParser.create_parser(provider)
#
#     # 示例 HTML 内容
#     html_content = """
#     <div style="line-height:1.7;color:#000000;
#     font-size:14px;font-family:Arial"><p><br></p></div>
#     <div id="divNeteaseSiriusCloudAttach" style="clear: both;
#     margin-top: 1px; margin-bottom: 1px;font-family: verdana,
#     Arial,Helvetica,sans-serif;border: 1px solid rgba(238, 238, 239, 1);
#     box-shadow: 0px 5px 15px rgba(203, 205, 210, 0.3);border-radius: 6px;color:
#      #262A33;"><div style="font-size: 13px; padding: 12px 0px 12px 0px;
#       line-height: 16px;border-bottom: 1px solid #ECECED;"><b style="padding-left: 12px;">
#       从网易企业邮箱发来的云附件</b></div><div style="padding:
#       0px 12px;position: relative;width: 392px;background: rgba(38, 42, 51, 0.02);
#       border: 0.5px solid rgba(38, 42, 51, 0.12);border-radius:
#       4px;display: inline-block;margin: 12px;"><div style="width: 2
#       4px;float:left;height: 40px;left:16px;top:4px;margin-top:16px;"><a href="
#       https://edisk.qiye.163.com/api/biz/attachment/download?identity=
#       e7bb4414a8c248bcaeb376a72e0595b8&title=%E4%BC%81%E4%B8%9A%E9%82%AE%E7%AE
#       %B1%E4%BA%91%E9%99%84%E4%BB%B6%E6%B5%8B%E8%AF%95" style="text-underline:
#        none;"><img width="24px" height="24px" src="https://mimg.127.net/xm/all
#        /fj/ico-bfile-3.gif" border="0" title="云附件"></a></div><div style="padd
#        ing-right: 16px;margin-left: 30px;margin-top: 16px;padding-bottom: 16px;">
#        <div style="margin-left: 4px;overflow: hidden;"><div style="padding: 1px;
#        font-size: 14px; line-height: 14px;word-break: break-all;"><a style=" text
#        -decoration: none;color: #262A33;display: block" href="https://edisk.qiye.1
#        63.com/api/biz/attachment/download?identity=e7bb4414a8c248bcaeb376a72e0595b8&
#        title=%E4%BC%81%E4%B8%9A%E9%82%AE%E7%AE%B1%E4%BA%91%E9%99%84%E4%BB%B6%E6%B
#        5%8B%E8%AF%95" target="_blank" rel="noopener" download="https://edisk.qiye.163
#        .com/api/biz/attachment/download?identity=e7bb4414a8c248bcaeb376a72e0595b8&tit
#        le=%E4%BC%81%E4%B8%9A%E9%82%AE%E7%AE%B1%E4%BA%91%E9%99%84%E4%BB%B6%E6%B5%8B%E8%AF
#        %95">现有工具对比.docx</a></div><div><div style="float: left;padding: 1px;col
#        or: #262A33;opacity: 0.4;font-size: 12px;margin-top: 4px;">20.49K&nbsp;|&nbsp;过期时
#        间：2024年8月4日 23:48</div><div style="line-height: 23px;text-align: right;"><a href
#        ="https://edisk.qiye.163.com/api/biz/attachment/download?identity=e7bb4414a8c248
#        bcaeb376a72e0595b8&title=%E4%BC%81%E4%B8%9A%E9%82%AE%E7%AE%B1%E4%BA%91%E9%99%84%E4%BB
#        %B6%E6%B5%8B%E8%AF%95"style="display:inline-block;text-decoration: none;font-size:
#        12px; line-height: 12px;color:#386EE7;    border-right: solid 1px #ccc;padding-righ
#        t: 12px;"><img src="https://cowork-storage-public-cdn.lx.netease.com/common/2022/10/26
#        /5f754abd17944c758451bfc87efd1db4.png" width="16px" height="16px" border="0" title="
#        下载(download)"/></a><a class="divNeteaseSiriusCloudAttachItemPreview"
#        href="https://mailh.qiye.163.com/edisk/api/biz/attachment/generic/preview?&id
#        entity=e7bb4414a8c248bcaeb376a72e0595b8" style="display:inline-block;padding-left
#        : 12px;text-decoration: none;font-size: 12px; line-height: 12px;color:#386EE7;
#        "><img width="16px" height="16px" src="https://cowork-storage-public-cdn.lx.net
#        ease.com/common/2022/10/26/561b03b1f15d4dd8b75598771e3d45f9.png" border="0" title="预
#        览(preview)"</a></div></div></div></div><a class="divNeteaseSiriusCloudAttachItem" tar
#        get="_blank" href="https://edisk.qiye.163.com/api/biz/attachment/download?identity=e7bb4414a8c248bcaeb376a72e0595b8&title=%E4%BC%81%E4%B8%9A%E9%82%AE%E7%AE%B1%E4%BA%91%E9%99%84%E4%BB%B6%E6%B5%8B%E8%AF%95" download="https://edisk.qiye.163.com/api/biz/attachment/download?identity=e7bb4414a8c248bcaeb376a72e0595b8&title=%E4%BC%81%E4%B8%9A%E9%82%AE%E7%AE%B1%E4%BA%91%E9%99%84%E4%BB%B6%E6%B5%8B%E8%AF%95" file-id="e7bb4414a8c248bcaeb376a72e0595b8" file-name="现有工具对比.docx" file-size="20977" file-previewUrl="https://mailh.qiye.163.com/edisk/api/biz/attachment/generic/preview?&identity=e7bb4414a8c248bcaeb376a72e0595b8" expired="1722786486117" style=" text-decoration: none;display: none; font-size: 12px; line-height: 12px;float:right;margin-top: -30px;color:#386EE7">下载</a></div></div><br>
#
#     """
#
#     file_info_list = parser.get_cloud_file_info(html_content)
#
#     for file_info in file_info_list:
#         # print("Filename:", file_info.get("filename"))
#         # print("File Status:", file_info.get("file_status"))
#         # print("File Size:", file_info.get("file_size"))
#         # print("Expiry Date:", file_info.get("expire_time"))
#         # print("Expired:", file_info.get("expired"))
#         # print("Direct Download Link:", file_info.get("outside_link"))
#         # print("-" * 40)
#         print(file_info)


class RedirectHandler:
    @staticmethod
    def handle_redirect(source_url, headers=None, cookies=None):
        """
        使用 http.client 处理 URL 重定向，返回最终的重定向 URL 和 cookies
        :param source_url: 源 URL
        :param headers: 请求头字典
        :param cookies: 之前的cookie字典，跟踪多个请求间的cookies
        :return: 最终的重定向 URL 和所有 cookie
        """
        if headers is None:
            headers = {}

        if cookies is None:
            cookies = {}

        # 将 cookie 转换为请求头中的格式
        if cookies:
            cookie_header = '; '.join([f'{key}={value}' for key, value in cookies.items()])
            headers['Cookie'] = cookie_header

        # 解析初始 URL
        parsed_url = urllib.parse.urlparse(source_url)
        conn = None

        try:
            # 建立连接
            if parsed_url.scheme == 'https':
                conn = http.client.HTTPSConnection(parsed_url.netloc)
            else:
                conn = http.client.HTTPConnection(parsed_url.netloc)

            # 构造路径，考虑到URL中可能包含查询参数
            path = parsed_url.path
            if parsed_url.query:
                path += '?' + parsed_url.query

            # 发送请求
            conn.request("GET", path, headers=headers)

            # 获取响应
            response = conn.getresponse()

            # 处理响应的 Set-Cookie 头
            set_cookie_headers = response.getheader('Set-Cookie')
            if set_cookie_headers:
                # 解析 Set-Cookie 头中的 cookies
                for cookie in set_cookie_headers.split(','):
                    parts = cookie.split(';')[0].split('=')
                    if len(parts) == 2:
                        key, value = parts
                        cookies[key.strip()] = value.strip()

            # 如果响应状态码是 3xx 表示有重定向
            if 300 <= response.status < 400:
                # 获取重定向的 URL
                redirect_url = response.getheader('Location')
                if not redirect_url:
                    raise Exception("重定向但未找到 Location 头")

                # 解析可能的相对重定向 URL
                redirect_url = urllib.parse.urljoin(source_url, redirect_url)

                # 递归调用处理新的重定向 URL，并传递 cookies
                return RedirectHandler.handle_redirect(redirect_url, headers, cookies)
            else:
                # 如果没有重定向，返回最终的 URL 和 cookies
                return source_url, cookies

        except Exception as e:
            print(f"An error occurred: {e}")
            return None, cookies

        finally:
            if conn:
                conn.close()
