from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt

from MDLStore.database.config_database_setup import SessionManager
from MDLStore.database.service import EmailAccountManager


class TaskViewer(QDialog):
    def __init__(self, task_results, parent=None):
        super().__init__(parent)
        self.text_browser = None
        self.task_results = task_results
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("备份任务执行结果")
        self.setMinimumSize(800, 600)  # 设置窗口的最小尺寸

        layout = QVBoxLayout()

        # 创建 QTextBrowser 以显示任务结果
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)  # 允许点击链接打开外部浏览器

        if not self.task_results:
            self.text_browser.setHtml("<p>尚未备份，无任务结果！</p>")
        else:
            # 设置表头
            result_text = """
            <h3 style='text-align: center; color: #333;'>备份任务执行结果</h3>
            <br>  <!-- 添加空行 -->
            <div style='display: flex; justify-content: center;'>
                <table style='width: 80%; border-collapse: collapse; background-color: #f9f9f9;'>
                    <thead>
                        <tr style='background-color: #e0e0e0;'>
                            <th style='border: 1px solid #ddd; padding: 8px; text-align: center;'>编号</th>
                            <th style='border: 1px solid #ddd; padding: 8px; text-align: center;'>备份任务名称</th>
                            <th style='border: 1px solid #ddd; padding: 8px; text-align: center;'>备份类型</th>
                            <th style='border: 1px solid #ddd; padding: 8px; text-align: center;'>备份邮箱地址</th>
                            <th style='border: 1px solid #ddd; padding: 8px; text-align: center;'>目标存储磁盘</th>
                            <th style='border: 1px solid #ddd; padding: 8px; text-align: center;'>执行结果</th>
                        </tr>
                    </thead>
                    <tbody>
            """

            for index, (task_key, task_info) in enumerate(self.task_results.items()):
                task = task_info['task']
                result = task_info['result']
                drive = task_info['drive']
                email_address_id = task.email_account_id

                # 从 SessionManager 中获取 EmailAccountManager
                session = SessionManager().get_session()
                account_manager = EmailAccountManager(session)
                account = account_manager.get_email_account_by_id(email_address_id)
                email_address = account.username
                content_type = task.content_type
                task_name = task.task_name

                # 根据任务结果选择图标
                result_icon = "&#10004;"  # 默认绿色对勾
                result_color = "#4CAF50"  # 绿色
                if result.lower() != "success":
                    result_icon = "&#10060;"  # 红色叉叉
                    result_color = "#F44336"  # 红色

                # 格式化每个任务的结果
                result_text += f"""
                <tr>
                    <td style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{index + 1}</td>
                    <td style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{task_name}</td>
                    <td style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{content_type}</td>
                    <td style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{email_address}</td>
                    <td style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{drive}</td>
                    <td style='border: 1px solid #ddd; padding: 8px; text-align: center; color: {result_color}; font-size: 18px;'>{result_icon}</td>
                </tr>
                """

            result_text += "</tbody></table></div>"

            self.text_browser.setHtml(result_text)

        layout.addWidget(self.text_browser)

        # 添加自定义按钮
        custom_button = QPushButton("确认")
        custom_button.clicked.connect(self.accept)  # 连接“确认”按钮的点击事件

        # 创建水平布局来居中自定义按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)  # 添加弹性空间，以便按钮居中
        button_layout.addWidget(custom_button)
        button_layout.addStretch(1)

        layout.addLayout(button_layout)  # 将水平布局添加到主布局中

        self.setLayout(layout)
