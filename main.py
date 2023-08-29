"""Application starter.

Run this file in the terminal to start the application.

"""

from PyQt5.QtWidgets import QMainWindow, QApplication
import os

os.chdir(r"c:\Users\bruce\Documents\GitHub\LinoSPAD2-app")
from gui.ui.mainwindow import Ui_MainWindow
import sys

print(os.getcwd())


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)

    # for stopping the script upon closing the app window
    def closeEvent(self, event):
        QApplication.quit()


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
