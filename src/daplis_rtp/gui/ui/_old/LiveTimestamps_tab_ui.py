# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'LiveTimestamps_tab.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets
from app.graphic.plot_figure import PltCanvas
import glob
import os
from app.tools import timestamp_computation
import numpy as np


class Ui_LiveTimestamps(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(900, 560)
        Form.setMinimumSize(QtCore.QSize(900, 560))
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")

        self.pushButtonLoadPath = QtWidgets.QPushButton(Form)
        self.pushButtonLoadPath.setObjectName("pushButton")
        self.pushButtonLoadPath.clicked.connect(self._slot_loadpath)
        self.gridLayout.addWidget(self.pushButtonLoadPath, 0, 0, 1, 2)
        self.pathtotimestamp = ""

        self.lineEditPath = QtWidgets.QLineEdit(Form)
        self.lineEditPath.setObjectName("lineEdit")
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEditPath.sizePolicy().hasHeightForWidth())
        self.lineEditPath.setSizePolicy(sizePolicy)
        self.gridLayout.addWidget(self.lineEditPath, 0, 2, 1, 1)

        self.label = QtWidgets.QLabel(Form)
        self.label.setAutoFillBackground(True)
        self.label.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.label.setFrameShadow(QtWidgets.QFrame.Plain)
        self.label.setTextFormat(QtCore.Qt.PlainText)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 3, 1, 1)

        # self.widget = QtWidgets.QWidget(Form)
        self.plotWidget = PltCanvas()
        self.plotWidget.setMinimumSize(500, 400)
        self.plotWidget.setObjectName("widget")
        self.gridLayout.addWidget(self.plotWidget, 1, 0, 4, 3)

        # pixel masking scroll area
        self.scrollArea = QtWidgets.QScrollArea(Form)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 383, 346))
        self.checkBoxPixel = []
        self.scrollAreaWidgetContentslayout = QtWidgets.QGridLayout(
            self.scrollAreaWidgetContents
        )
        self.maskValidPixels = np.zeros(256)
        for col in range(4):
            for row in range(64):
                self.checkBoxPixel.append(
                    QtWidgets.QCheckBox(
                        str(row + col * 64), self.scrollAreaWidgetContents
                    )
                )
                self.scrollAreaWidgetContentslayout.addWidget(
                    self.checkBoxPixel[row + col * 64], row, col, 1, 1
                )
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout.addWidget(self.scrollArea, 1, 3, 1, 1)
        # button for pix masking reset
        self.btnPixMaskReset = QtWidgets.QPushButton(Form)
        self.btnPixMaskReset.setObjectName("pushButton_4")
        self.gridLayout.addWidget(self.btnPixMaskReset, 2, 3, 1, 1)
        self.btnPixMaskReset.clicked.connect(self._reset_pix_mask)
        # linear scale check box
        self.checkBoxScale = QtWidgets.QCheckBox(Form)
        self.checkBoxScale.setObjectName("checkBox")
        self.gridLayout.addWidget(self.checkBoxScale, 3, 3, 1, 1)
        self.checkBoxScale.stateChanged.connect(self._slot_checkplotscale)
        # plot refresh button
        self.refreshBtn = QtWidgets.QPushButton(Form)
        self.refreshBtn.setObjectName("pushButton_2")
        self.gridLayout.addWidget(self.refreshBtn, 4, 3, 1, 1)
        self.refreshBtn.clicked.connect(self._slot_refresh)
        # real-time plotting button
        self.pushButtonStartSync = QtWidgets.QPushButton(Form)
        self.pushButtonStartSync.setMinimumSize(QtCore.QSize(385, 40))
        self.pushButtonStartSync.setObjectName("pushButton_3")
        self.gridLayout.addWidget(self.pushButtonStartSync, 5, 3, 1, 1)
        self.pushButtonStartSync.clicked.connect(self._slot_startstream)

        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 5, 0, 1, 1)

        # left xlim slider
        self.xSliderLeft = QtWidgets.QSlider(Form)
        self.xSliderLeft.setOrientation(QtCore.Qt.Horizontal)
        self.xSliderLeft.setObjectName("horizontalSlider")
        self.gridLayout.addWidget(self.xSliderLeft, 5, 1, 1, 2)
        self.xSliderLeft.valueChanged.connect(self._slot_updateLeftSlider)

        self.label_3 = QtWidgets.QLabel(Form)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 6, 0, 1, 1)

        # right xlim slider
        self.xSliderRight = QtWidgets.QSlider(Form)
        self.xSliderRight.setOrientation(QtCore.Qt.Horizontal)
        self.xSliderRight.setObjectName("horizontalSlider_2")
        self.gridLayout.addWidget(self.xSliderRight, 6, 1, 1, 2)
        self.xSliderRight.valueChanged.connect(self._slot_updateRightSlider)

        self.xSliderLeft.setMinimum(0)
        self.xSliderLeft.setMaximum(255)
        self.xSliderRight.setMinimum(0)
        self.xSliderRight.setMaximum(255)
        self.xSliderRight.setSliderPosition(255)
        self.leftPosition = 0
        self.rightPosition = 255

        self._retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

        # timer
        self.timer = QtCore.QTimer()
        self.timerRunning = False
        self.last_file_ctime = 0
        self.timer.timeout.connect(self._update_time_stamp)

    def _retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButtonLoadPath.setText(_translate("Form", "Browse"))
        self.label.setText(_translate("Form", "Pixel Masking"))
        self.checkBoxScale.setText(_translate("Form", "Linear scale"))
        self.refreshBtn.setText(_translate("Form", "Refresh plot"))
        self.pushButtonStartSync.setText(_translate("Form", "Start stream"))
        self.label_2.setText(_translate("Form", "Left xlim"))
        self.label_3.setText(_translate("Form", "Right xlim"))
        self.btnPixMaskReset.setText(_translate("Form", "Reset pixel masking"))

    def _slot_loadpath(self):
        file = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.lineEditPath.setText(file)
        self.pathtotimestamp = file

    def _slot_startstream(self):
        self.last_file_ctime = 0

        if self.timerRunning is True:
            self.timer.stop()
            self.timerRunning = False
            self.pushButtonStartSync.setText("Start stream")
        else:
            self.pushButtonStartSync.setText("Stop stream")
            self.timer.start(100)
            self.timerRunning = True

    def _slot_checkplotscale(self):
        if self.checkBoxScale.isChecked():
            self.plotWidget.setPlotScale(True)
        else:
            self.plotWidget.setPlotScale(False)

    def _slot_refresh(self):
        self._update_time_stamp()
        self.last_file_ctime = 0

    def _slot_updateLeftSlider(self):
        if self.xSliderLeft.value() >= self.xSliderRight.value():
            self.xSliderLeft.setValue(self.xSliderRight.value() - 1)
        self.leftPosition = self.xSliderLeft.value()

    def _slot_updateRightSlider(self):
        if self.xSliderRight.value() <= self.xSliderLeft.value():
            self.xSliderRight.setValue(self.xSliderLeft.value() + 1)
        self.rightPosition = self.xSliderRight.value()

    def _update_time_stamp(self):
        self._mask_pixels()
        os.chdir(self.pathtotimestamp)
        DATA_FILES = glob.glob("*.dat*")
        print("_update_time_stamp: timer running")
        try:
            last_file = max(DATA_FILES, key=os.path.getctime)
            new_file_ctime = os.path.getctime(last_file)

            if new_file_ctime > self.last_file_ctime:

                self.last_file_ctime = new_file_ctime

                validtimestemps, peak = timestamp_computation.get_nmr_validtimestamps(
                    self.pathtotimestamp + "/" + last_file, np.arange(145, 155, 1), 512
                )
                validtimestemps = validtimestemps * self.maskValidPixels
                self.plotWidget.setPlotData(
                    np.arange(0, 256, 1),
                    validtimestemps,
                    peak,
                    [self.leftPosition, self.rightPosition],
                )
        except ValueError:
            print("_update_time_stamp:  waiting for a file")

    def _mask_pixels(self):
        '''
        Function for masking the chosen pixels.

        Returns
        -------
        None.

        '''
        for i in range(256):
            if self.checkBoxPixel[i].isChecked():
                self.maskValidPixels[i] = 0
            else:
                self.maskValidPixels[i] = 1

    def _reset_pix_mask(self):
        """
        Function for resetting the pixel masking by unchecking all pixel
        mask check boxes.

        Returns
        -------
        None.

        """
        for i in range(256):
            cb = self.scrollAreaWidgetContentslayout.itemAt(i).widget()
            cb.setChecked(False)
