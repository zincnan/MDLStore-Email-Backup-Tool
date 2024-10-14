import os
import random
import string
import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidgetItem, QMessageBox

from MDLStore.UI.AboutPages import AboutPage
from MDLStore.UI.BackupTaskPages import BackupTaskPage
from MDLStore.UI.EmailAccountPages import AccountPage, MyObject
from MDLStore.UI.HomePages import HomePage
from MDLStore.UI.ResultPages import ResultPage
from MDLStore.UI.SearchPages import SearchPage
from MDLStore.UI.THEMES import FUNC_LIST_THEME
from MDLStore.UI.Ui_main_app import Ui_MainAppPage
from MDLStore.ui_utils import APP_Signals, UiUtils

module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
icon_path = os.path.join(module_path, 'icons')

class MainApp(Ui_MainAppPage, QWidget):
    def __init__(self, width, height, parent=None, *args, **kwargs):
        super(MainApp, self).__init__(parent, *args, **kwargs)
        self.setupUi(self)

        self.setGeometry(0, 0, width, height)

        self.init_ui()
        self.set_layout()
        self.set_theme()

    def init_ui(self):
        # self.left_widget.addItem("开始页面")
        # self.left_widget.addItem("邮箱账户管理")
        # self.left_widget.addItem("备份任务管理")
        # self.left_widget.addItem("搜索邮件数据")
        # self.left_widget.addItem("搜索结果")
        # self.left_widget.addItem("关于软件")

        # item1 = QListWidgetItem(QIcon(os.path.join(icon_path, 'home.png')), "开始页面")
        cur_icon = QIcon(':/icons/home.png')
        item1 = QListWidgetItem(QIcon(cur_icon), "开始页面")
        self.left_widget.addItem(item1)

        cur_icon = QIcon(':/icons/mailbox.png')
        item2 = QListWidgetItem(cur_icon, "邮箱账户管理")
        self.left_widget.addItem(item2)

        cur_icon = QIcon(':/icons/mailbox.png')
        item3 = QListWidgetItem(QIcon(':/icons/task2.png'), "备份任务管理")
        self.left_widget.addItem(item3)

        cur_icon = QIcon(':/icons/search.png')
        item4 = QListWidgetItem(cur_icon, "搜索邮件数据")
        self.left_widget.addItem(item4)

        cur_icon = QIcon(':/icons/read_email.png')
        item5 = QListWidgetItem(cur_icon, "搜索结果")
        self.left_widget.addItem(item5)

        cur_icon = QIcon(':/icons/about_app.png')
        item6 = QListWidgetItem(cur_icon, "关于软件")
        self.left_widget.addItem(item6)

        self.left_widget.currentRowChanged.connect(self.display_page)

        self.account_page = AccountPage()
        self.task_page = BackupTaskPage()
        self.search_page = SearchPage()
        APP_Signals.search_finished.connect(self.show_search_result_page)
        APP_Signals.jump_page.connect(self.jump_to_pages)
        self.result_page = ResultPage()

        self.about_page = AboutPage()
        self.home_page = HomePage()

        self.stackedWidget.addWidget(self.home_page)
        self.stackedWidget.addWidget(self.account_page)
        self.stackedWidget.addWidget(self.task_page)
        self.stackedWidget.addWidget(self.search_page)
        self.stackedWidget.addWidget(self.result_page)
        self.stackedWidget.addWidget(self.about_page)

    def set_layout(self):
        layout_frame = self.frame.layout()
        utils = UiUtils()
        utils.set_stretch_by_widget(layout_frame, self.verticalLayout, 1)
        utils.set_stretch_by_widget(layout_frame, self.stackedWidget, 6)

    def set_theme(self):
        self.stackedWidget.setStyleSheet("""
            QStackedWidget {
                border: 2px solid black;  /* 设置边框为黑色，宽度为2px */
                border-radius: 5px;  /* 可选：设置圆角边框 */
            }
        """)
        self.left_widget.setFocusPolicy(Qt.NoFocus)
        self.left_widget.setStyleSheet(FUNC_LIST_THEME)

    def display_page(self, index):
        """根据左侧按钮栏的索引显示对应的页面"""
        # print(index)
        self.stackedWidget.setCurrentIndex(index)

    def create_page(self, text):
        """创建一个简单的页面，包含一个标签"""
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(text, page)
        layout.addWidget(label)
        return page

    def show_search_result_page(self):
        # 获取对象列表
        # objs = generate_random_objects(6)
        emails = self.search_page.search_email_data()

        self.result_page.set_target(self.search_page.tar_drive)
        self.result_page.set_search_keywords(self.search_page.search_body_text,
                                             self.search_page.search_filename,
                                             self.search_page.search_content_keyword)

        if not emails:
            QMessageBox.warning(self, "提示", "没有符合条件的邮件数据！请重新搜索")
            return

        self.result_page.refresh_list(emails)

        QMessageBox.information(self, "搜索完成", f"共找到相关邮件{len(emails)}封！")
        # self.stackedWidget.setCurrentIndex(4)
        self.left_widget.setCurrentRow(4)

    def jump_to_pages(self, index):
        pass
        # print(f'跳转{index}')
        self.left_widget.setCurrentRow(index)


def generate_random_objects(num_objects):
    objects = []
    for _ in range(num_objects):
        name = ''.join(random.choices(string.ascii_uppercase, k=5))  # 随机生成5个字母的名称
        value = random.randint(1, 100)  # 随机生成1到100之间的整数值
        obj = MyObject(name, value)
        objects.append(obj)
    return objects
