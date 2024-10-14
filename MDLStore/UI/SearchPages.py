from pathlib import Path

from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, QComboBox, QPushButton, QTextEdit, QMessageBox
)
from PyQt5.QtCore import QDate, Qt
from dataclasses import dataclass
from typing import Optional
from datetime import date

from MDLStore.UI.THEMES import TREEVIEW_TASKS_FOLDER
from MDLStore.UI.Ui_SearchPage import Ui_SearchPage
from MDLStore.database.index_database_setup import DatabaseManager
from MDLStore.database.service import StatisticManager
from MDLStore.search import MailSearcher
from MDLStore.storage import StorageManager
from MDLStore.ui_utils import APP_Signals


@dataclass
class EmailSearchCriteria:
    email_id: Optional[int] = None
    email_address: Optional[str] = None
    email_uid: Optional[int] = None
    subject: Optional[str] = None
    from_address: Optional[str] = None
    to_addresses: Optional[str] = None
    cc_addresses: Optional[str] = None
    bcc_addresses: Optional[str] = None
    received_date_start: Optional[date] = None
    received_date_end: Optional[date] = None
    task_name: Optional[str] = None
    mailbox: Optional[str] = None
    body_text: Optional[str] = None
    eml_path: Optional[str] = None


@dataclass
class AttachmentSearchCriteria:
    attachment_id: Optional[int] = None
    email_id: Optional[int] = None
    filename: Optional[str] = None
    attachment_type: Optional[str] = None
    file_path: Optional[str] = None


class SearchPage(QWidget, Ui_SearchPage):
    def __init__(self, parent=None, *args, **kwargs):
        super(SearchPage, self).__init__(parent, *args, **kwargs)
        self.taskname = None
        self.search_filename = None
        self.search_content_keyword = None
        self.search_body_text = None
        self.model = None
        self.date_end = None
        self.date_start = None
        self.tar_drive = None
        self.setupUi(self)

        self.init_ui()
        self.set_theme()

    def init_ui(self):
        self.button_search.clicked.connect(self.start_search)
        self.button_clear.clicked.connect(self.clearSearchCriteria)
        self.init_treeView()
        self.init_date_input()

        self.label_date.setAlignment(Qt.AlignCenter)  # 设置文本居中对齐
        # self.textBrowser_details.setWordWrap(True)  # 允许换行
        self.textBrowser_details.setTextInteractionFlags(
            self.textBrowser_details.textInteractionFlags() | 0x1)  # 启用HTML链接等交互

        # 安装事件过滤器
        self.installEventFilter(self)

    def set_theme(self):
        # self.label_from.setStyleSheet()
        # self.label_subject.setAlignment(Qt.AlignRight)
        self.treeView.setStyleSheet(TREEVIEW_TASKS_FOLDER)
        self.treeView.setFocusPolicy(Qt.NoFocus)

    # 事件过滤器
    def eventFilter(self, obj, event):
        # 检查事件类型是否是按键按下
        if event.type() == event.KeyPress and event.key() == Qt.Key_Return:
            # 如果按下的是回车键，触发搜索按钮点击
            self.button_search.click()
            return True  # 事件已处理
        # 检查是否按下ESC键
        elif event.type() == event.KeyPress and event.key() == Qt.Key_Escape:
            self.button_clear.click()
            return True  # 事件已处理
        return super(SearchPage, self).eventFilter(obj, event)

    def start_search(self):
        # print(f'选中磁盘{self.tar_drive}')
        if not self.tar_drive:
            QMessageBox.warning(self, "缺少查询范围", "请在左侧选择磁盘分区或任务名！")
            return

        APP_Signals.search_finished.emit()

    def search_email_data(self):
        target_drive = self.tar_drive
        task_name = self.taskname
        account = None if self.lineEdit_account.text() == '' else self.lineEdit_account.text()
        subject = None if self.lineEdit_subject.text() == '' else self.lineEdit_subject.text()
        sender = None if self.lineEdit_from.text() == '' else self.lineEdit_from.text()
        send_to = None if self.lineEdit_to.text() == '' else self.lineEdit_to.text()
        filename = None if self.lineEdit_filename.text() == '' else self.lineEdit_filename.text()
        cc = None if self.lineEdit_cc.text() == '' else self.lineEdit_cc.text()
        bcc = None if self.lineEdit_bcc.text() == '' else self.lineEdit_bcc.text()
        body_text = None if self.lineEdit_body.text() == '' else self.lineEdit_body.text()
        content_keyword = None if self.lineEdit_file_content.text() == '' else self.lineEdit_file_content.text()
        date_start, date_end = self.get_date_range()

        email_criteria = EmailSearchCriteria(
            email_address=account,
            subject=subject,
            from_address=sender,
            to_addresses=send_to,
            cc_addresses=cc,
            bcc_addresses=bcc,
            received_date_start=date_start,
            received_date_end=date_end,
            task_name=task_name,
            body_text=body_text,
        )

        attachment_criteria = AttachmentSearchCriteria(
            filename=filename
        )
        self.search_body_text = body_text
        self.search_filename = filename

        searcher = MailSearcher(target_drive)
        if content_keyword is None:
            print(f'搜索1 常规检索')
            email_searched = searcher.search_emails_and_attachments(email_criteria, attachment_criteria)
            emails = email_searched
            self.search_content_keyword = None
        else:
            print(f'搜索2 全文检索')
            self.search_content_keyword = content_keyword
            email_searched = searcher.search_all_with_fulltext2(email_criteria, attachment_criteria, content_keyword)
            emails = []
            for i in email_searched:
                email = i['email']
                files = i['files']
                # 动态为 email 对象添加一个 files 属性
                email.files = files
                # 将处理过的 email 对象添加到 emails 列表
                emails.append(email)
        # print(f'搜索结果')
        # for item in emails:
        #     print(item)
        #     if hasattr(item, 'files'):
        #         print(item.files)
        #     else:
        #         print(f'==={item.attachments}')
        return emails

    def init_treeView(self):

        # partitions = ['C', 'D', 'E', 'F']
        partitions = self.get_disks_info_partitions()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["历史备份任务"])

        # 添加分区到模型中
        for partition in partitions:
            partition_item = QStandardItem(partition)
            partition_item.setEditable(False)  # 禁止编辑分区名称
            self.model.appendRow(partition_item)

            # 添加子文件夹
            sub_folders = self.get_subfolders(f'{partition}:/MDLStore')
            for folder_name in sub_folders:
                folder_item = QStandardItem(folder_name)
                folder_item.setEditable(False)  # 禁止编辑文件夹名称
                partition_item.appendRow(folder_item)

        # 将模型设置到 QTreeView 中
        self.treeView.setModel(self.model)
        self.treeView.expandAll()  # 展开所有节点

        self.treeView.clicked.connect(self.on_item_clicked)
        self.button_flash.clicked.connect(self.refresh_treeView)
        APP_Signals.flush_storage_infos.connect(self.refresh_treeView)

    def on_item_clicked(self, index):
        # 获取被点击的项目
        item = self.model.itemFromIndex(index)
        if item.parent() is None:
            partition = item.text()
            subdirectory = None
        else:
            partition = self.get_partition(item)
            subdirectory = item.text()

            # 打印结果
        # print(f"Selected item: {subdirectory}, Partition: {partition}")
        self.taskname = subdirectory
        self.tar_drive = partition
        # print(self.taskname, self.tar_drive)
        print(f'查询磁盘{self.tar_drive}--备份任务{self.taskname}')

        # 查看任务数据概览
        session = DatabaseManager(self.tar_drive).get_session()
        statistic_manager = StatisticManager(session)

        if self.taskname:
            taskname_ = self.taskname
            statistic_infos = statistic_manager.get_statistic_info(taskname_)
            print(statistic_infos)
        else:
            # print(f'大范围统计')
            statistic_infos = statistic_manager.get_all_statistic_info()

        self.display_statistics_in_label(statistic_infos)

        # 释放焦点
        self.button_search.setFocus()  # 将焦点设置到搜索按钮

    def display_statistics_in_label(self, statistic_infos):
        """
        将 statistic_infos 数据在 QLabel 中以简单 HTML 表格形式显示，并手动设置明暗相间的背景色，同时计算各列总和
        :param statistic_infos: 包含统计信息的列表
        """
        # 初始化计数器，用于存储各列的总和
        total_mail_count = 0
        total_direct_attachments = 0
        total_cloud_attachments = 0

        # 创建 HTML 表格的头部，直接为表格设置样式
        html_content = """
        <html>
        <style>
            table { 
                width: 100%;  /* 表格宽度 */
                border: none;  /* 移除表格的默认边框 */
                border-spacing: 0px;  /* 确保单元格之间没有间隙 */
                background-color: #f0f8ff;  /* 表格背景颜色 */
            }
            th, td {
                border: none;  /* 移除单元格的边框 */
                padding: 10px 20px;  /* 单元格内边距：上下10px，左右20px */
                text-align: center;  /* 文字水平居中 */
                vertical-align: middle;  /* 文字垂直居中 */
                background-color: #ffffff;  /* 单元格背景颜色 */
                font-family: Arial, sans-serif;  /* 字体样式 */
            }
            th {
                background-color: #add8e6;  /* 表头背景色 */
                padding: 12px 20px;  /* 表头内边距，左右边距大一些 */
            }
        </style>
        <table>
            <tr>
                <th style="padding-left: 80px;padding-right: 80px;">邮箱账户</th>
                <th style="padding-left: 35px;padding-right: 35px;">邮件数</th>
                <th>直接附件数</th>
                <th>云附件数</th>
            </tr>
        """

        # 遍历统计信息，并手动设置行的背景色，奇数行和偶数行不同
        for index, info in enumerate(statistic_infos):
            if index % 2 == 0:
                # 偶数行背景色
                row_background = '#f2f2f2'
            else:
                # 奇数行背景色
                row_background = '#aaaaaa'

            # 累加每列的数据
            total_mail_count += info['邮件数量']
            total_direct_attachments += info['直接附件数量']
            total_cloud_attachments += info['云附件数量']

            # 生成表格行内容
            html_content += f"""
            <tr style="background-color: {row_background};">
                <td>{info['邮箱账户']}</td>
                <td>{info['邮件数量']}</td>
                <td>{info['直接附件数量']}</td>
                <td>{info['云附件数量']}</td>
            </tr>
            """

        # 添加最后一行，显示各列的总和
        html_content += f"""
        <tr style="background-color: #add8e6;">
            <td><b>总计</b></td>
            <td>{total_mail_count}</td>
            <td>{total_direct_attachments}</td>
            <td>{total_cloud_attachments}</td>
        </tr>
        """

        # 关闭表格
        html_content += "</table></html>"

        # 在 QLabel 中显示 HTML 表格
        self.textBrowser_details.setText(html_content)

    @staticmethod
    def get_partition(item):
        # 向上查找，直到找到根节点（即分区）
        while item.parent() is not None:
            item = item.parent()
        return item.text()

    @staticmethod
    def get_subfolders(base_folder):
        base_path = Path(base_folder)

        # 检查路径是否存在
        if not base_path.exists():
            return []

        # 返回子文件夹名称列表
        sub_folders = [f.name for f in base_path.iterdir() if f.is_dir()]
        if 'index' in sub_folders:
            sub_folders.remove('index')

        return sub_folders

    def refresh_treeView(self):
        # 假设 partitions 变量可能会变化，你可以在这里重新定义它
        # partitions = ['C', 'D', 'E']
        partitions = self.get_disks_info_partitions()
        # 清空现有模型
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["历史备份任务"])

        # 重新添加分区到模型中
        for partition in partitions:
            partition_item = QStandardItem(partition)
            partition_item.setEditable(False)  # 禁止编辑分区名称
            self.model.appendRow(partition_item)

            # 重新添加子文件夹
            sub_folders = self.get_subfolders(f'{partition}:/MDLStore')
            for folder_name in sub_folders:
                folder_item = QStandardItem(folder_name)
                folder_item.setEditable(False)  # 禁止编辑文件夹名称
                partition_item.appendRow(folder_item)

        # 刷新视图
        self.treeView.expandAll()  # 展开所有节点

    def init_date_input(self):
        self.dateEdit_start.setCalendarPopup(True)
        self.dateEdit_end.setCalendarPopup(True)

        self.label_date.hide()
        self.dateEdit_end.hide()
        self.dateEdit_start.hide()

        self.comboBox.currentIndexChanged.connect(self.on_combobox_changed)

        today = QDate.currentDate()
        self.dateEdit_start.setDate(today)
        self.dateEdit_end.setDate(today)

        # self.date_start = None
        # self.date_end = None
        self.date_start = self.dateEdit_start.date()
        self.date_end = self.dateEdit_end.date()

    def on_combobox_changed(self, index):
        if index == 0:
            self.label_date.hide()
            self.dateEdit_start.hide()
            self.dateEdit_end.hide()
        if index == 1:  # 指定收件日期
            self.dateEdit_start.show()
            self.label_date.hide()
            self.dateEdit_end.hide()
            # 将结束日期设置为与开始日期相同
            # self.date_end = self.dateEdit_start.date()
        elif index == 2:  # 指定日期及以前
            self.label_date.show()
            self.dateEdit_start.hide()
            self.dateEdit_end.show()
            # self.date_start = None
            # self.date_end = self.dateEdit_end.date()
        elif index == 3:  # 指定收件时段
            self.dateEdit_start.show()
            self.label_date.show()
            self.dateEdit_end.show()
            # # 在日期选择后更新日期区间
            # self.date_start = self.dateEdit_start.date()
            # self.date_end = self.dateEdit_end.date()

    def get_date_range(self):
        # 返回选定的日期区间
        if self.dateEdit_end.isHidden() and self.dateEdit_start.isHidden() and self.label_date.isHidden():
            self.date_start = self.date_end = None
            return self.date_start, self.date_end
        elif self.label_date.isHidden() and self.dateEdit_end.isHidden():
            self.date_start = self.date_end = self.dateEdit_start.date()
        elif self.dateEdit_start.isHidden():
            self.date_start = None
            self.date_end = self.dateEdit_end.date()
            return self.date_start, self.date_end.toPyDate()
        else:
            self.date_start = self.dateEdit_start.date()
            self.date_end = self.dateEdit_end.date()
        print('搜索日期', self.date_start.toPyDate(), self.date_end.toPyDate())
        return self.date_start.toPyDate(), self.date_end.toPyDate()

    @staticmethod
    def get_disks_info_partitions():
        storage_manager = StorageManager()
        # 刷新
        storage_manager.refresh_disk_info()
        partitions = storage_manager.get_disk_partitions()

        result_partition = []
        for partition in partitions:
            # print(f"Device: {partition.device}, Mountpoint: {partition.mountpoint}, Fstype: {partition.fstype}")
            result_partition.append(partition.device[0])
        return result_partition

    def clearSearchCriteria(self):
        self.lineEdit_account.clear()
        self.lineEdit_from.clear()
        self.lineEdit_filename.clear()
        self.lineEdit_subject.clear()
        self.lineEdit_cc.clear()
        self.lineEdit_bcc.clear()
        self.lineEdit_to.clear()
        self.lineEdit_file_content.clear()
        self.lineEdit_body.clear()


