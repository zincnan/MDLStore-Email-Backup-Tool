# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\Xsoftware\Python\workstation\MDLStore_v1.0\MDLStore\UI\ResultPage.ui'
#
# Created by: PyQt5 UI code generator 5.15.3
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ResultPage(object):
    def setupUi(self, ResultPage):
        ResultPage.setObjectName("ResultPage")
        ResultPage.resize(1149, 734)
        self.horizontalLayout = QtWidgets.QHBoxLayout(ResultPage)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.groupBox = QtWidgets.QGroupBox(ResultPage)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.listView_emails = QtWidgets.QListView(self.groupBox)
        self.listView_emails.setObjectName("listView_emails")
        self.verticalLayout.addWidget(self.listView_emails)
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setText("")
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.widget_eml = QtWidgets.QWidget(self.groupBox)
        self.widget_eml.setObjectName("widget_eml")
        self.horizontalLayout_2.addWidget(self.widget_eml)
        self.horizontalLayout.addWidget(self.groupBox)

        self.retranslateUi(ResultPage)
        QtCore.QMetaObject.connectSlotsByName(ResultPage)

    def retranslateUi(self, ResultPage):
        _translate = QtCore.QCoreApplication.translate
        ResultPage.setWindowTitle(_translate("ResultPage", "Form"))
        self.groupBox.setTitle(_translate("ResultPage", "搜索结果"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ResultPage = QtWidgets.QWidget()
    ui = Ui_ResultPage()
    ui.setupUi(ResultPage)
    ResultPage.show()
    sys.exit(app.exec_())