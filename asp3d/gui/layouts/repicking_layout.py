# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'repicking_layout.ui'
#
# Created: Fri Mar 10 10:39:40 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_repicking(object):
    def setupUi(self, repicking):
        repicking.setObjectName("repicking")
        repicking.setWindowModality(QtCore.Qt.WindowModal)
        repicking.resize(800, 600)
        self.verticalLayout = QtGui.QVBoxLayout(repicking)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_repick = QtGui.QPushButton(repicking)
        self.pushButton_repick.setMaximumSize(QtCore.QSize(16777215, 30))
        self.pushButton_repick.setCheckable(True)
        self.pushButton_repick.setObjectName("pushButton_repick")
        self.horizontalLayout.addWidget(self.pushButton_repick)
        self.pushButton_delete = QtGui.QPushButton(repicking)
        self.pushButton_delete.setMaximumSize(QtCore.QSize(16777215, 30))
        self.pushButton_delete.setObjectName("pushButton_delete")
        self.horizontalLayout.addWidget(self.pushButton_delete)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_plot = QtGui.QVBoxLayout()
        self.verticalLayout_plot.setObjectName("verticalLayout_plot")
        self.verticalLayout.addLayout(self.verticalLayout_plot)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.pushButton_done = QtGui.QPushButton(repicking)
        self.pushButton_done.setObjectName("pushButton_done")
        self.horizontalLayout_2.addWidget(self.pushButton_done)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(repicking)
        QtCore.QMetaObject.connectSlotsByName(repicking)

    def retranslateUi(self, repicking):
        repicking.setWindowTitle(QtGui.QApplication.translate("repicking", "Repicking", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_repick.setText(QtGui.QApplication.translate("repicking", "Repick", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_delete.setText(QtGui.QApplication.translate("repicking", "Delete", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_done.setText(QtGui.QApplication.translate("repicking", "Done", None, QtGui.QApplication.UnicodeUTF8))

