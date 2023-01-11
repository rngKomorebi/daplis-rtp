# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SinglePixelHistogram.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import os
from app.graphic.single_pixel_histogram import SinglePixelHistogram


class Ui_SinglePixelHistogram(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(900, 560)
        Form.setMinimumSize(QtCore.QSize(900, 560))

        # pixel number
        self.pix = None
        # path
        self.folder = ""

        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.btnBrowse = QtWidgets.QPushButton(Form)
        self.btnBrowse.setObjectName("pushButton")
        self.gridLayout.addWidget(self.btnBrowse, 0, 0, 1, 1)

        self.btnBrowse.clicked.connect(self._get_dir)

        self.path = QtWidgets.QLineEdit(Form)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.path.sizePolicy().hasHeightForWidth())
        self.path.setSizePolicy(sizePolicy)
        self.path.setObjectName("lineEdit")
        self.gridLayout.addWidget(self.path, 0, 1, 1, 1)

        spacerItem = QtWidgets.QSpacerItem(
            382, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.gridLayout.addItem(spacerItem, 0, 2, 1, 2)

        # self.widget = QtWidgets.QWidget(Form)
        self.figureWidget = SinglePixelHistogram()
        self.figureWidget.setMinimumSize(QtCore.QSize(486, 445))
        self.figureWidget.setObjectName("widget")
        self.gridLayout.addWidget(self.figureWidget, 1, 0, 2, 2)

        self.label = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setTextFormat(QtCore.Qt.AutoText)
        self.label.setScaledContents(False)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 2, 1, 1)

        self.pixInput = QtWidgets.QLineEdit(Form)
        self.pixInput.setMinimumSize(QtCore.QSize(0, 28))
        self.pixInput.setObjectName("pixInput")
        self.pixInput.setValidator(QtGui.QIntValidator())
        self.pixInput.setMaxLength(4)
        self.pixInput.setAlignment(QtCore.Qt.AlignCenter)
        self.pixInput.setFont(QtGui.QFont("Arial", 20))
        self.gridLayout.addWidget(self.pixInput, 1, 3, 1, 1)

        self.pixInput.returnPressed.connect(lambda: self._pix_input())

        self.btnRfrshPlot = QtWidgets.QPushButton(Form)
        self.btnRfrshPlot.setObjectName("pushButton_2")
        self.gridLayout.addWidget(self.btnRfrshPlot, 2, 2, 1, 2)
        
        self.btnRfrshPlot.clicked.connect(self._refresh_plot)

        self._retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def _retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.btnBrowse.setText(_translate("Form", "Browse"))
        self.label.setText(_translate("Form", "Enter pixel index:"))
        self.btnRfrshPlot.setText(_translate("Form", "Refresh plot"))

    def _get_dir(self):
        self.folder = str(
            QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        )
        self.path.setText(self.folder)

    def _pix_input(self):

        self.pix = int(self.pixInput.text())
        os.chdir(self.folder)

        self.figureWidget._plot_hist(self.pix)

    def _refresh_plot(self):
        
        self.pix = int(self.pixInput.text())
        os.chdir(self.folder)

        self.figureWidget._plot_hist(self.pix)
