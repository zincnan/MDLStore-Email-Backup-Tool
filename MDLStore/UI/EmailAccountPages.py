import traceback

from PyQt5.QtCore import QVariant, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QListWidget, QListWidgetItem, QFormLayout, QLineEdit, QTextEdit, \
    QPushButton, QDialog, QVBoxLayout, QMessageBox, QSizePolicy, QSpacerItem

from MDLStore.UI.THEMES import LISTVIEW_ACC
from MDLStore.UI.Ui_AccountPage import Ui_AccountPage
from MDLStore.database.config_database_setup import setupConfigDatabase, SessionManager
from MDLStore.database.entities import EmailAccount
from MDLStore.database.service import EmailAccountManager
from MDLStore.mailclients import IMAPClientFactory
from MDLStore.ui_utils import UiUtils, MessageDialog
from MDLStore.utils import ServerUtils


class MyObject:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return f"{self.name}: {self.value}"

    def __eq__(self, other):
        if isinstance(other, MyObject):
            return self.name == other.name and self.value == other.value
        return False

    def __hash__(self):
        return hash((self.name, self.value))


class AccountPage(Ui_AccountPage, QWidget):
    def __init__(self, parent=None, *args, **kwargs):
        super(AccountPage, self).__init__(parent, *args, **kwargs)
        self.setupUi(self)

        # self.setGeometry(0, 0, width, height)

        self.init_ui()
        self.set_layout()
        self.set_theme()

    def init_ui(self):
        # 初始化数据库
        setupConfigDatabase()

        self.button_new_account.clicked.connect(self.show_input_dialog)
        self.init_listView()
        self.button_delete.clicked.connect(self.delete_item)

        self.button_password.setFixedSize(29, 29)
        self.button_password.setCheckable(True)
        self.button_password.toggled.connect(self.toggle_password_visibility)

    def init_listView(self):
        self.model = QStandardItemModel()

        # 获取邮箱列表信息
        # setupConfigDatabase()
        session = SessionManager().get_session()
        manager = EmailAccountManager(session)
        email_list = manager.get_all_email_account()
        # print(f'打印邮箱列表{type(email_list)}')
        # 创建自定义对象列表
        # self.object_list = [
        #     MyObject("Object 1", 10),
        #     MyObject("Object 2", 20),
        #     MyObject("Object 3", 30),
        #     MyObject("Object 4", 40),
        #     MyObject("Object 5", 50)
        # ]
        self.object_list = email_list

        self.populate_list()
        self.listView.clicked.connect(self.on_item_clicked)

    def populate_list(self):
        self.model.clear()  # 清空模型
        for obj in self.object_list:
            # item = QStandardItem(str(obj))  # 设置显示的文本
            item = QStandardItem(f'邮箱地址：{obj.username}')
            item.setData(QVariant(obj), Qt.UserRole)  # 存储对象
            self.model.appendRow(item)  # 逐个添加项
        self.listView.setModel(self.model)  # 设置模型到 QListView

    def on_item_clicked(self, index):
        self.selected_index = index
        item = self.model.itemFromIndex(index)
        text = item.text()
        # print(f"Clicked item: {text}")
        obj = item.data(Qt.UserRole)  # 获取存储的对象
        # if obj:
        #     print(f"Clicked item: {obj}")
        #     print(f"Object name: {obj.name}, Object value: {obj.value}")
        username = obj.username
        password = obj.password
        server_address = obj.server_address
        port = obj.port
        remarks = obj.remarks
        # print(f"Username: {username}")
        # print(f"Password: {password}")
        # print(f"Server Address: {server_address}")
        # print(f"Port: {port}")
        # print(f"Remarks: {remarks}")

        self.lineEdit_email_addr.setText(username)
        self.lineEdit_password.setText(password)
        self.lineEdit_password.setEchoMode(QLineEdit.Password)
        self.lineEdit_imap_server.setText(server_address)
        self.lineEdit_port.setText(str(port))
        self.textEdit_remarks.setText(remarks)

    def delete_item(self):
        if self.selected_index is not None:
            reply = QMessageBox.question(
                self,
                "确认删除",
                "您确定要删除该项目吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                item = self.model.itemFromIndex(self.selected_index)
                obj = item.data(Qt.UserRole)
                if obj in self.object_list:
                    session = SessionManager().get_session()
                    manager = EmailAccountManager(session)
                    print(f'邮箱地址{obj}')
                    try:
                        manager.delete_email_account(obj.account_id)
                    except Exception as e:  # 捕获所有异常
                        print(f"An error occurred: {str(e)}")  # 输出简单的错误消息
                        traceback.print_exc()  # 打印完整的堆栈追踪信息

                    self.object_list.remove(obj)  # 从对象列表中删除对象
                    # print(f"Deleted item: {obj}")
                    self.populate_list()  # 更新视图
                self.selected_index = None  # 清除选中状态

    def set_layout(self):
        self.init_spacers()
        utils = UiUtils()
        utils.set_stretch_by_widget(self.horizontalLayout_2, self.verticalLayout, 2)
        utils.set_stretch_by_widget(self.horizontalLayout_2, self.frame, 3)
        utils.set_stretch_by_widget(self.horizontalLayout_2, self.spacer_h_1, 0.6)
        utils.set_stretch_by_widget(self.horizontalLayout_2, self.spacer_h_2, 0.8)

        # 设置所有行的stretch为相同的值，比如 1
        # self.label_status.setMaximumHeight(30)

        for row in range(self.gridLayout.rowCount()):
            self.gridLayout.setRowMinimumHeight(row, 50)  # 设置每行的最小高度为50像素
            self.gridLayout.setRowStretch(row, 0)  # 确保行的拉伸因子为0，以避免高度变化
        self.gridLayout.setColumnStretch(0, 1)  # 确保行的拉伸因子为0，以避免高度变化
        self.gridLayout.setColumnStretch(1, 4)  # 确保行的拉伸因子为0，以避免高度

    def init_spacers(self):
        self.spacer_h_1 = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
        # 在第三个位置（索引2）插入spacer
        self.horizontalLayout_2.insertSpacerItem(1, self.spacer_h_1)
        self.spacer_h_2 = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
        # 在第三个位置（索引2）插入spacer
        self.horizontalLayout_2.insertSpacerItem(3, self.spacer_h_2)

        self.spacer2 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.frame.layout().insertSpacerItem(1, self.spacer2)

    def set_theme(self):
        self.listView.setStyleSheet(LISTVIEW_ACC)
        self.listView.setFocusPolicy(Qt.NoFocus)
        # print(self.label_status.width())
        # self.setStyleSheet("""
        #     QLabel {
        #         border: 2px solid red;
        #     }
        # """)

    def show_input_dialog(self):
        dialog = EmailAccountDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # 处理表单数据
            form = dialog.form
            email = form.email_input.text()
            password = form.password_input.text()
            imap_server = form.imap_server_input.text()
            imap_port = form.imap_port_input.text()
            remark = form.remark_input.toPlainText()
            # print(email, password, imap_server)

            email_account = form.email_account_input

            # new_object = MyObject("Object 6", 60)
            self.object_list.append(email_account)  # 添加新对象到列表中
            # print(f"Added item: {new_object}")
            self.populate_list()  # 更新视图

    def toggle_password_visibility(self, checked):
        if checked:
            self.lineEdit_password.setEchoMode(QLineEdit.Normal)  # 显示明文
        else:
            self.lineEdit_password.setEchoMode(QLineEdit.Password)  # 显示密


class EmailAccountForm(QWidget):
    def __init__(self, parent=None):
        super(EmailAccountForm, self).__init__(parent)
        # 主布局
        self.email_account_input = None
        main_layout = QHBoxLayout(self)

        # 左侧的邮箱服务类型列表
        self.service_list = QListWidget()
        services = ["网易163邮箱", "网易126邮箱", "QQ邮箱", "搜狐邮箱", "电信189邮箱", "RUC人大邮箱", "Gmail邮箱",
                    "Outlook邮箱", "搜狐邮箱", "其他邮箱"]
        for service in services:
            item = QListWidgetItem(service)
            self.service_list.addItem(item)
        main_layout.addWidget(self.service_list)

        # 右侧的表单布局
        form_layout = QFormLayout()

        # 邮箱账户
        self.email_input = QLineEdit()
        form_layout.addRow("邮箱账户:", self.email_input)

        # 密码
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("密码:", self.password_input)

        # IMAP 服务器地址
        self.imap_server_input = QLineEdit()
        form_layout.addRow("IMAP 服务器地址:", self.imap_server_input)

        # IMAP 端口
        self.imap_port_input = QLineEdit()
        form_layout.addRow("IMAP 端口:", self.imap_port_input)

        # 备注信息
        self.remark_input = QTextEdit()
        form_layout.addRow("备注信息:", self.remark_input)

        # 提交按钮
        self.submit_button = QPushButton("确定")
        self.submit_button.clicked.connect(self.add_account)
        form_layout.addWidget(self.submit_button)

        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.cancel)  # 连接到取消按钮的槽函数
        form_layout.addWidget(self.cancel_button)

        # 将表单布局添加到主布局
        main_layout.addLayout(form_layout)

        # 连接服务类型选择事件
        self.service_list.currentRowChanged.connect(self.update_form)

    def update_form(self, index):
        """根据选择的服务类型更新表单内容"""
        service = self.service_list.item(index).text()
        if service == "QQ邮箱":
            self.imap_server_input.setText("imap.qq.com")
            self.imap_port_input.setText("993")
        elif service == "网易163邮箱":
            self.imap_server_input.setText("imap.163.com")
            self.imap_port_input.setText("993")
        elif service == "网易126邮箱":
            self.imap_server_input.setText("imap.126.com")
            self.imap_port_input.setText("993")
        elif service == "RUC人大邮箱":
            self.imap_server_input.setText("imap.ruc.edu.cn")
            self.imap_port_input.setText("993")
        elif service == "RUC人大邮箱":
            self.imap_server_input.setText("imap.ruc.edu.cn")
            self.imap_port_input.setText("993")
        elif service == "新浪邮箱":
            self.imap_server_input.setText("imap.sina.com")
            self.imap_port_input.setText("993")
        elif service == "搜狐邮箱":
            self.imap_server_input.setText("imap.sohu.com")
            self.imap_port_input.setText("993")
        elif service == "电信189邮箱":
            self.imap_server_input.setText("imap.189.com")
            self.imap_port_input.setText("993")
        elif service == "Gmail邮箱":
            self.imap_server_input.setText("imap.gmail.com")
            self.imap_port_input.setText("993")
        elif service == "Outlook邮箱":
            self.imap_server_input.setText("(服务变更:暂不支持)Outlook.office365.com")
            self.imap_port_input.setText("993")
        elif service == "其他邮箱":
            # self.imap_server_input.setText("outlook.office365.com")
            self.imap_port_input.setText("993")
        else:  # Custom
            self.imap_server_input.clear()
            self.imap_port_input.clear()

    def add_account(self):
        """处理添加账户的逻辑"""
        email = self.email_input.text()
        password = self.password_input.text()
        imap_server = self.imap_server_input.text()
        imap_port = self.imap_port_input.text()
        remark = self.remark_input.toPlainText()

        if not email.strip():
            MessageDialog().show_error("邮箱账户不能为空！")
            return
        if not password.strip():
            MessageDialog().show_error("请输入密码！")
            return
        if not imap_server.strip():
            MessageDialog().show_error("请输入IMAP服务器域名！")
            return
        if not imap_port.strip():
            print("请输入端口号")
            return

        self.email_account_input = None
        account = EmailAccount(server_address=imap_server, port=imap_port, username=email,
                               password=password, ssl_encryption=True, remarks=remark)
        # 添加账户保存逻辑
        session = SessionManager().get_session()
        manager = EmailAccountManager(session)
        v = manager.get_email_account_by_mail(account.username)
        if v:
            # print(f'账户{v.username}已存在')
            QMessageBox.information(self, "提示", "当前账户已存在！")
        else:
            client_type = ServerUtils.get_client_type(account.username)
            client = IMAPClientFactory.get_client(client_type, account.server_address, account.port,
                                                  account.username, account.password, account.ssl_encryption)
            connection = client.connect()
            if connection:
                manager.add_email_account(account)
                # print(f'{account.username}已添加。')
                QMessageBox.information(self, "成功", "账户添加成功！")
                self.email_account_input = account
            else:
                print(f'连接错误，重新输入。')
                QMessageBox.information(self, "验证错误", "请检查网络状态并输入正确密码！")

        # QMessageBox.information(self, "成功", "账户添加成功！")
        # 关闭表单
        self.parent().accept()

    def cancel(self):
        """处理取消按钮的逻辑"""
        self.parent().reject()  # 关闭对话框并返回取消状态


class EmailAccountDialog(QDialog):
    def __init__(self, parent=None):
        super(EmailAccountDialog, self).__init__(parent)
        self.setWindowTitle("添加邮箱账户")
        # 创建并设置表单
        self.form = EmailAccountForm(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.form)
        self.setLayout(layout)
