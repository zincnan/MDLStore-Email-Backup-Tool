import configparser
import inspect
import os
import pickle
import traceback
from datetime import timedelta, date, datetime

from PyQt5.QtCore import QVariant, Qt, QDate, QThreadPool, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPainter, QColor
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QMessageBox, QDialogButtonBox, QLabel, QComboBox, \
    QButtonGroup, QGridLayout, QRadioButton, QPushButton

from MDLStore.UI.EmailAccountPages import MyObject
from MDLStore.UI.THEMES import LISTVIEW_TASK_ALL, LISTVIEW_TASK_CUR
from MDLStore.UI.Ui_BackupTaskPage import Ui_BackupTaskPage
from MDLStore.UI.Ui_BackupTaskWidget import Ui_BackupTaskWidget
from MDLStore.database.config_database_setup import SessionManager
from MDLStore.database.entities import BackupTask
from MDLStore.database.service import BackupTaskManager, EmailAccountManager
from MDLStore.dialogs import ProgressWidget, Worker
from MDLStore.execute import backupEmailToTmpArea, extractEmailData, long_running_task
from MDLStore.mailclients import IMAPClientFactory
from MDLStore.storage import StorageManager
from MDLStore.ui_utils import APP_Signals
from MDLStore.utils import ServerUtils

module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.join(module_path, 'configs')

if not os.path.exists(config_path):
    os.makedirs(config_path)

ini_path = os.path.join(config_path, 'history.ini')


class BackupTaskPage(QWidget, Ui_BackupTaskPage):
    def __init__(self, parent=None, *args, **kwargs):
        super(BackupTaskPage, self).__init__(parent, *args, **kwargs)
        self.task_date_to = None
        self.task_date_from = None
        self.target_drive = 'C'
        self.selected_index_cur = None
        self.progress_widget = None
        self.on_change = None
        self.model_all = None
        self.disk_info = None
        self.model_cur = None
        self.all_tasks = None
        self.setupUi(self)
        self.init_ui()
        self.init_theme()

    def init_ui(self):
        self.button_new.clicked.connect(self.show_task_form)
        self.frame.setMinimumWidth(570)  # 设置最小宽度为200像素
        self.comboBox_date.setMinimumHeight(24)

        self.button_add_exec.clicked.connect(self.add_to_cur)
        self.button_del_exec.clicked.connect(self.delete_item_cur)
        self.button_delete.clicked.connect(self.delete_item_all)
        self.init_tasklist()
        self.button_modify.clicked.connect(self.modify_task)

        self.init_date_input()

        self.button_tar.clicked.connect(self.show_disk_selection_dialog)
        self.button_exec.clicked.connect(self.start_exec_backup_task)

        # self.label_date_to.setFixedWidth(10)
        # self.comboBox_date.setFixedWidth(120)
        self.label_cur2all.setAlignment(Qt.AlignCenter)
        self.label_all2cur.setAlignment(Qt.AlignCenter)

    def init_theme(self):
        self.listView_all.setFocusPolicy(Qt.NoFocus)
        self.listView_all.setStyleSheet(LISTVIEW_TASK_ALL)
        self.listView_cur.setFocusPolicy(Qt.NoFocus)
        self.listView_cur.setStyleSheet(LISTVIEW_TASK_CUR)

    def init_tasklist(self):
        self.model_all = QStandardItemModel()

        session = SessionManager().get_session()
        manager = BackupTaskManager(session)
        tasks_list = manager.get_all_backup_tasks()
        # self.all_tasks = [
        #     MyObject("Object 1", 10),
        #     MyObject("Object 2", 20),
        #     MyObject("Object 3", 30),
        #     MyObject("Object 4", 40),
        #     MyObject("Object 5", 50)
        # ]

        self.all_tasks = tasks_list
        self.model_cur = QStandardItemModel()
        self.cur_tasks = []

        self.populate_list_all()
        self.populate_list_cur()

        self.listView_all.clicked.connect(self.on_item_clicked_all)
        self.listView_cur.clicked.connect(self.on_item_clicked_cur)

    def on_item_clicked_all(self, index):
        self.listView_cur.clearSelection()
        self.selected_index_cur = None

        self.selected_index_all = index
        item = self.model_all.itemFromIndex(index)
        text = item.text()
        print(f"Clicked item: {text}")
        obj = item.data(Qt.UserRole)  # 获取存储的对象
        # print(f"Object name: {obj.name}, Object value: {obj.value}")
        print(obj)
        self.display_task(obj)

    def on_item_clicked_cur(self, index):
        self.listView_all.clearSelection()
        self.selected_index_all = None

        self.selected_index_cur = index
        item = self.model_cur.itemFromIndex(index)
        text = item.text()
        print(f"Clicked item: {text}")
        obj = item.data(Qt.UserRole)  # 获取存储的对象
        # print(f"Object name: {obj.name}, Object value: {obj.value}")
        # print(obj)
        self.display_task(obj)

    def delete_item_all(self):
        index_delete = self.selected_index_all

        if self.selected_index_all is not None:
            item = self.model_all.itemFromIndex(self.selected_index_all)
            obj = item.data(Qt.UserRole)
            if obj in self.all_tasks:
                # 删除任务
                session = SessionManager().get_session()
                manager = BackupTaskManager(session)
                manager.delete_backup_task(obj.task_id)

                self.all_tasks.remove(obj)  # 从对象列表中删除对象
                # print(f"Deleted item: {obj}")
                self.populate_list_all()  # 更新视图
                # self.selected_index_all = None  # 清除选中状态

            row_to_select = index_delete.row()  # 获取删除项的行号
            new_index_row = max(0, row_to_select - 1)  # 新索引最小为0

            # 如果列表中还有剩余项，则选中新的索引
            if self.all_tasks:
                new_selected_item = self.model_all.index(new_index_row, 0)
                self.listView_all.setCurrentIndex(new_selected_item)  # 选中新索引项
                self.selected_index_all = new_selected_item
            else:
                self.selected_index_all = None  # 如果没有剩余项，清除选中状态

    def delete_item_cur(self):
        index_delete = self.selected_index_cur

        if self.selected_index_cur is not None:
            item = self.model_cur.itemFromIndex(self.selected_index_cur)
            obj = item.data(Qt.UserRole)
            if obj in self.cur_tasks:
                self.cur_tasks.remove(obj)  # 从对象列表中删除对象
                # print(f"Deleted item: {obj}")
                self.populate_list_cur()  # 更新视图
            # self.selected_index_cur = None  # 清除选中状态

            row_to_select = index_delete.row()  # 获取删除项的行号
            new_index_row = max(0, row_to_select - 1)  # 新索引最小为0

            # 如果列表中还有剩余项，则选中新的索引
            if self.cur_tasks:
                new_selected_item = self.model_cur.index(new_index_row, 0)
                self.listView_cur.setCurrentIndex(new_selected_item)  # 选中新索引项
                self.selected_index_cur = new_selected_item
            else:
                self.selected_index_cur = None  # 如果没有剩余项，清除选中状态

    def add_to_cur(self):
        if self.selected_index_all is None:
            # 自定义消息弹窗
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)  # 设置为警告图标（叹号）
            msg_box.setWindowTitle("警告")
            msg_box.setText("请从左侧选择后再添加！")
            # 创建自定义按钮
            custom_button = QPushButton("确定")  # 自定义按钮文字为“确定”
            msg_box.addButton(custom_button, QMessageBox.AcceptRole)  # 将按钮添加到提示框中
            msg_box.exec_()

            return
        item = self.model_all.itemFromIndex(self.selected_index_all)
        text = item.text()
        # print(f"Clicked item: {text}")
        obj = item.data(Qt.UserRole)  # 获取存储的对象
        if obj not in self.cur_tasks:
            self.cur_tasks.append(obj)
            self.populate_list_cur()

    def populate_list_all(self):
        self.model_all.clear()  # 清空模型
        for obj in self.all_tasks:
            text_task = obj.task_name
            item = QStandardItem(text_task)  # 设置显示的文本
            item.setData(QVariant(obj), Qt.UserRole)  # 存储对象
            self.model_all.appendRow(item)  # 逐个添加项
        self.listView_all.setModel(self.model_all)  # 设置模型到 QListView
        self.selected_index_all = None

    def populate_list_cur(self):
        self.model_cur.clear()  # 清空模型
        for obj in self.cur_tasks:
            text_task = obj.task_name
            item = QStandardItem(text_task)  # 设置显示的文本
            item.setData(QVariant(obj), Qt.UserRole)  # 存储对象
            self.model_cur.appendRow(item)  # 逐个添加项
        self.listView_cur.setModel(self.model_cur)  # 设置模型到 QListView
        self.selected_index_cur = None

    def show_task_form(self):
        dialog = BackupTaskDialog(self)
        print("显示窗口")
        if dialog.exec_() == QDialog.Accepted:
            # 处理表单数据
            form = dialog.form
            # obj = form.get_selected_account_object()
            # print(obj)
            # print(form.lineEdit_from.text(), form.lineEdit_filename.text(), form.lineEdit_subject.text(),
            # form.task_date_from)
            # new_obj = MyObject("test", 66)
            new_obj = form.new_task_object
            print(f'执行到此处：当前文件是 {__file__}，行号 {inspect.currentframe().f_lineno}')
            print(new_obj)
            self.all_tasks.append(new_obj)
            self.populate_list_all()

    def modify_task(self):
        # if self.listView_all.selectionModel().hasSelection():
        #     self.modify_all()
        #     # 检查 listView_cur 是否有选中的项
        # elif self.listView_cur.selectionModel().hasSelection():
        #     self.modify_cur()
        if self.selected_index_all:
            self.modify_all()
        elif self.selected_index_cur:
            self.modify_cur()

    def modify_all(self):
        new_obj = MyObject('all', 150)

        # 获取选中项对应的对象
        item = self.model_all.itemFromIndex(self.selected_index_all)
        old_obj = item.data(Qt.UserRole)

        if old_obj in self.all_tasks:
            index = self.all_tasks.index(old_obj)
            self.all_tasks[index] = new_obj  # 替换成新对象
            # print(f"Replaced {old_obj} with {new_obj}")
        # 更新视图
        self.populate_list_all()

    def modify_cur(self):
        new_obj = MyObject('cur', 140)
        # 获取选中项对应的对象
        item = self.model_cur.itemFromIndex(self.selected_index_cur)
        old_obj = item.data(Qt.UserRole)

        if old_obj in self.cur_tasks:
            index = self.cur_tasks.index(old_obj)
            self.cur_tasks[index] = new_obj  # 替换成新对象
            # print(f"Replaced {old_obj} with {new_obj}")
        # 更新视图
        self.populate_list_cur()

    def init_date_input(self):
        self.dateEdit_start.hide()
        self.dateEdit_end.hide()
        self.label_date_to.hide()
        self.comboBox_date.currentIndexChanged.connect(self.on_combobox_changed)
        self.dateEdit_start.setCalendarPopup(True)  # 启用日历弹出窗口
        # self.dateEdit_start.setReadOnly(True)
        self.dateEdit_start.setGeometry(50, 50, 150, 30)  # 设置位置和大
        self.dateEdit_end.setCalendarPopup(True)  # 启用日历弹出窗口
        # self.dateEdit_end.setReadOnly(True)
        self.dateEdit_end.setGeometry(50, 100, 150, 30)  # 设置位置和大小

        calendar_start = self.dateEdit_start.calendarWidget()
        calendar_end = self.dateEdit_end.calendarWidget()
        calendar_start.clicked.connect(self.on_date_start_selected)
        calendar_end.clicked.connect(self.on_date_end_selected)

        self.get_task_date_range('一周内')

    def on_combobox_changed(self, index):
        selected_text = self.comboBox_date.itemText(index)
        # 根据选中的选项执行不同的操作
        if selected_text == "自定义时间段":
            self.show_date_start_and_end()
        # elif selected_text == "一周内":
        #     self.do_action_2()
        # elif selected_text == "半个月内":
        #     self.do_action_3()
        # elif selected_text == "一个月内":
        #     self.do_action_3()
        # elif selected_text == "三个月内":
        #     self.do_action_3()
        # elif selected_text == "半年内":
        #     self.do_action_3()
        # elif selected_text == "半年内":
        #     self.do_action_3()
        else:
            self.get_task_date_range(selected_text)

    def show_date_start_and_end(self):
        self.dateEdit_start.show()
        self.dateEdit_end.show()
        self.label_date_to.show()

        today = QDate.currentDate()
        # 将 QDateEdit 的日期设置为当前日期
        self.dateEdit_start.setDate(today)
        self.dateEdit_end.setDate(today)

        start_qdate = self.dateEdit_start.date()
        end_qdate = self.dateEdit_end.date()

        # 将 QDate 对象转换为 Python 的 date 对象
        start_date = start_qdate.toPyDate()
        end_date = end_qdate.toPyDate()

        self.task_date_from = start_date
        self.task_date_to = end_date

    def on_date_start_selected(self):
        # 获取选定的日期
        start_date = self.dateEdit_start.date().toPyDate()
        # end_date = self.dateEdit_end.date().toPyDate()
        self.task_date_from = start_date
        # self.task_date_to = end_date
        print(f"Start Date: {start_date}")
        # print(f"End Date: {end_date}")
        self.dateEdit_start.clearFocus()

    def on_date_end_selected(self):
        end_date = self.dateEdit_end.date().toPyDate()
        # self.task_date_from = start_date
        self.task_date_to = end_date
        # print(f"Start Date: {start_date}")
        print(f"End Date: {end_date}")
        self.dateEdit_end.clearFocus()

    def get_task_date_range(self, selected_text):
        self.dateEdit_start.hide()
        self.dateEdit_end.hide()
        self.label_date_to.hide()

        self.task_date_to = date.today()  # 设为今天的日期

        # 根据选中的文本设置对应的起始日期
        if selected_text == "一周内":
            self.task_date_from = self.task_date_to - timedelta(weeks=1)
        elif selected_text == "半个月内":
            self.task_date_from = self.task_date_to - timedelta(days=15)
        elif selected_text == "一个月内":
            self.task_date_from = self.task_date_to - timedelta(days=30)
        elif selected_text == "三个月内":
            self.task_date_from = self.task_date_to - timedelta(days=90)
        elif selected_text == "半年内":
            self.task_date_from = self.task_date_to - timedelta(days=180)
        elif selected_text == "一年内":
            self.task_date_from = self.task_date_to - timedelta(days=365)
        # 打印日期（可选）
        # print(f"From: {self.task_date_from}, To: {self.task_date_to}")

    def display_task(self, task):

        self.lineEdit_account.clear()
        self.lineEdit_folders.clear()
        self.dateEdit_start.clear()
        self.dateEdit_end.clear()
        self.comboBox_date.setCurrentIndex(-1)  # 清空下拉框的选择
        self.checkBox.setChecked(False)
        self.checkBox_2.setChecked(False)
        self.checkBox_3.setChecked(False)
        self.lineEdit_from.clear()
        self.lineEdit_subject.clear()
        self.lineEdit_filename.clear()

        session = SessionManager().get_session()
        email_account_manager = EmailAccountManager(session)
        email_account_id = task.email_account_id
        folder_list = task.folder_list
        folders = pickle.loads(folder_list)
        start_date = task.start_date
        end_date = task.end_date
        content_type = task.content_type
        sender = task.sender
        subject_keywords = task.subject_keywords
        filename_keywords = task.filename_keywords
        email_account = email_account_manager.get_email_account_by_id(email_account_id)

        try:
            self.lineEdit_account.setText(email_account.username)
            self.lineEdit_folders.setText('; '.join(folders))
            self.dateEdit_start.show()
            self.dateEdit_end.show()
            self.label_date_to.show()
            self.comboBox_date.setCurrentText('自定义时间段')
            start_qdate = QDate(start_date.year, start_date.month, start_date.day)
            end_qdate = QDate(end_date.year, end_date.month, end_date.day)
            # 设置 QDateEdit 的日期
            self.dateEdit_start.setDate(start_qdate)
            self.dateEdit_end.setDate(end_qdate)

            if 'RFC2822' in content_type:
                self.checkBox.setChecked(True)
            if 'Attachment' in content_type:
                self.checkBox_2.setChecked(True)
            if 'CloudAttach' in content_type:
                self.checkBox_3.setChecked(True)

            self.lineEdit_from.setText(sender)
            self.lineEdit_subject.setText(subject_keywords)
            self.lineEdit_filename.setText(filename_keywords)
        except Exception as e:
            print(f'ERR:{e}')
            traceback.print_exc()

    def show_disk_selection_dialog(self):
        self.disk_info = StorageManager().get_disk_info()
        dialog = DiskSelectionDialog(self.disk_info, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_disk = dialog.get_selected_disk()
            if selected_disk:
                self.target_drive = selected_disk['device'][0]
                # print(f"您选择了磁盘分区: {selected_disk['device']}，容量: {self.bytes_to_gb(selected_disk['total'])}")
                self.lineEdit_7.setText(f'磁盘分区：{self.target_drive}')

    def bytes_to_gb(self, bytes_value):
        """将字节数转换为 GB 并保留两位小数"""
        return f"{bytes_value / (1024 ** 3):.2f} GB"

    def start_exec_backup_task(self):
        if not self.target_drive:
            QMessageBox.warning(self, "提示", "请选择备份位置！")
            print(f'备份位置未选择')
            return

        if not self.cur_tasks:  # 检查列表是否为空
            QMessageBox.warning(self, "提示", "请选择需要执行的备份任务")
            print(f'待备份任务列表为空')
            return

        print(f'运行任务')

        self.on_change = self.radioButton.isChecked()

        session = SessionManager().get_session()
        # account_manager = EmailAccountManager(session)
        print(f'当前任务列表{self.cur_tasks}')
        self.progress_widget = ProgressWidget(label="备份任务执行...")
        worker = Worker(long_running_task, self.cur_tasks, self.target_drive, self.on_change)
        worker.signals.progress.connect(self.update_progress)
        worker.signals.detail.connect(self.update_detail)
        worker.signals.info.connect(self.update_info)
        worker.signals.result.connect(self.task_result)
        worker.signals.finished.connect(self.task_finished)
        worker.signals.error.connect(self.task_error)
        # 启动任务
        QThreadPool.globalInstance().start(worker)

    @staticmethod
    def load_task_from_ini(ini_file, task_id):
        """从指定的 ini 文件中加载 task 对象"""
        config = configparser.ConfigParser()
        config.read(ini_file)
        task_section = f"Task_{task_id}"
        if config.has_section(task_section):
            serialized_task_hex = config.get(task_section, "task_data")
            serialized_task = bytes.fromhex(serialized_task_hex)  # 从十六进制字符串恢复为字节流
            task = pickle.loads(serialized_task)  # 反序列化为 task 对象
            return task
        return None

    def update_progress(self, n):
        self.progress_widget.progressbar.setValue(n)

    def update_detail(self, detail):
        self.progress_widget.detail_label.setText(detail)

    def update_info(self, info):
        self.progress_widget.info_label.setText(info)

    def task_result(self, result):
        print(f"Result: {result}")

    def task_finished(self):
        # self.progress_widget.close()
        print("Task 结束!")

        self.progress_widget.progressbar.setValue(100)
        # 更改进度条的文本格式，显示 "已完成"
        self.progress_widget.progressbar.setFormat("已完成")
        self.progress_widget.info_label.setText('备份任务已完成')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.progress_widget.detail_label.setText(f'任务完成时间:{current_time}')
        APP_Signals.flush_storage_infos.emit()
        # # 延迟几秒钟后自动关闭窗口
        QTimer.singleShot(5000, self.progress_widget.close)  # 3000 毫秒 = 3 秒

    def task_error(self, error_tuple):
        exctype, value, tb_str = error_tuple
        print(f"Error: {value}\n{tb_str}")


class BackupTaskWidget(QWidget, Ui_BackupTaskWidget):
    def __init__(self, parent=None, *args, **kwargs):
        super(BackupTaskWidget, self).__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.init_ui()

    def init_ui(self):
        self.button_add.clicked.connect(self.on_add_clicked)
        self.button_cancel.clicked.connect(self.on_cancel_clicked)
        self.init_date_input()
        self.init_email_account()
        self.init_folders_input()

    def on_add_clicked(self):
        """
        添加备份任务
        :return:
        """
        # 获取文件夹状态
        self.folders = self.get_checked_folders()
        print(f'文件夹列表{self.folders}')
        folder_list = self.folders

        # 左闭右闭区间，时间
        start_date = self.task_date_from
        end_date = self.task_date_to
        content_type = self.get_content_type()
        sender = self.lineEdit_from.text()
        subject_keywords = self.lineEdit_subject.text()
        filename_keywords = self.lineEdit_filename.text()
        # 输入或选择文件名
        task_name = self.lineEdit_taskname.text()

        if not task_name:
            QMessageBox.warning(self, "输入错误", "任务名称不能为空！")
            return

        if not folder_list or len(folder_list) == 0:
            QMessageBox.warning(self, "输入错误", "文件夹列表不能为空！")
            return

        if content_type is None or content_type == '':
            QMessageBox.warning(self, "输入错误", "请勾选备份数据类型！")
            return

        email_account = self.get_selected_account_object()
        new_backup_task = BackupTask(
            email_account_id=email_account.account_id,  # 关联的邮箱账户ID
            folder_list=pickle.dumps(folder_list),  # 要备份的邮箱文件夹列表
            start_date=start_date,  # 备份的开始日期
            end_date=end_date,  # 备份的结束日期
            content_type=content_type,  # 备份内容类型
            sender=sender,  # 发件人过滤条件
            subject_keywords=subject_keywords,  # 主题关键字过滤条件
            filename_keywords=filename_keywords,  # 文件名关键字过滤条件
            task_name=task_name  # 备份任务名称
        )

        session = SessionManager().get_session()
        backup_manager = BackupTaskManager(session)

        # print(backup_manager.check_tasks_with_same_name(task_name))

        if backup_manager.check_tasks_with_same_name(task_name):
            # 弹出确认对话框
            reply = QMessageBox.question(
                self,
                "确认添加",
                f"已经存在名称为 '{task_name}' 的备份任务。是否仍要添加此任务？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            # 如果用户点击“否”，则不添加任务
            if reply == QMessageBox.No:
                return

        self.new_task_object = backup_manager.add_backup_task(new_backup_task)
        QMessageBox.information(self, "成功", "备份任务添加成功")
        self.parent().accept()  # 关闭对话框并返回接受状态

    def on_cancel_clicked(self):
        self.parent().reject()  # 关闭对话框并返回拒绝状态

    def init_date_input(self):
        self.dateEdit_start.hide()
        self.dateEdit_end.hide()
        self.label_date.hide()
        self.get_task_date_range('一周内')

        self.comboBox_date.currentIndexChanged.connect(self.on_combobox_date_changed)

        self.dateEdit_start.setCalendarPopup(True)  # 启用日历弹出窗口
        # self.dateEdit_start.setReadOnly(True)
        self.dateEdit_start.setGeometry(50, 50, 150, 30)  # 设置位置和大
        self.dateEdit_end.setCalendarPopup(True)  # 启用日历弹出窗口
        # self.dateEdit_end.setReadOnly(True)
        self.dateEdit_end.setGeometry(50, 100, 150, 30)  # 设置位置和大小

        calendar_start = self.dateEdit_start.calendarWidget()
        calendar_end = self.dateEdit_end.calendarWidget()
        calendar_start.clicked.connect(self.on_date_start_selected)
        calendar_end.clicked.connect(self.on_date_end_selected)

    def get_task_date_range(self, selected_text):
        self.dateEdit_start.hide()
        self.dateEdit_end.hide()
        self.label_date.hide()

        self.task_date_to = date.today()  # 设为今天的日期

        # 根据选中的文本设置对应的起始日期
        if selected_text == "一周内":
            self.task_date_from = self.task_date_to - timedelta(weeks=1)
        elif selected_text == "半个月内":
            self.task_date_from = self.task_date_to - timedelta(days=15)
        elif selected_text == "一个月内":
            self.task_date_from = self.task_date_to - timedelta(days=30)
        elif selected_text == "三个月内":
            self.task_date_from = self.task_date_to - timedelta(days=90)
        elif selected_text == "半年内":
            self.task_date_from = self.task_date_to - timedelta(days=180)
        elif selected_text == "一年内":
            self.task_date_from = self.task_date_to - timedelta(days=365)
        # 打印日期（可选）
        print(f"From: {self.task_date_from}, To: {self.task_date_to}")

    def on_combobox_date_changed(self, index):
        selected_text = self.comboBox_date.itemText(index)
        # 根据选中的选项执行不同的操作
        if selected_text == "自定义时间段":
            self.show_date_start_and_end()
        # elif selected_text == "一周内":
        #     self.do_action_2()
        # elif selected_text == "半个月内":
        #     self.do_action_3()
        # elif selected_text == "一个月内":
        #     self.do_action_3()
        # elif selected_text == "三个月内":
        #     self.do_action_3()
        # elif selected_text == "半年内":
        #     self.do_action_3()
        # elif selected_text == "半年内":
        #     self.do_action_3()
        else:
            self.get_task_date_range(selected_text)

    def show_date_start_and_end(self):
        self.dateEdit_start.show()
        self.dateEdit_end.show()
        self.label_date.show()

        today = QDate.currentDate()
        # 将 QDateEdit 的日期设置为当前日期
        self.dateEdit_start.setDate(today)
        self.dateEdit_end.setDate(today)

        start_qdate = self.dateEdit_start.date()
        end_qdate = self.dateEdit_end.date()

        # 将 QDate 对象转换为 Python 的 date 对象
        start_date = start_qdate.toPyDate()
        end_date = end_qdate.toPyDate()
        self.task_date_from = start_date
        self.task_date_to = end_date

    def on_date_start_selected(self):
        # 获取选定的日期
        start_date = self.dateEdit_start.date().toPyDate()
        # end_date = self.dateEdit_end.date().toPyDate()
        self.task_date_from = start_date
        # self.task_date_to = end_date
        print(f"Start Date: {start_date}")
        # print(f"End Date: {end_date}")
        self.dateEdit_start.clearFocus()

    def on_date_end_selected(self):
        end_date = self.dateEdit_end.date().toPyDate()
        # self.task_date_from = start_date
        self.task_date_to = end_date
        # print(f"Start Date: {start_date}")
        print(f"End Date: {end_date}")
        self.dateEdit_end.clearFocus()

    def init_folders_input(self):

        # 创建树模型和根节点
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['邮箱文件夹'])

        # 添加根文件夹（邮箱地址）
        # self.root_item = QStandardItem(email_address)
        self.root_item = QStandardItem('email_address')
        self.root_item.setCheckable(True)
        self.model.appendRow(self.root_item)

        # # 构建文件夹结构树
        # folder_items = {}
        # for folder in folders:
        #     parts = folder.split('/')
        #     parent_item = self.root_item
        #
        #     for part in parts:
        #         if part not in folder_items:
        #             item = QStandardItem(part)
        #             item.setCheckable(True)
        #             parent_item.appendRow(item)
        #             folder_items[part] = item
        #         parent_item = folder_items[part]

        # 创建 QTreeView 并设置模型
        self.treeView.setModel(self.model)
        self.treeView.expandAll()  # 展开所有节点
        self.treeView.setGeometry(50, 50, 300, 400)

        # 连接模型的 itemChanged 信号
        self.model.itemChanged.connect(self.on_item_folder_changed)

        # 设置主窗口属性
        self.setGeometry(100, 100, 400, 500)
        self.setWindowTitle("Email Folders")

        self.refresh_folders_input()

    def refresh_folders_input(self):
        email_account = self.get_selected_account_object()
        email_address = email_account.username

        self.root_item.setText(email_address)
        self.root_item.setCheckState(False)

        # 获取新的文件夹结构
        client_type = ServerUtils.get_client_type(email_account.username)
        client = IMAPClientFactory.get_client(client_type, email_account.server_address, email_account.port,
                                              email_account.username, email_account.password,
                                              email_account.ssl_encryption)

        connection = client.connect()
        if connection:
            client.login()
            mail_boxs = client.get_mailbox_list()
            print(f'邮箱文件夹：{type(mail_boxs)}\n内容：{mail_boxs}')
            folders = mail_boxs
            # print(folders)
        else:
            folders = ['收件箱', '已发送', '收件箱/子文件夹1', '收件箱/子文件夹2', 'test', 'test/test1']

        # 清空当前的树结构（只保留根节点）
        self.root_item.removeRows(0, self.root_item.rowCount())

        # 重建文件夹结构树
        self.build_folder_tree(folders)

    def build_folder_tree(self, folders):
        folder_items = {}
        for folder in folders:
            # 去掉文件夹名称中的引号
            folder = folder.strip('"')

            parts = folder.split('/')
            parent_item = self.root_item

            for part in parts:
                if part not in folder_items:
                    item = QStandardItem(part)
                    item.setCheckable(True)
                    parent_item.appendRow(item)
                    folder_items[part] = item
                parent_item = folder_items[part]

    def on_item_folder_changed(self, item):
        if item.checkState() == Qt.Checked:
            # 如果文件夹被选中，递归选中所有子文件夹
            self.set_children_check_state(item, Qt.Checked)
            # 更新父文件夹的状态
            self.update_parent_check_state(item)
        elif item.checkState() == Qt.Unchecked:
            # 如果文件夹取消选中，取消选中所有子文件夹
            self.set_children_check_state(item, Qt.Unchecked)

    def set_children_check_state(self, item, check_state):
        # 递归设置子节点的勾选状态
        for i in range(item.rowCount()):
            child_item = item.child(i)
            child_item.setCheckState(check_state)
            self.set_children_check_state(child_item, check_state)

    def update_parent_check_state(self, item):
        parent_item = item.parent()
        if parent_item is not None:
            checked_children = 0
            for i in range(parent_item.rowCount()):
                child_item = parent_item.child(i)
                if child_item.checkState() == Qt.Checked:
                    checked_children += 1

            if checked_children == parent_item.rowCount():
                parent_item.setCheckState(Qt.Checked)
            else:
                parent_item.setCheckState(Qt.PartiallyChecked)

            # 递归地更新祖先节点的状态
            self.update_parent_check_state(parent_item)

    # def get_checked_folders(self):
    #     checked_folders = []
    #     self._collect_checked_items(self.root_item, "", checked_folders)
    #
    #     # 删除邮箱地址和第一个斜杠
    #     trimmed_folders = [folder.replace(f"{self.root_item.text()}/", "", 1) for folder in checked_folders]
    #
    #     # 为每个文件夹添加双引号
    #     quoted_folders = [f'"{folder}"' for folder in trimmed_folders]
    #     # print(f'选中文件夹{quoted_folders}')
    #
    #     return quoted_folders
    def get_checked_folders(self):
        checked_folders = []
        self._collect_checked_items(self.root_item, "", checked_folders)

        # 获取根节点的文本，假设根节点的文本是邮箱地址
        root_text = self.root_item.text()

        # 删除邮箱地址和第一个斜杠
        trimmed_folders = []
        for folder in checked_folders:
            # 如果不是根节点的邮箱地址，则处理该文件夹路径
            if folder != root_text:
                trimmed_folder = folder.replace(f"{root_text}/", "", 1)
                trimmed_folders.append(trimmed_folder)

        # 为每个文件夹添加双引号
        quoted_folders = [f'"{folder}"' for folder in trimmed_folders]

        return quoted_folders

    def _collect_checked_items(self, item, path, checked_folders):
        # 更新当前路径
        current_path = path + "/" + item.text() if path else item.text()

        # 如果当前项目被选中，记录路径
        if item.checkState() == Qt.Checked:
            checked_folders.append(current_path)

        # 递归处理子节点
        for i in range(item.rowCount()):
            child_item = item.child(i)
            self._collect_checked_items(child_item, current_path, checked_folders)

    def init_email_account(self):
        self.comboBox_acc.currentIndexChanged.connect(self.on_combobox_account_changed)
        session = SessionManager().get_session()
        manager = EmailAccountManager(session)
        email_list = manager.get_all_email_account()
        objects = email_list
        # objects = [
        #     MyObject("User1", "user1@example.com"),
        #     MyObject("User2", "user2@example.com"),
        #     MyObject("User3", "user3@example.com")
        # ]
        for obj in objects:
            self.comboBox_acc.addItem(str(obj.username))
            self.comboBox_acc.setItemData(self.comboBox_acc.count() - 1, obj)

    def get_selected_account_object(self):
        # 获取当前选中的对象
        index = self.comboBox_acc.currentIndex()
        selected_obj = self.comboBox_acc.itemData(index)
        return selected_obj

    def get_content_type(self):
        selected_types = []
        # 检查每个 QCheckBox 的选中状态并添加对应的类型字符串
        if self.checkBox_rfc.isChecked():
            selected_types.append("RFC2822")

        if self.checkBox_att.isChecked():
            selected_types.append("Attachment")

        if self.checkBox_cloud.isChecked():
            selected_types.append("CloudAttach")

        # 将类型字符串列表转换为逗号分隔的字符串
        return ",".join(selected_types)

    def on_combobox_account_changed(self, index):
        if index >= 0:  # 确保选择了有效的项目
            selected_obj = self.comboBox_acc.itemData(index)
            if selected_obj:
                # print(selected_obj)
                self.refresh_folders_input()


class BackupTaskDialog(QDialog):
    def __init__(self, parent=None):
        super(BackupTaskDialog, self).__init__(parent)
        self.setWindowTitle("添加备份任务")
        # 创建并设置表单
        self.form = BackupTaskWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.form)
        self.setLayout(layout)


class DiskUsageBar(QWidget):
    def __init__(self, percent_used, parent=None):
        super(DiskUsageBar, self).__init__(parent)
        self.percent_used = percent_used

        # 设置固定高度
        self.setFixedHeight(20)

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        # 绘制已使用空间（蓝色）
        used_rect = rect.adjusted(0, 0, -rect.width() * (1 - self.percent_used / 100), 0)
        painter.fillRect(used_rect, QColor(0, 120, 215))  # Windows 蓝色

        # 绘制未使用空间（灰色）
        free_rect = rect.adjusted(used_rect.width(), 0, 0, 0)
        painter.fillRect(free_rect, QColor(192, 192, 192))  # 浅灰色

class DiskWidget(QWidget):
    def __init__(self, disk_info, parent=None):
        super(DiskWidget, self).__init__(parent)

        self.disk_info = disk_info
        layout = QGridLayout(self)

        # 添加选择的单选按钮
        self.radio_button = QRadioButton(self)
        layout.addWidget(self.radio_button, 0, 0)

        # 显示磁盘名称和挂载点
        disk_label = QLabel(f"逻辑分区 {disk_info['device']}:/", self)
        layout.addWidget(disk_label, 0, 1)

        # 使用垂直布局放置矩形条和文本标签
        vbox = QVBoxLayout()

        # 显示磁盘使用情况的矩形条
        usage_bar = DiskUsageBar(disk_info['percent_used'])
        vbox.addWidget(usage_bar)

        # 显示进度条下方的文本内容
        progress_label = QLabel(
            f"{disk_info['percent_used']}% 已用 ({self.bytes_to_gb(disk_info['used'])}/{self.bytes_to_gb(disk_info['total'])})",
            self)
        progress_label.setAlignment(Qt.AlignCenter)  # 使文本居中
        vbox.addWidget(progress_label)

        # 将垂直布局添加到网格布局中
        layout.addLayout(vbox, 0, 2)

        # 显示剩余空间
        free_space_label = QLabel(f"剩余: {self.bytes_to_gb(disk_info['free'])}", self)
        layout.addWidget(free_space_label, 0, 3)

        # 设置各列的固定宽度
        layout.setColumnMinimumWidth(0, 40)  # 为单选按钮设置一个较小的宽度
        layout.setColumnMinimumWidth(1, 120) # 为磁盘名称设置一个固定宽度
        layout.setColumnStretch(2, 1)        # 确保矩形条和标签有足够空间
        layout.setColumnMinimumWidth(3, 150) # 为剩余空间设置一个固定宽度

    def bytes_to_gb(self, bytes_value):
        """将字节数转换为 GB 并保留两位小数"""
        return f"{bytes_value / (1024 ** 3):.2f} GB"

    def is_selected(self):
        """检查这个磁盘是否被选中"""
        return self.radio_button.isChecked()


class DiskSelectionDialog(QDialog):
    def __init__(self, disk_info, parent=None):
        super(DiskSelectionDialog, self).__init__(parent)

        self.setWindowTitle("选择磁盘分区")

        layout = QVBoxLayout(self)
        self.button_group = QButtonGroup(self)

        self.disk_widgets = []
        for i, disk in enumerate(disk_info):
            disk_widget = DiskWidget(disk)
            layout.addWidget(disk_widget)
            self.disk_widgets.append(disk_widget)
            self.button_group.addButton(disk_widget.radio_button, i)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # 自定义按钮上的文字
        ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        cancel_button = self.buttonBox.button(QDialogButtonBox.Cancel)
        ok_button.setText("确定")
        cancel_button.setText("取消")

        layout.addWidget(self.buttonBox)

    def get_selected_disk(self):
        """返回用户选中的磁盘信息"""
        for disk_widget in self.disk_widgets:
            if disk_widget.is_selected():
                return disk_widget.disk_info
        return None

