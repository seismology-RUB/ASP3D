# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'plot_shots_layout.ui'
#
# Created: Fri Mar 10 10:39:40 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_plot_shots(object):
    def setupUi(self, plot_shots):
        plot_shots.setObjectName("plot_shots")
        plot_shots.setWindowModality(QtCore.Qt.WindowModal)
        plot_shots.resize(1024, 768)
        self.verticalLayout = QtGui.QVBoxLayout(plot_shots)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout.addLayout(self.gridLayout)
        self.buttonBox = QtGui.QDialogButtonBox(plot_shots)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(plot_shots)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), plot_shots.close)
        QtCore.QMetaObject.connectSlotsByName(plot_shots)

    def retranslateUi(self, plot_shots):
        plot_shots.setWindowTitle(QtGui.QApplication.translate("plot_shots", "Plot of Shots", None, QtGui.QApplication.UnicodeUTF8))

