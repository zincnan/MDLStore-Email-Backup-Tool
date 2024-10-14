import os
import re
import subprocess
import tempfile
import traceback
from pathlib import Path
import mammoth

from PyQt5.QtCore import QVariant, Qt, QItemSelectionModel, QUrl, QTimer, QSize
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QColor, QPixmap, QPainter, QFont
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage
from PyQt5.QtWidgets import QWidget, QApplication, QListWidget, QListWidgetItem, QTextEdit, QLabel, QDialog, \
    QVBoxLayout, QFileDialog, QPushButton, QHBoxLayout, QMessageBox, QSizePolicy, QLineEdit

from MDLStore.UI.SearchPages import EmailSearchCriteria, AttachmentSearchCriteria
from MDLStore.UI.THEMES import LISTVIEW_EMAILS, LISTWIDGET_ATTACH
from MDLStore.UI.Ui_EmailReader import Ui_EmailReader
from MDLStore.UI.Ui_ResultPage import Ui_ResultPage
from MDLStore.search import MailSearcher
from MDLStore.storage import PathDirUtil
from MDLStore.ui_utils import UiUtils, APP_Signals, EmailParser, replace_cid_with_base64


class FileObject:
    def __init__(self, filename, filetype, filepath=''):
        self.filename = filename
        self.filetype = filetype
        self.filepath = filepath  # 文件路径


class ResultPage(QWidget, Ui_ResultPage):
    def __init__(self, parent=None, *args, **kwargs):
        super(ResultPage, self).__init__(parent, *args, **kwargs)
        self.search_body_text = None
        self.search_filename = None
        self.tar_drive = None
        self.search_content_keyword = None
        self.objects = None
        self.cur_email = None
        self.email_reader = None
        self.model = None
        self.setupUi(self)

        self.init_ui()
        self.set_layout()
        self.set_theme()

    def init_ui(self):
        utils = UiUtils()
        self.email_reader = EmailReader()
        utils.replace_or_insert_widget(self.widget_eml, self.email_reader)

        self.init_listView()

    def set_layout(self):
        layout = self.groupBox.layout()
        utils = UiUtils()
        utils.set_stretch_by_widget(layout, self.listView_emails, 1)
        utils.set_stretch_by_widget(layout, self.email_reader, 6)

        list_size = self.listView_emails.size()
        # print(f'控件的寬度和高度分別是:{list_size.width()}{list_size.height()}')
        # self.listView_emails.setFixedSize(list_size.width(), list_size.height())

    def set_theme(self):
        self.listView_emails.setStyleSheet(LISTVIEW_EMAILS)
        self.listView_emails.setFocusPolicy(Qt.NoFocus)

    def init_listView(self):
        # self.objects = [
        #     MyObject("Item1", 10),
        #     MyObject("Item2", 20),
        #     MyObject("Item3", 30)
        # ]
        # 创建 QStandardItemModel
        self.model = QStandardItemModel()
        #
        # # 将对象添加到模型中
        # for obj in self.objects:
        #     item = QStandardItem(str(obj))  # 显示的文本
        #     item.setData(QVariant(obj), Qt.UserRole)  # 存储对象
        #     self.model.appendRow(item)
        #
        # # 将模型设置到 QListView 中
        # self.listView_emails.setModel(self.model)
        # self.refresh_list()
        self.listView_emails.clicked.connect(self.on_item_clicked)

    def refresh_list(self, objects):
        self.objects = objects
        nums = len(objects)
        self.label.setText(f'共搜索到邮件{nums}封')
        # 清空现有模型
        self.model.clear()
        # 将对象添加到模型中
        for obj in self.objects:
            # print(f'搜索结果{type(obj)}')
            #     if hasattr(item, 'files'):
            #         print(item.files)
            #     else:
            #         print(f'==={item.attachments}')
            subject = obj.subject
            from_address = obj.from_address
            received_date = obj.received_date
            item = QStandardItem(f'{subject}\n来自:<{from_address}>\n日期:{received_date}')  # 显示的文本
            item.setData(QVariant(obj), Qt.UserRole)  # 存储对象
            self.model.appendRow(item)
        self.listView_emails.setModel(self.model)

        if self.model.rowCount() > 0:
            # 默认选中第一项
            index = self.model.index(0, 0)
            self.listView_emails.setCurrentIndex(index)
            # self.on_item_clicked(index)
            QTimer.singleShot(1000, lambda: self.on_item_clicked(index))
        # if self.model.rowCount() > 0:
        #     # 获取第一项的索引
        #     index = self.model.index(0, 0)
        #     self.listView_emails.setCurrentIndex(index)
        #     # 手动触发 clicked 信号
        #     # 使用 QTimer 来确保在事件循环完成后触发
        #     QTimer.singleShot(1000, lambda: self.listView_emails.clicked.emit(index))

    def on_item_clicked(self, index):
        # 获取被点击的项
        item = self.model.itemFromIndex(index)
        # 从 UserRole 中取出对象
        obj = item.data(Qt.UserRole)
        # print(f"Selected: {obj.name} - {obj.value}")
        self.cur_email = obj
        # 显示邮件内容
        APP_Signals.read_email_ready.emit(self.cur_email)

    def update_objects(self, new_objects):
        # 更新对象列表
        self.objects = new_objects
        # 刷新 QListView
        self.refresh_list()

    def set_target(self, drive):
        self.tar_drive = drive
        # print(f'Result获取了磁盘{self.tar_drive}')
        self.email_reader.set_target_drive(drive)

    def set_search_keywords(self, body_text, filename, content_):
        self.search_body_text = body_text
        self.search_filename = filename
        self.search_content_keyword = content_
        self.email_reader.set_search_keywords(body_text, filename, content_)


class EmailReader(QWidget, Ui_EmailReader):
    def __init__(self, parent=None, *args, **kwargs):
        super(EmailReader, self).__init__(parent, *args, **kwargs)
        # self.tar_drive = None
        self.search_content_keyword = None
        self.tar_drive = None
        self.search_filename = None
        self.attachments_fulltext_searched = None
        self.html_view = None
        self.search_body_text = None
        self.cur_eml_path = None
        self.setupUi(self)

        self.init_ui()
        self.set_layout()
        self.init_theme()

    def set_layout(self):
        layout = self.frame_all.layout()
        utils = UiUtils()
        utils.set_stretch_by_widget(layout, self.label_subject, 1)
        utils.set_stretch_by_widget(layout, self.label_headers, 0)
        utils.set_stretch_by_widget(layout, self.listWidget_attach, 0)
        utils.set_stretch_by_widget(layout, self.frame_placeholder, 8)

    def init_theme(self):
        self.label_headers.setObjectName("label_headers_email")
        self.label_headers.setStyleSheet("""
            QLabel#label_headers_email {
                font-size: 16px; /* 设置字体大小为 16px */
                text-align: left; /* 左对齐 */
                qproperty-alignment: 'AlignLeft | AlignVCenter'; /* 水平左对齐，垂直居中 */
            }
        """)
        self.frame_headers.setStyleSheet("""
            QFrame#frame_headers { background-color: #f1f6f5; }
        """)
        self.label_subject.setWordWrap(True)
        self.label_subject.setObjectName("label_subject_email")
        self.label_subject.setStyleSheet("""
                    QLabel#label_subject_email {
                        font-size: 30px; /* 设置字体大小为 16px */
                        text-align: left; /* 左对齐 */
                        qproperty-alignment: 'AlignLeft | AlignVCenter'; /* 水平左对齐，垂直居中 */
                    }
                """)
        self.listWidget_attach.setStyleSheet(LISTWIDGET_ATTACH)
        self.listWidget_attach.setFocusPolicy(Qt.NoFocus)

        self.frame_placeholder.setStyleSheet("""
            QFrame#frame_placeholder { background-color: #f1f6f5; }
        """)

    def init_ui(self):
        APP_Signals.read_email_ready.connect(self.read_email)
        self.listWidget_attach.itemDoubleClicked.connect(self.open_or_preview_file)
        self.html_view = QWebEngineView()
        layout = QVBoxLayout(self.frame_placeholder)
        # 将 QWebEngineView 添加到布局中
        layout.addWidget(self.html_view)
        # 将布局设置到 QFrame 中
        self.frame_placeholder.setLayout(layout)

        self.listWidget_attach.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.label_headers.setWordWrap(True)
        self.label_headers.setTextFormat(Qt.RichText)

    def read_email(self, email):
        # print(f'打印邮件{email.name,email.value},类型是{type(email)}')
        # print(f'读取邮件数据:{email}')
        try:
            if hasattr(email, 'files'):
                self.attachments_fulltext_searched = email.files
            else:
                self.attachments_fulltext_searched = []

            subject = email.subject
            # 设置主题
            self.set_subject(subject)
            belong_to = email.email_address
            sender = email.from_address
            send_to = email.to_addresses
            cc_address = email.cc_addresses
            bcc_address = email.bcc_addresses
            email_date = email.received_date
            eml_path = email.eml_path
            body_text = email.body_text
            task_name = email.task_name

            # print(f'测试目标磁盘{self.tar_drive}')
            if eml_path is None or eml_path == '' or eml_path == 'None':
                source_path = None
                info_path = f'原件未备份'
            else:
                path_convert = PathDirUtil()
                # print(f'目标磁盘{self.tar_drive}')
                source_path = path_convert.relative_to_absolute(self.tar_drive, eml_path)
                info_path = f'原件存储路径:{source_path}'
            self.cur_eml_path = source_path

            # 构建HTML表格
            header_info = f"<table border='0' cellpadding='3' cellspacing='5'>"
            header_info += f"<tr><td>所属邮箱账户:</td><td>{belong_to}</td></tr>"
            header_info += f"<tr><td>备份任务名称:</td><td>{task_name}</td></tr>"

            if sender and sender != 'None':
                header_info += f"<tr><td>发件人[From]:</td><td>{sender}</td></tr>"
            if send_to and send_to != 'None':
                header_info += f"<tr><td>收件人[To]:</td><td>{send_to}</td></tr>"
            if email_date and email_date != 'None':
                header_info += f"<tr><td>日期[Date]:</td><td>{email_date}</td></tr>"
            if cc_address and cc_address != 'None':
                header_info += f"<tr><td>抄送人[Cc]:</td><td>{cc_address}</td></tr>"
            if bcc_address and bcc_address != 'None':
                header_info += f"<tr><td>密送人[Bcc]:</td><td>{bcc_address}</td></tr>"

            header_info += "</table>"

            self.set_headers(header_info)

            email_criteria = EmailSearchCriteria(
                email_id=email.email_id
            )
            attachment_criteria = AttachmentSearchCriteria(

            )

            searcher = MailSearcher(self.tar_drive)
            email_searched = searcher.search_emails_and_attachments(email_criteria, attachment_criteria)
            self.set_attachments(email_searched[0].attachments)
            if self.attachments_fulltext_searched is not None and len(self.attachments_fulltext_searched) > 0:
                # print(f'指定全文检索的文件')
                self.set_attachment_founded(self.attachments_fulltext_searched)

        except Exception as e:
            print(f'ERR{e}')
            traceback.print_exc()

        self.set_body(body_text)

        # self.set_subject(email.name)
        # self.set_headers(email.value)
        # self.set_attachments()

    def set_subject(self, subject):
        self.label_subject.setText(str(subject))

    def set_headers(self, headers):
        self.label_headers.setText(str(headers))

    def set_attachments(self, attachments):
        # print(f'附件数据{attachments}')
        # 获取附件和云附件
        # files = [
        #     FileObject("document1.pdf", "pdf", "E:/Xsoftware/Python/workstation/MDLStore_UI/emls/test.pdf"),
        #     FileObject("image1.png", "image", "E:/Xsoftware/Python/workstation/MDLStore_UI/emls/小刘鸭.png"),
        #     FileObject("presentation.docx", "docx", "C:/Users/Lenovo/Desktop/现有工具对比.docx"),
        #     FileObject("spreadsheet.xlsx", "excel", "/path/to/spreadsheet.xlsx"),
        #     FileObject("archive.zip", "zip", "/path/to/archive.zip")
        # ]

        files = attachments

        self.listWidget_attach.clear()
        self.listWidget_attach.setViewMode(QListWidget.IconMode)  # 设置为图标模式
        self.listWidget_attach.setResizeMode(QListWidget.Adjust)  # 自动调整项目的大小
        self.listWidget_attach.setSpacing(0)  # 设置项目间的间距
        self.listWidget_attach.setIconSize(QSize(180, 50))  # 设置子项宽度为 180px
        self.listWidget_attach.setWrapping(True)  # 启用自动换行

        for i, file in enumerate(files):
            # 根据文件类型设置图标
            filename = file.filename
            _, file_extension = os.path.splitext(filename)  # 提取文件扩展名

            # 将扩展名转换为小写以避免大小写问题
            file_extension = file_extension.lower()
            if file_extension == ".pdf":
                icon = QIcon("path/to/pdf_icon.png")
            elif file_extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
                icon = QIcon("path/to/image_icon.png")
            elif file_extension == ".ppt" or file_extension == ".pptx":
                icon = QIcon("path/to/ppt_icon.png")
            elif file_extension == ".xls" or file_extension == ".xlsx":
                icon = QIcon("path/to/excel_icon.png")
            elif file_extension == ".zip" or file_extension == ".rar":
                icon = QIcon("path/to/zip_icon.png")
            else:
                icon = QIcon("path/to/default_icon.png")  # 默认图标

            # 创建 QListWidgetItem，并设置图标和文本
            item = QListWidgetItem(icon, filename)

            # 将对象数据存储到 UserRole 中
            item.setData(Qt.UserRole, file)
            item.setToolTip(f'{filename}')

            # 设置背景色，每个项目不同颜色
            if i % 2 == 0:
                item.setBackground(QColor("#DFF0D8"))  # 绿色背景
            else:
                item.setBackground(QColor("#F2DEDE"))  # 红色背景

            # 添加项到 QListWidget
            self.listWidget_attach.addItem(item)

        # print('调整附件表大小')
        self.adjust_list_widget_size(self.listWidget_attach)

    def set_attachment_founded(self, files_list):
        files_to_highlight = {item['filename'] for item in files_list}
        # 遍历 QListWidget 中的所有项目
        for index in range(self.listWidget_attach.count()):
            item = self.listWidget_attach.item(index)
            filename = item.text()
            # 如果文件名在 files_to_highlight 集合中，则设置背景色为红色
            if filename in files_to_highlight:
                # print('找到')
                item.setForeground(QColor("red"))  # 设置文本颜色为红色
                # item.setFont(QFont("Arial", 12, QFont.Bold))  # 设置为加粗字体
                item.setToolTip("内含全文检索关键字")  # 添加提示信息

    # def set_body(self):
    #     if self.search_body_text is None:
    #         eml_path = self.cur_eml_path
    #         with open(eml_path, 'rb') as file:
    #             raw_email = file.read()
    #         email_parser = EmailParser(raw_email)
    #         body = email_parser.get_body()
    #         body = ''.join(body)
    #         html = f'<html>{body}</html>'
    #         # print(html)
    #         images_info = email_parser.extract_images()
    #         html = replace_cid_with_base64(html, images_info)
    #         self.html_view.setHtml(html)
    def set_body(self, body_text):
        if self.cur_eml_path:
            eml_path = self.cur_eml_path
            with open(eml_path, 'rb') as file:
                raw_email = file.read()
            email_parser = EmailParser(raw_email)
            body = email_parser.get_body()
            body = ''.join(body)

            # 如果 search_body_text 不是 None，则高亮显示对应文本
            if self.search_body_text is not None:
                # 使用正则表达式来匹配所有的关键字
                pattern = re.escape(self.search_body_text)
                highlight_start = '<span style="background-color: yellow;">'
                highlight_end = '</span>'

                # 通过正则表达式替换，忽略大小写，替换所有出现的关键字
                body = re.sub(pattern, f'{highlight_start}\\g<0>{highlight_end}', body, flags=re.IGNORECASE)

            html = f'<html>{body}</html>'
            images_info = email_parser.extract_images()
            html = replace_cid_with_base64(html, images_info)
            self.html_view.setHtml(html)
        else:
            html = f'<html>{body_text}</html>'
            self.html_view.setHtml(html)

    def on_item_clicked(self, item):
        # 从 UserRole 中获取对象数据
        file_obj = item.data(Qt.UserRole)
        # print(f"Selected file: {file_obj.filename}, Type: {file_obj.filetype}")
        # print(f'选中了附件：{file_obj}')

    def open_or_preview_file(self, item):
        file_obj = item.data(Qt.UserRole)
        # print(f"Selected file: {file_obj.filename}, Type: {file_obj.filetype}")
        # print(f'预览文件数据{file_obj}')
        file_path = file_obj.file_path
        # if file_obj.attachment_type == 'CloudAttach' and file_obj.file_path is None or file_obj.file_path == 'None':
        if file_obj.attachment_type == 'CloudAttach' and (file_obj.file_path is None or file_obj.file_path == 'None'):
            print('该云附件已过期，未备份，无法查看！')
            # QMessageBox.warning(None, "警告", "该云附件已过期，未备份，无法查看！", QMessageBox.Ok)
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)  # 设置为警告图标（叹号）
            msg_box.setWindowTitle("警告")
            msg_box.setText("该云附件已过期，未备份，无法查看！")
            # 创建自定义按钮
            custom_button = QPushButton("确定")  # 自定义按钮文字为“确定”
            msg_box.addButton(custom_button, QMessageBox.AcceptRole)  # 将按钮添加到提示框中
            msg_box.exec_()
            return
        if file_path == 'None':
            abstract_file_path = None
            # 解析并预览，预览页面提供一下另存到本地的按钮
            self.show_file_preview_save(file_obj)
        else:
            abstract_file_path = PathDirUtil().relative_to_absolute(self.tar_drive, file_path)
            # 这里文件已经下载了，双击预览，同时提供一个打开文件位置按钮
            self.show_file_preview_open(file_obj, abstract_file_path)

    def show_file_preview_save(self, file_obj):
        """
        预览文件，预览页提供另存为按钮，用来将文件保存到本地
        :param file_obj: <Attachment(attachment_id=6, email_id=26, filename='logo.png',
        attachment_type='Attach', file_path='None')>
        :return:
        """
        print(f'预览并下载附件 {file_obj}')
        filename = file_obj.filename
        eml_path = self.cur_eml_path
        with open(eml_path, 'rb') as file:
            raw_email = file.read()
        email_parser = EmailParser(raw_email)
        file_content = email_parser.get_attachment_by_filename(filename)  # 完整的文件内容

        dialog = QDialog(self)
        dialog.setWindowTitle(f"预览: {filename}")
        dialog.setFixedSize(1024, 750)
        layout = QVBoxLayout(dialog)

        # 添加搜索框和查找按钮布局
        search_layout = QHBoxLayout()
        search_box = QLineEdit(dialog)
        search_box.setPlaceholderText("输入关键词查找")
        next_button = QPushButton("下一个", dialog)
        prev_button = QPushButton("上一个", dialog)
        search_layout.addWidget(search_box)
        search_layout.addWidget(prev_button)
        search_layout.addWidget(next_button)
        layout.addLayout(search_layout)

        # 使用 QWebEngineView 预览内容
        web_view = QWebEngineView(dialog)

        temp_file_path = None
        html_temp_file_path = None

        # 假设内容是 PDF 或图像，可以直接预览
        if filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, filename)
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(file_content)

            web_view.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
            web_view.setUrl(QUrl.fromLocalFile(temp_file_path))

        elif filename.lower().endswith(('.docx', '.doc')):
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, filename)
            # 将文件内容写入临时文件
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(file_content)

            # 使用 mammoth 将 .docx 文件转换为 HTML
            with open(temp_file_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                # if result.messages:
                #     print(f"Mammoth messages: {result.messages}")
                html_content = result.value  # 获取转换后的 HTML 内容
                # print(f'转换后的HTML内容为{html_content}')

            # 创建一个新的临时文件来保存 HTML
            html_temp_file_path = os.path.join(temp_dir, f"{os.path.splitext(filename)[0]}.html")
            with open(html_temp_file_path, 'w', encoding='utf-8') as html_file:
                html_file.write(html_content)

            # 在 QWebEngineView 中显示 HTML 文件
            web_view.setUrl(QUrl.fromLocalFile(html_temp_file_path))

        elif filename.lower().endswith(('.txt', '.cpp', '.py', 'java', '.md')):
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, filename)

            # 将文件内容写入临时文件
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(file_content)

            # 使用 QWebEngineView 来预览文本内容
            with open(temp_file_path, 'r', encoding='utf-8') as temp_file:
                text_content = temp_file.read()
            # 将文本内容包装成 HTML 格式以便在 QWebEngineView 中显示
            html_content = f"<html><body><pre>{text_content}</pre></body></html>"
            web_view.setHtml(html_content)
        elif filename.lower().endswith('.html'):
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, filename)
            # 将文件内容写入临时文件
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(file_content)
            # 使用 QWebEngineView 来显示 HTML 文件内容
            web_view.setUrl(QUrl.fromLocalFile(temp_file_path))
        else:
            # 对于其他文件类型，暂时只显示内容
            text_edit = QTextEdit(dialog)
            text_edit.setText("暂时无法预览此文件类型，请点击另存为下载文件。")
            layout.addWidget(text_edit)

        layout.addWidget(web_view, 1)

        # # 添加 "另存为" 按钮
        # save_button = QPushButton("另存为", dialog)
        # save_button.clicked.connect(lambda: self.save_file_as(filename, file_content))
        # layout.addWidget(save_button)

        # 创建按钮布局
        button_layout = QHBoxLayout()
        # 添加左右两侧的 spacing
        button_layout.addStretch(1)
        # 添加 "另存为" 按钮
        save_button = QPushButton("另存为", dialog)
        save_button.clicked.connect(lambda: self.save_file_as(filename, file_content))
        button_layout.addWidget(save_button, 1)
        button_layout.addStretch(1)
        # 将按钮布局添加到主布局中
        layout.addLayout(button_layout)

        # 查找功能实现
        def search_next():
            keyword = search_box.text()
            if keyword:
                web_view.page().findText(keyword, QWebEnginePage.FindFlags())

        def search_previous():
            keyword = search_box.text()
            if keyword:
                web_view.page().findText(keyword, QWebEnginePage.FindBackward)

        # 绑定按钮事件
        next_button.clicked.connect(search_next)
        prev_button.clicked.connect(search_previous)

        dialog.setLayout(layout)

        # 在对话框关闭时删除临时文件
        def cleanup_temp_file():
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                print(f"临时文件 {temp_file_path} 已删除")
                if html_temp_file_path and os.path.exists(html_temp_file_path):
                    os.remove(html_temp_file_path)
                    print(f"----临时文件 {html_temp_file_path} 已删除")

        dialog.finished.connect(cleanup_temp_file)
        dialog.exec_()

    # def show_file_preview_save(self, file_obj):
    #     """
    #     预览文件，预览页提供另存为按钮，用来将文件保存到本地
    #     :param file_obj: <Attachment(attachment_id=6, email_id=26, filename='logo.png',
    #     attachment_type='Attach', file_path='None')>
    #     :return:
    #     """
    #     print(f'预览并下载附件{file_obj}')
    #     filename = file_obj.filename
    #     eml_path = self.cur_eml_path
    #     with open(eml_path, 'rb') as file:
    #         raw_email = file.read()
    #     email_parser = EmailParser(raw_email)
    #     file_content = email_parser.get_attachment_by_filename(filename) # 完整的文件内容
    #
    #     dialog = QDialog(self)
    #     dialog.setWindowTitle(f"预览: {filename}")
    #     dialog.setFixedSize(1024, 750)
    #     layout = QVBoxLayout(dialog)
    #
    #     # 使用 QWebEngineView 预览内容
    #     web_view = QWebEngineView(dialog)
    #
    #     # 假设内容是 PDF 或图像，可以直接预览
    #     if filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp')):
    #         temp_path = os.path.join(os.getcwd(), filename)
    #         with open(temp_path, 'wb') as temp_file:
    #             temp_file.write(file_content)
    #
    #         web_view.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
    #         web_view.setUrl(QUrl.fromLocalFile(temp_path))
    #     else:
    #         # 对于其他文件类型，暂时只显示内容
    #         text_edit = QTextEdit(dialog)
    #         text_edit.setText("暂时无法预览此文件类型，请点击另存为下载文件。")
    #         layout.addWidget(text_edit)
    #
    #     layout.addWidget(web_view)
    #
    #     # 添加 "另存为" 按钮
    #     save_button = QPushButton("另存为", dialog)
    #     save_button.clicked.connect(lambda: self.save_file_as(filename, file_content))
    #     layout.addWidget(save_button)
    #
    #     dialog.setLayout(layout)
    #
    #     def cleanup_temp_file():
    #         if temp_path and os.path.exists(temp_path):
    #             os.remove(temp_path)
    #             print(f"临时文件 {temp_path} 已删除")
    #
    #     dialog.finished.connect(cleanup_temp_file)
    #     dialog.exec_()

    def save_file_as(self, filename, file_content):
        """
        处理文件另存为操作
        :param filename: 文件名
        :param file_content: 文件内容
        :return:
        """
        options = QFileDialog.Options()
        save_path, _ = QFileDialog.getSaveFileName(self, "另存为", filename,
                                                   "All Files (*);;PDF Files (*.pdf);;Image Files (*.png *.jpg *.jpeg "
                                                   "*.gif *.bmp)",
                                                   options=options)

        if save_path:
            with open(save_path, 'wb') as file:
                file.write(file_content)
            QMessageBox.information(self, "文件保存", f"文件已成功保存到: {save_path}")

    def show_file_preview_open(self, file_obj, file_abstract_path):
        """
        预览文件，预览页面提供打开文件位置按钮，在资源管理器中显示该文件
        :param file_abstract_path: 文件的绝对路径
        :param file_obj: <Attachment(attachment_id=6, email_id=26, filename='logo.png',
        attachment_type='Attach', file_path='xxx/yyy/zzz')>
        :return:
        """
        print(f'预览并打开附件{file_obj}')
        filename = file_obj.filename

        # 创建对话框用于显示预览和打开文件位置按钮
        dialog = QDialog(self)
        dialog.setWindowTitle(f"预览: {filename}")
        dialog.setFixedSize(1024, 750)
        layout = QVBoxLayout(dialog)

        # 添加搜索框和查找按钮布局
        search_layout = QHBoxLayout()
        search_box = QLineEdit(dialog)
        search_box.setPlaceholderText("输入关键词查找")
        next_button = QPushButton("下一个", dialog)
        prev_button = QPushButton("上一个", dialog)
        search_layout.addWidget(search_box)
        search_layout.addWidget(prev_button)
        search_layout.addWidget(next_button)
        layout.addLayout(search_layout)

        # 临时HTML文件
        html_temp_file_path = None

        # 使用 QWebEngineView 预览内容
        web_view = QWebEngineView(dialog)

        # 内容是 PDF 或图像，可以直接预览
        if filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            web_view.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
            web_view.setUrl(QUrl.fromLocalFile(file_abstract_path))
            # layout.addWidget(web_view)
        elif filename.lower().endswith(('.docx', '.doc')):
            temp_dir = tempfile.gettempdir()
            with open(file_abstract_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html_content = result.value  # 获取转换后的HTML内容

            html_temp_file_path = os.path.join(temp_dir, f"{os.path.splitext(filename)[0]}.html")
            with open(html_temp_file_path, 'w', encoding='utf-8') as html_file:
                html_file.write(html_content)

            # 在 QWebEngineView 中显示 HTML 文件
            web_view.setUrl(QUrl.fromLocalFile(html_temp_file_path))

            # # 在 QWebEngineView 中显示 HTML
            # web_view.setHtml(html_content)

        elif filename.lower().endswith(('.txt', '.cpp', '.py', 'java', '.md')):
            with open(file_abstract_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
            # 将内容包装为 HTML 格式，方便在 QWebEngineView 中显示
            html_content = f"<pre>{file_content}</pre>"
            # 在 QWebEngineView 中显示 HTML
            web_view.setHtml(html_content)
        elif filename.lower().endswith('.html'):
            web_view.setUrl(QUrl.fromLocalFile(file_abstract_path))
        else:
            # 对于其他文件类型，暂时只显示内容
            text_edit = QTextEdit(dialog)
            text_edit.setText("暂时无法预览此文件类型，请点击打开文件位置。")
            layout.addWidget(text_edit)

        layout.addWidget(web_view, 1)

        # 创建按钮布局
        button_layout = QHBoxLayout()
        # 添加左侧的spacing
        button_layout.addStretch(1)  # 在左侧添加20像素的空白
        # 添加 "打开文件位置" 按钮
        open_button = QPushButton("打开文件位置", dialog)
        open_button.clicked.connect(lambda: self.open_file_location(file_abstract_path))
        button_layout.addWidget(open_button, 1)
        # 添加右侧的spacing
        button_layout.addStretch(1)  # 在右侧添加20像素的空白

        layout.addLayout(button_layout)

        # 查找功能实现
        def search_next():
            keyword = search_box.text()
            if keyword:
                web_view.page().findText(keyword, QWebEnginePage.FindFlags())

        def search_previous():
            keyword = search_box.text()
            if keyword:
                web_view.page().findText(keyword, QWebEnginePage.FindBackward)

        # 绑定按钮事件
        next_button.clicked.connect(search_next)
        prev_button.clicked.connect(search_previous)

        dialog.setLayout(layout)

        def cleanup_temp_html_file():
            print("预览页面已关闭")
            if html_temp_file_path and os.path.exists(html_temp_file_path):
                os.remove(html_temp_file_path)
                print(f"临时文件 {html_temp_file_path} 已删除")

        dialog.finished.connect(cleanup_temp_html_file)
        dialog.exec_()

    def open_file_location(self, file_path):
        """
        打开文件所在的目录并选中文件
        :param file_path: 文件的绝对路径
        :return:
        """
        # print(f'文件绝对路径{file_path}')
        file_path = Path(file_path)
        try:
            if os.name == 'nt':  # Windows
                subprocess.Popen(f'explorer /select,"{file_path}"')
            elif os.name == 'posix':  # macOS or Linux
                subprocess.Popen(['xdg-open', file_path])
            else:
                raise NotImplementedError("不支持的操作系统")
        except Exception as e:
            print(f"打开文件位置失败: {e}")

    def get_file_base64(self):
        file_path = 'E:\Xsoftware\Python\workstation\MDLStore_UI\emls\进度汇报-梁家浩-20240811.eml'
        file_path = file_path.replace('\\', '/')
        with open(file_path, 'rb') as file:
            raw_email = file.read()
        email_parser = EmailParser(raw_email)
        headers = email_parser.get_headers()
        subject = email_parser.getSubject(headers)
        # images_info = email_parser.extract_images()
        print(email_parser.get_attachments())
        return email_parser.get_attachment_base64_by_filename('进度汇报-梁家浩-20240811.docx')

    def show_file_preview(self, file_path, file_type):
        dialog = QDialog(self)
        dialog.resize(1024, 750)
        dialog.setWindowTitle(f"Preview: {os.path.basename(file_path)}")
        layout = QVBoxLayout(dialog)

        if file_type == "image":
            label = QLabel(dialog)
            pixmap = QPixmap(file_path)
            label.setPixmap(pixmap.scaled(800, 600, Qt.KeepAspectRatio))
            layout.addWidget(label)

        elif file_type == "pdf" or file_type == 'docx':
            # 使用 QWebEngineView 来预览 PDF 文件
            pdf_view = QWebEngineView(dialog)
            print(f'路径{QUrl.fromLocalFile(file_path)}')
            pdf_view.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
            pdf_view.setUrl(QUrl.fromLocalFile(file_path))
            layout.addWidget(pdf_view)

        elif file_type == 'docx':
            pass
            # pdf_view = QWebEngineView(dialog)
            # pdf_view.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
            # # 加载 Data URL
            # pdf_view.setUrl(QUrl(data_url))
            # layout.addWidget(pdf_view)

        else:  # 对于非 PDF 文件，尝试将其打印为 PDF
            pdf_path = os.path.splitext(file_path)[0] + ".pdf"
            try:
                self.print_to_pdf(file_path, pdf_path)
                pdf_view = QWebEngineView(dialog)
                pdf_view.setUrl(QUrl.fromLocalFile(pdf_path))
                layout.addWidget(pdf_view)
            except Exception as e:
                text_edit = QTextEdit(dialog)
                text_edit.setText(f"Cannot preview or print this file type.\nError: {e}")
                layout.addWidget(text_edit)

        dialog.setLayout(layout)
        dialog.exec_()

    def print_to_pdf(self, file_path, output_pdf_path):
        # 创建 QPrinter 对象
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(output_pdf_path)

        # 使用 QPainter 绘制内容（这里只是一个示例，具体绘制内容需根据文件类型调整）
        painter = QPainter()
        painter.begin(printer)

        try:
            with open(file_path, 'r') as file:
                content = file.read()
                painter.drawText(100, 100, content)  # 在 PDF 上绘制文本
        except Exception as e:
            raise RuntimeError(f"Failed to print to PDF: {e}")
        finally:
            painter.end()

    def set_target_drive(self, drive):
        self.tar_drive = drive
        # print(f'阅读器获取磁盘{self.tar_drive}')

    @staticmethod
    def adjust_list_widget_size(list_widget):
        item_width = 180  # 每个项目的宽度
        items_per_row = 4  # 每行最多 4 个项目

        total_items = list_widget.count()
        if total_items == 0:
            list_widget.setFixedSize(0, 0)
            return

        # 计算行数
        rows = (total_items + items_per_row - 1) // items_per_row

        # 计算列表控件的宽度和高度
        list_width = item_width * items_per_row + 50
        list_height = rows * 30 + rows + 1  # 每行项目的高度为 50px
        list_widget.setFixedSize(list_width, list_height)

    def set_search_keywords(self, body_text, filename, content_):
        self.search_body_text = body_text
        self.search_filename = filename
        self.search_content_keyword = content_
