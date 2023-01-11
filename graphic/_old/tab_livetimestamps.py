import glob
import os

from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout, QFileDialog, QLineEdit, QCheckBox, \
    QHBoxLayout, QGridLayout, QSlider
from PyQt5.QtCore import pyqtSlot, QTimer, Qt
from app.tools import timestamp_computation
from app.graphic.plot_figure import PltCanvas
import numpy as np
import matplotlib

matplotlib.use("Qt5Agg")


class LiveTimestamps(QWidget):
    def __init__(self, parent):
        super(LiveTimestamps, self).__init__(parent)
        self.mainLayout = QHBoxLayout(self)
        self.setLayout(self.mainLayout)

        self.leftQwidget = QWidget(self)
        self.leftLayout = QVBoxLayout(self)
        self.pushButtonLoadPath = QPushButton("Set path")

        self.xSliderLeft = QSlider(Qt.Horizontal)
        self.xSliderRight = QSlider(Qt.Horizontal)
        self.checkBoxScale = QCheckBox("Linear scale", self)
        self.lineEditPath = QLineEdit('')
        self.refreshBtn = QPushButton("Refresh plot")
        self.pushButtonStartSync = QPushButton("Start stream")
        self.plotWidget = PltCanvas(self)
        self.timer = QTimer()
        self.timerRunning = False
        self.last_file_ctime = 0

        self.pathtotimestamp = ''
        self.leftLayout.addWidget(self.pushButtonLoadPath)
        self.leftLayout.addWidget(self.lineEditPath)
        self.leftLayout.addWidget(self.pushButtonStartSync)
        self.leftLayout.addWidget(self.refreshBtn)
        self.leftLayout.addWidget(self.plotWidget)
        self.leftLayout.addWidget(self.xSliderLeft)
        self.leftLayout.addWidget(self.xSliderRight)
        self.leftLayout.addWidget(self.checkBoxScale)
        self.leftQwidget.setLayout(self.leftLayout)
        self.mainLayout.addWidget(self.leftQwidget)

        self.checkBoxWidget = QWidget(self)
        self.checkBoxLayoutlayout = QGridLayout(self)
        self.checkBoxWidget.setLayout(self.checkBoxLayoutlayout)
        self.checkBoxPixel = []
        self.maskValidPixels = np.zeros(256)
        for clm in range(8):
            for row in range(32):
                self.checkBoxPixel.append(QCheckBox(str(row + clm * 32), self))
                self.checkBoxLayoutlayout.addWidget(self.checkBoxPixel[row + clm * 32], row, clm)
        self.checkBoxWidget.resize(400, 500)
        self.mainLayout.addWidget(self.checkBoxWidget)

        # Add tabs to widget
        self.pushButtonLoadPath.clicked.connect(self.slot_loadpath)
        self.pushButtonStartSync.clicked.connect(self.slot_startstream)
        self.timer.timeout.connect(self.updateTimeStamp)
        self.checkBoxScale.stateChanged.connect(self.slot_checkplotscale)
        self.refreshBtn.clicked.connect(self.slot_refresh)
        self.xSliderLeft.valueChanged.connect(self.slot_updateLeftSlider)
        self.xSliderRight.valueChanged.connect(self.slot_updateRightSlider)

        self.leftPlotLim = 0
        self.rightPlotLim = 255
        self.xSliderLeft.setMinimum(0)
        self.xSliderLeft.setMaximum(255)
        self.xSliderRight.setMinimum(0)
        self.xSliderRight.setMaximum(255)
        self.xSliderRight.setSliderPosition(255)
        self.leftPosition = 0
        self.rightPosition = 255

    def updateTimeStamp(self):
        self.getvalidtimestamps()
        os.chdir(self.pathtotimestamp)
        DATA_FILES = glob.glob('*.dat*')
        print("updateTimeStamp: timer running")
        try:
            last_file = max(DATA_FILES, key=os.path.getctime)
            new_file_ctime = os.path.getctime(last_file)

            if new_file_ctime > self.last_file_ctime:
                # print("updateTimeStamp: new file")
                self.last_file_ctime = new_file_ctime
                # print("updateTimeStamp:" + self.pathtotimestamp + last_file)
                validtimestemps, peak = timestamp_computation.get_nmr_validtimestamps(
                    self.pathtotimestamp + '/' + last_file, np.arange(145, 155, 1), 512)
                validtimestemps = validtimestemps * self.maskValidPixels
                self.plotWidget.setPlotData(np.arange(0, 256, 1), validtimestemps, peak,[self.leftPosition,self.rightPosition])
            # else:
            # print("updateTimeStamp:  not a new file")

        except ValueError:
            print("updateTimeStamp:  waiting for a file")

    def getvalidtimestamps(self):
        for i in range(256):
            if self.checkBoxPixel[i].isChecked():
                self.maskValidPixels[i] = 0
            else:
                self.maskValidPixels[i] = 1

    @pyqtSlot()
    def slot_loadpath(self):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.lineEditPath.setText(file)
        self.pathtotimestamp = file
        print(file + "\n")

    def slot_startstream(self):
        self.last_file_ctime = 0

        if self.timerRunning is True:
            self.timer.stop()
            self.timerRunning = False
            self.pushButtonStartSync.setText("Start stream")
        else:
            self.pushButtonStartSync.setText("Stop stream")
            self.timer.start(100)
            self.timerRunning = True

    def slot_checkplotscale(self):
        if self.checkBoxScale.isChecked():
            self.plotWidget.setPlotScale(True)
        else:
            self.plotWidget.setPlotScale(False)

    def slot_refresh(self):
        self.updateTimeStamp()
        self.last_file_ctime = 0

    def slot_updateLeftSlider(self):
        if self.xSliderLeft.value() >= self.xSliderRight.value():
            self.xSliderLeft.setValue(self.xSliderRight.value()-1)
        self.leftPosition = self.xSliderLeft.value()


    def slot_updateRightSlider(self):
        if self.xSliderRight.value() <= self.xSliderLeft.value():
            self.xSliderRight.setValue(self.xSliderLeft.value()+1)
        self.rightPosition = self.xSliderRight.value()
