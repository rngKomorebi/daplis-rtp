# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SinglePixelHistogram_tab_c.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(874, 636)
        self.gridLayout_2 = QtWidgets.QGridLayout(Form)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.frame = QtWidgets.QFrame(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.gridLayout = QtWidgets.QGridLayout(self.frame)
        self.gridLayout.setObjectName("gridLayout")
        self.lineEdit_browse = QtWidgets.QLineEdit(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_browse.sizePolicy().hasHeightForWidth())
        self.lineEdit_browse.setSizePolicy(sizePolicy)
        self.lineEdit_browse.setMinimumSize(QtCore.QSize(0, 28))
        self.lineEdit_browse.setObjectName("lineEdit_browse")
        self.gridLayout.addWidget(self.lineEdit_browse, 0, 2, 1, 1)
        self.pushButton_browse = QtWidgets.QPushButton(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_browse.sizePolicy().hasHeightForWidth())
        self.pushButton_browse.setSizePolicy(sizePolicy)
        self.pushButton_browse.setMinimumSize(QtCore.QSize(100, 28))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.pushButton_browse.setFont(font)
        self.pushButton_browse.setObjectName("pushButton_browse")
        self.gridLayout.addWidget(self.pushButton_browse, 0, 0, 1, 2)
        self.widget_figure = QtWidgets.QWidget(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_figure.sizePolicy().hasHeightForWidth())
        self.widget_figure.setSizePolicy(sizePolicy)
        self.widget_figure.setMinimumSize(QtCore.QSize(500, 425))
        font = QtGui.QFont()
        font.setPointSize(15)
        self.widget_figure.setFont(font)
        self.widget_figure.setObjectName("widget_figure")
        self.gridLayout.addWidget(self.widget_figure, 1, 0, 1, 3)
        spacerItem = QtWidgets.QSpacerItem(20, 5, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.gridLayout.addItem(spacerItem, 5, 0, 1, 3)
        self.gridLayout_2.addWidget(self.frame, 0, 0, 1, 1)
        self.frame_2 = QtWidgets.QFrame(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame_2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_comboBox_mask_2 = QtWidgets.QLabel(self.frame_2)
        self.label_comboBox_mask_2.setEnabled(True)
        self.label_comboBox_mask_2.setMinimumSize(QtCore.QSize(0, 26))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_comboBox_mask_2.setFont(font)
        self.label_comboBox_mask_2.setToolTip("")
        self.label_comboBox_mask_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_comboBox_mask_2.setObjectName("label_comboBox_mask_2")
        self.horizontalLayout_7.addWidget(self.label_comboBox_mask_2)
        self.comboBox_boardNumber = QtWidgets.QComboBox(self.frame_2)
        self.comboBox_boardNumber.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_boardNumber.sizePolicy().hasHeightForWidth())
        self.comboBox_boardNumber.setSizePolicy(sizePolicy)
        self.comboBox_boardNumber.setMinimumSize(QtCore.QSize(100, 0))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.comboBox_boardNumber.setFont(font)
        self.comboBox_boardNumber.setObjectName("comboBox_boardNumber")
        self.comboBox_boardNumber.addItem("")
        self.comboBox_boardNumber.addItem("")
        self.comboBox_boardNumber.addItem("")
        self.comboBox_boardNumber.addItem("")
        self.horizontalLayout_7.addWidget(self.comboBox_boardNumber)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.horizontalLayout_8.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_8.setSpacing(6)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_comboBox_mb_2 = QtWidgets.QLabel(self.frame_2)
        self.label_comboBox_mb_2.setMinimumSize(QtCore.QSize(0, 26))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_comboBox_mb_2.setFont(font)
        self.label_comboBox_mb_2.setObjectName("label_comboBox_mb_2")
        self.horizontalLayout_8.addWidget(self.label_comboBox_mb_2)
        self.comboBox_mb_2 = QtWidgets.QComboBox(self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_mb_2.sizePolicy().hasHeightForWidth())
        self.comboBox_mb_2.setSizePolicy(sizePolicy)
        self.comboBox_mb_2.setMinimumSize(QtCore.QSize(100, 0))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.comboBox_mb_2.setFont(font)
        self.comboBox_mb_2.setObjectName("comboBox_mb_2")
        self.comboBox_mb_2.addItem("")
        self.comboBox_mb_2.addItem("")
        self.comboBox_mb_2.addItem("")
        self.comboBox_mb_2.addItem("")
        self.comboBox_mb_2.addItem("")
        self.comboBox_mb_2.addItem("")
        self.comboBox_mb_2.addItem("")
        self.horizontalLayout_8.addWidget(self.comboBox_mb_2)
        self.verticalLayout.addLayout(self.horizontalLayout_8)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_FW_2 = QtWidgets.QLabel(self.frame_2)
        self.label_FW_2.setMinimumSize(QtCore.QSize(0, 26))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_FW_2.setFont(font)
        self.label_FW_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_FW_2.setObjectName("label_FW_2")
        self.horizontalLayout_9.addWidget(self.label_FW_2)
        self.comboBox_FW = QtWidgets.QComboBox(self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_FW.sizePolicy().hasHeightForWidth())
        self.comboBox_FW.setSizePolicy(sizePolicy)
        self.comboBox_FW.setMinimumSize(QtCore.QSize(100, 0))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.comboBox_FW.setFont(font)
        self.comboBox_FW.setObjectName("comboBox_FW")
        self.comboBox_FW.addItem("")
        self.comboBox_FW.addItem("")
        self.comboBox_FW.addItem("")
        self.horizontalLayout_9.addWidget(self.comboBox_FW)
        self.verticalLayout.addLayout(self.horizontalLayout_9)
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.label_timestamps_2 = QtWidgets.QLabel(self.frame_2)
        self.label_timestamps_2.setMinimumSize(QtCore.QSize(0, 26))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_timestamps_2.setFont(font)
        self.label_timestamps_2.setLineWidth(0)
        self.label_timestamps_2.setTextFormat(QtCore.Qt.PlainText)
        self.label_timestamps_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_timestamps_2.setObjectName("label_timestamps_2")
        self.horizontalLayout_11.addWidget(self.label_timestamps_2)
        self.spinBox_timestamps = QtWidgets.QSpinBox(self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox_timestamps.sizePolicy().hasHeightForWidth())
        self.spinBox_timestamps.setSizePolicy(sizePolicy)
        self.spinBox_timestamps.setMinimumSize(QtCore.QSize(100, 0))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.spinBox_timestamps.setFont(font)
        self.spinBox_timestamps.setMaximum(1536)
        self.spinBox_timestamps.setProperty("value", 300)
        self.spinBox_timestamps.setObjectName("spinBox_timestamps")
        self.horizontalLayout_11.addWidget(self.spinBox_timestamps)
        self.verticalLayout.addLayout(self.horizontalLayout_11)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setContentsMargins(-1, 0, -1, 7)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_enterPixNumber = QtWidgets.QLabel(self.frame_2)
        self.label_enterPixNumber.setEnabled(True)
        self.label_enterPixNumber.setMinimumSize(QtCore.QSize(100, 30))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_enterPixNumber.setFont(font)
        self.label_enterPixNumber.setTextFormat(QtCore.Qt.AutoText)
        self.label_enterPixNumber.setScaledContents(False)
        self.label_enterPixNumber.setObjectName("label_enterPixNumber")
        self.horizontalLayout_5.addWidget(self.label_enterPixNumber)
        self.spinBox_enterPixNumber = QtWidgets.QSpinBox(self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox_enterPixNumber.sizePolicy().hasHeightForWidth())
        self.spinBox_enterPixNumber.setSizePolicy(sizePolicy)
        self.spinBox_enterPixNumber.setMinimumSize(QtCore.QSize(100, 0))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.spinBox_enterPixNumber.setFont(font)
        self.spinBox_enterPixNumber.setMaximum(255)
        self.spinBox_enterPixNumber.setProperty("value", 127)
        self.spinBox_enterPixNumber.setObjectName("spinBox_enterPixNumber")
        self.horizontalLayout_5.addWidget(self.spinBox_enterPixNumber)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_cycle_length = QtWidgets.QLabel(self.frame_2)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_cycle_length.setFont(font)
        self.label_cycle_length.setObjectName("label_cycle_length")
        self.horizontalLayout.addWidget(self.label_cycle_length)
        self.lineEdit_cycleLength = QtWidgets.QLineEdit(self.frame_2)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.lineEdit_cycleLength.setFont(font)
        self.lineEdit_cycleLength.setObjectName("lineEdit_cycleLength")
        self.horizontalLayout.addWidget(self.lineEdit_cycleLength)
        self.label = QtWidgets.QLabel(self.frame_2)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_12.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.checkBox_linearScale_2 = QtWidgets.QCheckBox(self.frame_2)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.checkBox_linearScale_2.setFont(font)
        self.checkBox_linearScale_2.setChecked(True)
        self.checkBox_linearScale_2.setObjectName("checkBox_linearScale_2")
        self.horizontalLayout_12.addWidget(self.checkBox_linearScale_2)
        self.verticalLayout.addLayout(self.horizontalLayout_12)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.pushButton_refreshPlot = QtWidgets.QPushButton(self.frame_2)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.pushButton_refreshPlot.setFont(font)
        self.pushButton_refreshPlot.setObjectName("pushButton_refreshPlot")
        self.verticalLayout.addWidget(self.pushButton_refreshPlot)
        self.gridLayout_2.addWidget(self.frame_2, 0, 1, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton_browse.setText(_translate("Form", "Browse"))
        self.frame_2.setToolTip(_translate("Form", "asdf"))
        self.label_comboBox_mask_2.setText(_translate("Form", "LinoSPAD2 daughterboard"))
        self.comboBox_boardNumber.setItemText(0, _translate("Form", "B7d"))
        self.comboBox_boardNumber.setItemText(1, _translate("Form", "NL11"))
        self.comboBox_boardNumber.setItemText(2, _translate("Form", "A5"))
        self.comboBox_boardNumber.setItemText(3, _translate("Form", "D2b"))
        self.label_comboBox_mb_2.setText(_translate("Form", "LinoSPAD2 motherboard"))
        self.comboBox_mb_2.setItemText(0, _translate("Form", "#28"))
        self.comboBox_mb_2.setItemText(1, _translate("Form", "#33"))
        self.comboBox_mb_2.setItemText(2, _translate("Form", "#21"))
        self.comboBox_mb_2.setItemText(3, _translate("Form", "#36"))
        self.comboBox_mb_2.setItemText(4, _translate("Form", "#37"))
        self.comboBox_mb_2.setItemText(5, _translate("Form", "#4"))
        self.comboBox_mb_2.setItemText(6, _translate("Form", "#29"))
        self.label_FW_2.setText(_translate("Form", "Firmware version"))
        self.comboBox_FW.setItemText(0, _translate("Form", "2212b"))
        self.comboBox_FW.setItemText(1, _translate("Form", "2208"))
        self.comboBox_FW.setItemText(2, _translate("Form", "2212s"))
        self.label_timestamps_2.setToolTip(_translate("Form", "<html><head/><body><p>Number of timestamps per pixel per acquisition cycle. The default is 512.</p></body></html>"))
        self.label_timestamps_2.setText(_translate("Form", "Timestamps"))
        self.label_enterPixNumber.setText(_translate("Form", "Enter pixel index:"))
        self.label_cycle_length.setText(_translate("Form", "Cycle length"))
        self.lineEdit_cycleLength.setText(_translate("Form", "4e9"))
        self.label.setText(_translate("Form", "ps"))
        self.checkBox_linearScale_2.setText(_translate("Form", "Linear scale"))
        self.pushButton_refreshPlot.setText(_translate("Form", "Refresh plot"))
