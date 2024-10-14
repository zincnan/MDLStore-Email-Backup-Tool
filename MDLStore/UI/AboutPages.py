from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QTextBrowser


class AboutPage(QWidget):
    def __init__(self, parent=None, *args, **kwargs):
        super(AboutPage, self).__init__(parent, *args, **kwargs)
        # 创建 QVBoxLayout
        layout = QVBoxLayout()

        # 创建 QTextBrowser
        self.text_browser = QTextBrowser(self)

        html_text = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MDLStore 邮件备份工具 - 软件介绍</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #fff;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }
        h1, h2, h3 {
            color: #4a90e2;
        }
        h1 {
            text-align: center;
            margin-bottom: 20px;
        }
        h2 {
            margin-top: 40px;
            border-bottom: 2px solid #4a90e2;
            padding-bottom: 10px;
        }
        p {
            line-height: 1.8;
            margin: 10px 0;
        }
        ul {
            list-style-type: disc;
            padding-left: 20px;
        }
        .license {
            background-color: #f0f8ff;
            padding: 10px;
            border-left: 5px solid #4a90e2;
            margin-top: 20px;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            font-size: 12px;
            color: #777;
        }
        .logo {
            display: block;
            margin: 0 auto 20px auto;
            width: 150px;  /* 控制图标的宽度 */
        }
    </style>
</head>
<body>

<div class="container">
    <!-- 嵌入Base64编码图标 -->
    <!-- <img src="data:image/png;base64,PUT-YOUR-BASE64-HERE" alt="MDLStore Logo" class="logo"> -->

    <h1>MDLStore 邮件备份工具</h1>
    <p><strong>版本：</strong>v1.0</p>
    <p><strong>开发工具：</strong>PyQt, SQLite, IMAP 协议等多种 Python 包</p>
    <p><strong>开源协议：</strong>遵循 MIT 开源协议</p>

    <h2>概述</h2>
    <p>MDLStore 是一款轻量级但功能强大的专业级邮件数据备份解决方案。该工具专为需要管理和备份多个邮箱账户数据的用户而设计，能够实现自动化、定时化、分类化的邮件备份，确保用户的所有重要邮件数据都能够安全、可靠地存储和检索。</p>
    <p>MDLStore 提供了一站式的邮件备份体验，涵盖从邮件账户管理、数据备份到附件管理的完整功能流程，满足个人和企业用户对邮件数据安全性和高效管理的需求。</p>

    <h2>核心功能</h2>
    <ul>
        <li><strong>全面的邮件备份功能：</strong>支持自动从多个邮箱账户中抓取邮件并执行定期备份，确保所有重要的通信记录都能及时保存到本地存储。</li>
        <li><strong>高效的邮件数据分类和检索：</strong>通过强大的邮件分类和检索系统，可以根据发件人、时间、邮件主题等条件快速定位邮件。</li>
        <li><strong>附件管理与批量操作：</strong>支持邮件附件的自动分类存储，用户可以方便地查看、导出和管理备份的所有邮件附件。</li>
        <li><strong>多账户和多平台支持：</strong>软件支持多个邮箱账户的同时管理，允许用户在一处集中管理不同来源的邮件数据，并提供多平台的兼容性。</li>
        <li><strong>安全加密与数据恢复：</strong>提供邮件数据的加密备份功能，确保备份数据的安全性，并支持数据的精确恢复。</li>
        <li><strong>定时与自动化备份：</strong>用户可以自由配置自动备份任务，MDLStore 将按照用户设置的时间间隔定时执行备份操作。</li>
    </ul>

    <h2>技术架构</h2>
    <p>MDLStore 使用现代化的技术架构，确保软件的高效、稳定和可扩展性：</p>
    <ul>
        <li><strong>PyQt：</strong>用于实现跨平台的图形用户界面（GUI）。</li>
        <li><strong>IMAP 协议：</strong>用于安全地访问和同步用户的邮件账户数据。</li>
        <li><strong>SQLite：</strong>用于本地存储和管理备份的数据，确保数据的高效查询与组织。</li>
    </ul>

    <h2>系统要求</h2>
    <ul>
        <li>操作系统：Windows 7/8/10、macOS、Linux</li>
        <li>内存：至少 2GB 内存</li>
        <li>硬盘空间：至少 100MB 可用空间</li>
        <li>网络：能够连接 IMAP 服务器的稳定网络</li>
    </ul>

    <h2>许可证</h2>
    <div class="license">
        <p>MDLStore 邮件备份工具遵循 MIT 开源许可证发布。此许可证允许软件自由使用、修改和分发，无需附加其他的许可费用。</p>
        <p><strong>MIT 开源许可证 (MIT License)</strong></p>
        <p>版权所有 (c) 2024 MDLStore 项目</p>
        <p>特此授予获得本软件及相关文档文件（以下简称“软件”）副本的任何人，软件的使用权，包括但不限于使用、复制、修改、合并、出版、发布、散发、再授权及出售软件副本的权利，以及允许软件供应方在符合以下条件的情况下提供软件给他人：</p>
        <p>上述版权声明和本许可声明应包含在软件的所有副本或主要部分中。</p>
        <p>本软件按“原样”提供，不提供任何明示或暗示的担保，包括但不限于适销性、适用于特定目的及不侵权的担保。在任何情况下，作者或版权持有人均不对因软件或软件的使用或其他交易引起的任何索赔、损害或其他责任负责，无论是在合同诉讼、侵权行为或其他情况下。</p>
    </div>

    <div class="footer">
        <p>MDLStore 邮件备份工具 v1.0 提供了一个安全、稳定且灵活的邮件数据备份和管理解决方案，特别适合企业和个人用户的日常备份需求。</p>
        <p>如有任何疑问或建议，欢迎联系项目维护者或参与开源社区贡献代码。</p>
    </div>
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
