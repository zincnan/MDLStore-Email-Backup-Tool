# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\Xsoftware\Python\workstation\MDLStore_v1.0\MDLStore\UI\EmailReader.ui'
#
# Created by: PyQt5 UI code generator 5.15.3
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_EmailReader(object):
    def setupUi(self, EmailReader):
        EmailReader.setObjectName("EmailReader")
        EmailReader.resize(794, 651)
        self.horizontalLayout = QtWidgets.QHBoxLayout(EmailReader)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.frame_all = QtWidgets.QFrame(EmailReader)
        self.frame_all.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_all.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_all.setObjectName("frame_all")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame_all)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_subject = QtWidgets.QLabel(self.frame_all)
        self.label_subject.setObjectName("label_subject")
        self.verticalLayout_2.addWidget(self.label_subject)
        self.frame_headers = QtWidgets.QFrame(self.frame_all)
        self.frame_headers.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_headers.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_headers.setObjectName("frame_headers")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame_headers)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_headers = QtWidgets.QLabel(self.frame_headers)
        self.label_headers.setObjectName("label_headers")
        self.verticalLayout.addWidget(self.label_headers)
        self.verticalLayout_2.addWidget(self.frame_headers)
        self.listWidget_attach = QtWidgets.QListWidget(self.frame_all)
        self.listWidget_attach.setObjectName("listWidget_attach")
        self.verticalLayout_2.addWidget(self.listWidget_attach)
        self.frame_placeholder = QtWidgets.QFrame(self.frame_all)
        self.frame_placeholder.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_placeholder.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_placeholder.setObjectName("frame_placeholder")
        self.verticalLayout_2.addWidget(self.frame_placeholder)
        self.horizontalLayout.addWidget(self.frame_all)

        self.retranslateUi(EmailReader)
        QtCore.QMetaObject.connectSlotsByName(EmailReader)

    def retranslateUi(self, EmailReader):
        _translate = QtCore.QCoreApplication.translate
        EmailReader.setWindowTitle(_translate("EmailReader", "Form"))
        self.label_subject.setText(_translate("EmailReader", "主题"))
        self.label_headers.setText(_translate("EmailReader", "邮件头"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    EmailReader = QtWidgets.QWidget()
    ui = Ui_EmailReader()
    ui.setupUi(EmailReader)
    EmailReader.show()
    sys.exit(app.exec_())
