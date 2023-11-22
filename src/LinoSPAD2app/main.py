"""Application starter.

Run this file in the terminal to start the application.

"""

from PyQt5.QtWidgets import QMainWindow, QApplication
from LinoSPAD2app.gui.ui.mainwindow import Ui_MainWindow
import sys

# import qdarkstyle
import os


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
    # app.setStyleSheet(qdarkstyle.load_stylesheet())
    window.show()
    app.exec()
