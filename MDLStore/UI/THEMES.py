FUNC_LIST_THEME = """
                    QListWidget#left_widget {
                    background-color: #f0f0f0;
                    border: 2px solid #8f8f8f;
                    padding: 5px;
                }
                
                QListWidget#left_widget::item {
                    height: 42px; /* 设置每个项目的高度 */
                    padding: 0px;
                    background-color: #f0f0f0;
                    color: #333333;
                    border: none; /* 无边框 */
                }
                
                QListWidget#left_widget::item:selected {
                    background-color: #d2d2d2;
                    color: black;
                    border: none; /* 无边框 */
                }
                
                QListWidget#left_widget::item:selected:active {
                    background-color: #d2d2d2;
                    color: black;
                    border: none; /* 无边框 */
                }
                
                QListWidget#left_widget::item:hover {
                    background-color: #e1e1e1;
                }
                
                QListWidget#left_widget::item:selected:!active {
                    background-color: #d2d2d2; /* 确保非激活状态下的颜色 */
                    color: black;
                    border: none; /* 无边框 */
                }
                
                QListWidget#left_widget::item:selected:focus {
                outline: 0px;
                }

                """

LISTVIEW_ACC = """
                QListView#listView {
                    background-color: #f0f0f0;
                    border: 2px solid #8f8f8f;
                    padding: 5px;
                }
                QListView#listView::item {
                    height: 42px; /* 设置每个项目的高度 */
                    padding: 0px;
                    background-color: #f0f0f0;
                    color: #333333;
                }
                QListView#listView::item:selected {
                    background-color: #d2d2d2;
                    color: black;
                    border: none; /* 无边框 */
                }
                QListView#listView::item:hover {
                    background-color: #e1e1e1;
                }
                QListView#listView::item:selected:focus {
                    outline: none; /* 移除虚线框 */
                }
            """

LISTVIEW_TASK_ALL = """
        QListView#listView_all {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            padding: 0px;
        }
        QListView#listView_all::item {
            height: 20px;
            padding: 2px;
            color: #333;
            border: 1px solid #d1d1d1
        }
        QListView#listView_all::item:selected {
            background-color: #d2d2d2;
            color: black;
        }
        QListView#listView_all::item:hover {
            background-color: #e1e1e1;
        }
            """

LISTVIEW_TASK_CUR = """
        QListView#listView_cur {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            padding: 0px;
        }
        QListView#listView_cur::item {
            height: 20px;
            padding: 2px;
            color: #333;
            border: 1px solid #d1d1d1
        }
        QListView#listView_cur::item:selected {
            background-color: #d2d2d2;
            color: black;
        }
        QListView#listView_cur::item:hover {
            background-color: #e1e1e1;
        }
            """

TREEVIEW_TASKS_FOLDER = """
    QTreeView#treeView {
        background-color: #f0f0f0; 
        border: 2px solid #8f8f8f; 
        padding: 5px;
    }

    QTreeView#treeView::item {
        height: 24px; 
        padding: 2px 5px;
        color: #333333; /* 文本颜色 */
        border: none; /* 无边框 */
    }
    QTreeView#treeView::item:has-children {
    background-color: #d2d2d2;
    font-weight: bold;
}

    QTreeView#treeView::item:selected {
        background-color: #718ba4; /* 选中时的背景颜色 */
        color: white; /* 选中时的文本颜色 */
        border: none; /* 无边框 */
    }
    
    QTreeView#treeView::item:hover:selected {
        background-color: #7a8796; /* 确保选中状态优先于悬停状态 */
    }
    
    QTreeView#treeView::item:hover {
        background-color: #9da9b6; /* 悬停时的背景颜色 */
        color: black; /* 悬停时的文本颜色 */
    }

    QTreeView#treeView::item:selected:focus {
        outline: none; /* 移除虚线框 */
    }
    # 
    # QTreeView#treeView::branch:has-children:!has-siblings:closed,
    # QTreeView#treeView::branch:closed:has-children:has-siblings {
    #     image: none;
    #     border-image: none;
    #     border-left: 1px solid #8f8f8f;
    # }
    # 
    # QTreeView#treeView::branch:open:has-children:!has-siblings,
    # QTreeView#treeView::branch:open:has-children:has-siblings  {
    #     image: none;
    #     border-image: none;
    #     border-left: 1px solid #8f8f8f;
    # }
    # 
    QTreeView#treeView::branch {
        background-color: #f0f0f0;
        margin: 0px;
    }

    # QTreeView#treeView::branch:has-siblings:!adjoins-item {
    #     border-image: url(:/images/vline.png) 0;
    # }
    # 
    # QTreeView#treeView::branch:has-siblings:adjoins-item {
    #     border-image: url(:/images/branch-more.png) 0;
    # }
    # 
    # QTreeView#treeView::branch:!has-children:!has-siblings:adjoins-item {
    #     border-image: url(:/images/branch-end.png) 0;
    # }
"""

LISTVIEW_EMAILS = """
    QListView#listView_emails {
    background-color: #f0f0f0; /* 列表背景颜色 */
    border: 2px solid #4f7aa7; /* 列表边框 */
    padding: 0px;
}

QListView#listView_emails::item {
    height: 60px; /* 设置每个项目的高度 */
    padding: 1px;
    color: black; /* 项目文本颜色 */
    background-color: #ffffff; /* 项目背景颜色 */
    border-bottom: 1px solid #dcdcdc; /* 为每个项目添加底部边框 */
}

QListView#listView_emails::item:selected {
    background-color: #6e879f; /* 选中时的背景颜色 */
    color: white; /* 选中时的文本颜色 */
    border: 1px solid #5c8dbc; /* 选中时的边框颜色 */
}

"""
# LISTWIDGET_ATTACH = """
#     QListWidget#listWidget_attach {
#         background-color: #f8f8f8; /* 列表背景颜色 */
#         border: 1px solid #cccccc; /* 列表边框颜色 */
#         padding: 0px;
#         margin: 0px;
#     }
#
#     QListWidget#listWidget_attach::item {
#         height: 25px; /* 设置每个项目的高度 */
#         width: 260px;
#         padding: 0px;
#         color: black; /* 项目文本颜色 */
#         background-color: white; /* 项目背景颜色 */
#         border: 1px solid #cccccc; /* 项目边框颜色 */
#         margin-bottom: 0px; /* 项目之间的间距 */
#         text-align: left; /* 项目文本左对齐 */
#     }
#
#     QListWidget#listWidget_attach::item:selected {
#         background-color: #cfe3fa; /* 选中时的背景颜色 */
#         color: black; /* 选中时的文本颜色 */
#         border: 1px solid #5c6f7f; /* 选中时的边框颜色 */
#     }
#
#     QListWidget#listWidget_attach::item:hover {
#         background-color: #f0f9ff; /* 悬停时的背景颜色 */
#         color: black; /* 悬停时的文本颜色 */
#         border: 1px solid #b8c0c8; /* 悬停时的边框颜色 */
#     }
#
#     /* 确保选中状态下即使悬停，颜色也保持为选中颜色 */
#     QListWidget#listWidget_attach::item:selected:hover {
#         background-color: #cfe3fa; /* 选中时悬停时保持为选中颜色 */
#         color: black; /* 选中时悬停时的文本颜色 */
#         border: 1px solid #5c6f7f; /* 选中时悬停时的边框颜色 */
#     }
# """


LISTWIDGET_ATTACH = """
QListWidget#listWidget_attach {
    background-color: #f8f8f8;  /* 列表背景颜色 */
    border: none;  /* 无边框 */
    padding: 0px;  /* 无内边距 */
    margin: 0px;   /* 无外边距 */
}

QListWidget#listWidget_attach::item {
    width: 180px;  /* 设置每个项目的宽度 */
    height: 30px;  /* 设置每个项目的高度 */
    padding: 0px;
    border: 1px solid #cccccc;  /* 项目边框颜色 */
    margin: 0px;  /* 项目之间无间距 */
    text-align: left;  /* 项目文本左对齐 */
    background: none;
}

QListWidget#listWidget_attach::item:selected {
    background-color: #cfe3fa;  /* 选中时的背景颜色 */
    color: black;  /* 选中时的文本颜色 */
    border: 1px solid #5c6f7f;  /* 选中时的边框颜色 */
}

QListWidget#listWidget_attach::item:hover {
    background-color: #f0f9ff;  /* 悬停时的背景颜色 */
    color: black;  /* 悬停时的文本颜色 */
    border: 1px solid #b8c0c8;  /* 悬停时的边框颜色 */
}
"""