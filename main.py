from PyQt5.QtWidgets import QMainWindow, QApplication
from graphic.ui.mainwindow_ui import Ui_MainWindow
import sys


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
