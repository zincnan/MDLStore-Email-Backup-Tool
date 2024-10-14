import sys
import traceback
import time

from PyQt5.QtCore import pyqtSignal, QRunnable, pyqtSlot, QObject, Qt, QThreadPool
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QProgressBar, QLabel, QStyle, QVBoxLayout, QDialog, QApplication, QPushButton, QWidget, \
    QVBoxLayout, QSizePolicy


class ProgressWidget(QDialog):
    """Progress widget class"""

    def __init__(self, parent=None, label=''):
        super(ProgressWidget, self).__init__(parent)
        layout = QVBoxLayout(self)
        self.setWindowTitle(label)
        self.setMinimumSize(400, 100)
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                self.size(),
                QGuiApplication.primaryScreen().availableGeometry(),
            ))
        self.setMaximumHeight(150)
        self.label = QLabel(label)
        layout.addWidget(self.label)
        # Create a progress bar
        self.progressbar = QProgressBar(self)
        layout.addWidget(self.progressbar)
        self.progressbar.setGeometry(30, 40, 400, 200)
        # Create a label to show detailed progress
        self.detail_label = QLabel('', self)
        layout.addWidget(self.detail_label)
        self.info_label = QLabel('', self)
        layout.addWidget(self.info_label)

        self.setWindowFlag(Qt.WindowCloseButtonHint, False)  # 隐藏关闭按钮

        self.show()

    # 重载 closeEvent 方法，使窗口无法通过关闭按钮关闭
    # def closeEvent(self, event):
    #     event.ignore()  # 忽略关闭事件，防止窗口被关闭


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        No data
    error
        `tuple` (exctype, value, traceback.format_exc() )
    result
        `object` data returned from processing, anything
    """
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)
    detail = pyqtSignal(str)
    info = pyqtSignal(str)


class Worker(QRunnable):
    """Worker thread for running background tasks."""

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs['progress_callback'] = self.signals.progress
        self.kwargs['detail_callback'] = self.signals.detail
        self.kwargs['info_callback'] = self.signals.info

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(
                *self.args, **self.kwargs,
            )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()




