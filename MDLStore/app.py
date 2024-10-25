import configparser
import os
import pickle
import sys
import traceback

from PyQt5.QtCore import Qt, QRect, QThreadPool, QSize
from PyQt5.QtGui import QIcon, QGuiApplication, QKeySequence, QFont, QPalette, QColor
from PyQt5.QtWidgets import QMainWindow, QWidget, QTabWidget, QHBoxLayout, QStatusBar, QLabel, QMenu, QStyleFactory, \
    QToolBar, QAction, QShortcut, QApplication, QDesktopWidget, QMessageBox

from MDLStore.UI.HistoryPages import TaskViewer
from MDLStore.core import defaults
from MDLStore.UI.MainApp import MainApp
import MDLStore.images_rc
from MDLStore.database.config_database_setup import SessionManager
from MDLStore.database.service import EmailAccountManager
from MDLStore.ui_utils import APP_Signals

homepath = os.path.expanduser("~")
# module_path = os.path.dirname(os.path.abspath(__file__))
# 确定module_path
if getattr(sys, 'frozen', False):
    module_path = os.path.dirname(sys.executable)
else:
    # 如果是脚本运行，则获取脚本的所在目录
    module_path = os.path.dirname(os.path.abspath(__file__))


stylepath = os.path.join(module_path, 'styles')
iconpath = os.path.join(module_path, 'icons')
config_path = os.path.join(module_path, 'configs')
# pluginiconpath = os.path.join(module_path, 'plugins', 'icons')

splittercss = """QSplitter::handle:hover {
border: 0.1ex dashed #777;
width: 15px;
margin-top: 10px;
margin-bottom: 10px;
border-radius: 4px;
}
"""

dockstyle = '''
    QDockWidget {
        max-width:240px;
    }
    QDockWidget::title {
        background-color: lightblue;
    }
    QScrollBar:vertical {
         width: 15px;
         margin: 1px 0 1px 0;
     }
    QScrollBar::handle:vertical {
         min-height: 20px;
     }
'''

global_thread_pool = QThreadPool.globalInstance()


class Application(QMainWindow):
    def __init__(self, project_file=None, csv_file=None, excel_file=None):
        QMainWindow.__init__(self)
        self.task_viewer = None
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("MDLStore邮件备份工具v1.0")
        # logoicon = os.path.join(module_path, 'logo.png')
        # self.setWindowIcon(QIcon(logoicon))
        self.setWindowIcon(QIcon(':/icons/logo.png'))

        self.createMenu()

        # 获取可用分辨率
        screen_resolution = QGuiApplication.primaryScreen().availableGeometry()
        width, height = int(screen_resolution.width() * 0.8), int(screen_resolution.height() * 0.8)
        if screen_resolution.width() > 1024:
            self.setGeometry(QRect(200, 200, width, height))
        self.setMinimumSize(400, 300)

        # self.main = QWidget(self)
        self.main = MainApp(width, height, self)
        # self.tabs = QTabWidget(self.main)
        layout = QHBoxLayout(self.main)
        # layout.addWidget(self.tabs)

        # 设置键盘输入焦点
        self.main.setFocus()
        self.setCentralWidget(self.main)

        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.proj_label = QLabel("")
        self.statusbar.addWidget(self.proj_label, 1)
        self.proj_label.setStyleSheet('color: blue')
        self.theme = 'Fusion'
        self.font = 'monospace'

        self.recent_files = ['']
        self.recent_urls = []
        self.scratch_items = {}
        self.openplugins = {}

        self.setIconSize(QSize(defaults['ICONSIZE'], defaults['ICONSIZE']))

        self.threadpool = QThreadPool()
        self.center()
        self.init_theme()

    def createMenu(self):

        self.account_menu = QMenu('&账户管理(&A)|', self)

        icon = QIcon(os.path.join(iconpath, 'document-new.png'))
        self.account_menu.addAction(icon, '&添加邮箱账户', lambda: self.addEmailAccount(ask=True),
                                    Qt.CTRL + Qt.Key_N)
        icon = QIcon(os.path.join(iconpath, 'open.png'))
        self.account_menu.addAction(icon, '&编辑邮箱信息', self.editEmailAccount,
                                    Qt.CTRL + Qt.Key_O)

        self.account_menu.addAction('导出账户配置', self.exportAccounts)
        icon = QIcon(os.path.join(iconpath, 'application-exit.png'))
        self.account_menu.addAction(icon, '&退出|', self.fileQuit,
                                    Qt.CTRL + Qt.Key_Q)
        self.menuBar().addMenu(self.account_menu)

        self.task_menu = QMenu('任务管理(&T)|', self)
        self.menuBar().addMenu(self.task_menu)
        self.new_task = self.task_menu.addAction('新建备份任务', self.newBackupTask,
                                                 Qt.CTRL + Qt.Key_Z)

        icon = QIcon(os.path.join(iconpath, 'paste.png'))
        self.task_menu.addAction(icon, '查看任务记录', self.show_task_results)

        self.search_view_menu = QMenu('数据检索(&R)|', self)
        self.menuBar().addMenu(self.search_view_menu)
        icon = QIcon(os.path.join(iconpath, 'zoom-in.png'))
        self.search_view_menu.addAction(icon, '数据概览', self.dataOverview,
                                        Qt.CTRL + Qt.Key_Equal)
        icon = QIcon(os.path.join(iconpath, 'zoom-out.png'))
        self.search_view_menu.addAction(icon, '邮件数据检索', self.EmailRFC2822Search,
                                        Qt.CTRL + Qt.Key_Minus)

        self.theme_menu = QMenu("更换主题(&T)|", self.search_view_menu)
        # group = QActionGroup(self.theme_menu)
        # group.setExclusive(True)
        themes = QStyleFactory.keys()
        for t in themes:
            self.theme_menu.addAction(t, lambda te=t: self.setTheme(te))

        self.theme_menu.addAction('暗色系（Dark）', lambda: self.setTheme('dark'))
        self.theme_menu.addAction('亮色系（Light）', lambda: self.setTheme('light'))
        self.menuBar().addMenu(self.theme_menu)

        self.help_menu = QMenu('&帮助和关于(&H)|', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        # self.help_menu.addAction('查看错误日志', self.showErrorLog)
        url = 'https://www.baidu.cn'
        self.help_menu.addAction('在线帮助', lambda: self.open_url(url))
        icon = QIcon(os.path.join(iconpath, 'logo.png'))
        self.help_menu.addAction(icon, '关于软件', self.about)

        return

    def addDockWidgets(self):
        self
        pass

    # def createToolBar(self):
    #     """Create main toolbar"""
    #
    #     items = {'添加邮箱': {'action': lambda: self.addEmailAccount(ask=True), 'file': 'project-new'},
    #              '编辑邮箱': {'action': self.editEmailAccount, 'file': 'document-open'},
    #              '保存配置': {'action': lambda: self.saveEmailAccount(), 'file': 'save'},
    #              '新建备份任务': {'action': lambda: self.newBackupTask(), 'file': 'add'},
    #              '创建备份计划': {'action': self.newBackupPlan, 'file': 'zoom-out'},
    #              '查看备份历史记录': {'action': self.checkTaskHistory, 'file': 'scratchpad'},
    #              '邮件数据概览': {'action': self.dataOverview, 'file': 'zoom-in'},
    #              'RFC2822邮件检索': {'action': lambda: self.EmailRFC2822Search(), 'file': 'decrease-width'},
    #              '附件文件检索': {'action': lambda: self.AttachFileSearch(), 'file': 'increase-width'},
    #              '在线帮助': {'action': lambda : self.open_url('https://www.baidu.com'), 'file': 'preferences-system'},
    #              '退出': {'action': self.fileQuit, 'file': 'application-exit'}
    #              }
    #
    #     toolbar = QToolBar("Main Toolbar")
    #     self.addToolBar(toolbar)
    #     for i in items:
    #         if 'file' in items[i]:
    #             iconfile = os.path.join(iconpath, items[i]['file'] + '.png')
    #             icon = QIcon(iconfile)
    #         else:
    #             icon = QIcon.fromTheme(items[i]['icon'])
    #         btn = QAction(icon, i, self)
    #         btn.triggered.connect(items[i]['action'])
    #         # btn.setCheckable(True)
    #         toolbar.addAction(btn)
    #     return
    #     pass

    def loadSettings(self):
        pass

    def setTheme(self, theme=None):
        """Change interface theme."""
        app = QApplication.instance()
        if theme == None:
            theme = self.theme
        else:
            self.theme = theme
        app.setStyle(QStyleFactory.create(theme))
        self.setStyleSheet('')
        if theme in ['dark', 'light']:
            f = open(os.path.join(stylepath, '%s.qss' % theme), 'r')
            self.style_data = f.read()
            f.close()
            self.setStyleSheet(self.style_data)
        return

    def addEmailAccount(self, ask=True):
        APP_Signals.jump_page.emit(1)

    def editEmailAccount(self):
        APP_Signals.jump_page.emit(1)

    def saveEmailAccount(self):
        pass

    def exportAccounts(self):
        APP_Signals.jump_page.emit(1)

    def fileQuit(self):
        QApplication.quit()

    def newBackupTask(self):
        APP_Signals.jump_page.emit(2)

    def execBackupTask(self):
        pass

    def cancelBackupTask(self):
        pass

    def checkTaskHistory(self):
        history_ini_path = os.path.join(config_path, 'history.ini')

        # 创建 ConfigParser 对象
        config = configparser.ConfigParser()
        # 读取 ini 文件
        config.read(history_ini_path)
        # 存储所有任务结果的字典
        task_results = {}
        # 遍历所有的任务部分
        for section in config.sections():
            if section.startswith('Task_'):
                task_data_hex = config.get(section, 'task_data')
                result = config.get(section, 'result')
                drive = config.get(section, 'drive')
                # 反序列化 task 对象
                task_data = bytes.fromhex(task_data_hex)
                task = pickle.loads(task_data)
                # 存储结果
                task_results[section] = {
                    'task': task,
                    'result': result,
                    'drive': drive
                }

        return task_results
        # print(task_results)

    def show_task_results(self):
        task_results = self.checkTaskHistory()
        if task_results:
            self.task_viewer = TaskViewer(task_results)
            self.task_viewer.show()
        else:
            QMessageBox.information(self, '信息', '尚未备份，无任务结果！')

    def dataOverview(self):
        APP_Signals.jump_page.emit(3)

    def EmailRFC2822Search(self):
        APP_Signals.jump_page.emit(3)

    def AttachFileSearch(self):
        pass

    def showErrorLog(self):
        pass

    def open_url(self, url):
        import webbrowser
        webbrowser.open(url, autoraise=1)
        return

    def about(self):
        APP_Signals.jump_page.emit(5)

    def newBackupPlan(self):
        pass

    def center(self):
        # 获取屏幕的矩形区域
        screen = QDesktopWidget().availableGeometry()

        # 获取窗口的矩形区域
        window = self.frameGeometry()

        # 将窗口的中心点移动到屏幕的中心点
        window.moveCenter(screen.center())

        # 将窗口移动到屏幕的中心
        self.move(window.topLeft())

    def init_theme(self):

        self.setStyleSheet("""
            QMainWindow {
                background-color: #e7ebee;
            }
            QWidget#central_widget {
                background-color: white;
            }
            """
        )
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #f0f0f0;  /* 设置菜单栏背景色 */
                border: 1px solid #dcdcdc;  /* 设置菜单栏边框 */
            }
            QMenuBar::item {
                width: 120px;  /* 设置菜单项的宽度 */
                height: 40px;  /* 设置菜单项的高度 */
                padding: 10px 10px;  /* 减少上下 padding，适度增加左右 padding */
                background-color: transparent;  /* 默认背景透明 */
            }
            QMenuBar::item:selected { 
                background-color: #a8d8ea;  /* 当菜单项被选中时背景色 */
            }
        """)


def main():
    import sys, os

    from argparse import ArgumentParser
    parser = ArgumentParser()
    # parser.add_argument("-f", "--file", dest="msgpack",
    #                    help="Open a dataframe as msgpack", metavar="FILE")
    parser.add_argument("-p", "--project", dest="project_file",
                        help="Open a dataexplore project file", metavar="FILE")
    parser.add_argument("-i", "--csv", dest="csv_file",
                        help="Import a csv file", metavar="FILE")
    parser.add_argument("-x", "--excel", dest="excel_file",
                        help="Import an excel file", metavar="FILE")
    args = vars(parser.parse_args())

    app = QApplication(sys.argv)
    font = QFont("黑体", 10)  # 设置字体为黑体，字号为10
    app.setFont(font)
    # 启用高 DPI 缩放
    # QGuiApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # QGuiApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    # 禁用 DPI 缩放
    QApplication.setAttribute(Qt.AA_DisableHighDpiScaling)

    aw = Application(**args)
    aw.show()
    app.exec_()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'异常:{e}')
        traceback.print_exc()
