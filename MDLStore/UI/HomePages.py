from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser


class HomePage(QWidget):
    def __init__(self, parent=None, *args, **kwargs):
        super(HomePage, self).__init__(parent, *args, **kwargs)
        # 创建 QVBoxLayout
        layout = QVBoxLayout()

        # 创建 QTextBrowser
        self.text_browser = QTextBrowser(self)
        # self.text_browser.setMinimumSize(1024,1000)

        html_text = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>欢迎使用 MDLStore 邮件备份工具</title>
    <style>
        html, body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
            color: #333;
            display: flex;
            flex-direction: column;
            height: 100%;  /* 1. 需要将页面的高度设置成浏览器可视区域的高度 */
        }
        .container {
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
            border-radius: 10px;
            text-align: center;
            flex-grow: 1; /* 让 container 占据剩余空间 */
        }
        h1 {
            color: #4a90e2;
            font-size: 36px;
            margin-bottom: 20px;
        }
        p {
            font-size: 18px;
            line-height: 1.8;
            margin-bottom: 30px;
        }
        .features {
            text-align: left;
            margin-bottom: 40px;
        }
        .features h2 {
            color: #4a90e2;
            font-size: 24px;
            margin-bottom: 10px;
        }
        .features ul {
            list-style-type: disc;
            padding-left: 20px;
            font-size: 16px;
        }
        .features ul li {
            margin-bottom: 10px;
        }
        .start-button {
            display: inline-block;
            padding: 15px 30px;
            font-size: 18px;
            background-color: #4a90e2;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background-color 0.3s ease;
        }
        .start-button:hover {
            background-color: #357ab8;
        }
        .footer {
            font-size: 12px;
            color: #777;
            padding: 10px 0;
            text-align: center;
            background-color: #f4f4f9;
            position: absolute;
            bottom: 0; 
            width: 100%;
        }
    </style>
</head>
<body>

<div class="container">
    <h1>欢迎使用 MDLStore</h1>
    <hr>
    <p>MDLStore 是一款轻量级的邮件数据备份工具，帮助您轻松备
    份和管理重要的邮件数据。通过我们的工具，您可以确保所有重要的通
    信记录和附件都能安全地存储，便于随时使用。</p>
        

    <div class="features">
        <h2>核心功能</h2>
        <ul>
            <li>自动备份多个邮箱账户的邮件</li>
            <li>批量执行备份任务，支持增量备份</li>
            <li>安全加密，保护您的邮件数据</li>
            <li>支持备份多种邮件服务提供的云附件</li>
            <li>支持附件内容检索，具备强大的数据搜索能力</li>
            <li>支持（Windows8, Windows10）</li>
        </ul>
    </div>
</div>
<br><br><br><br><br><br><br><br><br><br>
<div class="footer">
    <p>&copy; 2024 MDLStore 邮件备份工具. 保留所有权利。</p>
</div>

</body>
</html>
"""

        # 设置 HTML 内容到 QTextBrowser
        self.text_browser.setHtml(html_text)

        # 将 QTextBrowser 添加到布局
        layout.addWidget(self.text_browser)

        # 设置窗口的布局
        self.setLayout(layout)