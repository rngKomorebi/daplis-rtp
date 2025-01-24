"""Application starter.

Run this file in the terminal to start the application.

"""

import os
import sys

import qdarkstyle
from PyQt5.QtWidgets import QApplication, QMainWindow

from daplis_rtp.gui.ui.mainwindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)

    # for stopping the script upon closing the app window
    def closeEvent(self, event):
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    # For dark theme
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    window.show()
    app.exec()
