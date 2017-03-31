# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'export_receiver_locations_layout.ui'
#
# Created: Fri Mar 10 10:39:40 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_export_receiver_locations(object):
    def setupUi(self, export_receiver_locations):
        export_receiver_locations.setObjectName("export_receiver_locations")
        export_receiver_locations.resize(340, 120)
        self.verticalLayout = QtGui.QVBoxLayout(export_receiver_locations)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_5 = QtGui.QLabel(export_receiver_locations)
        self.label_5.setObjectName("label_5")
        self.verticalLayout.addWidget(self.label_5)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_3 = QtGui.QLabel(export_receiver_locations)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_2.addWidget(self.label_3)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.lineEdit_outfile = QtGui.QLineEdit(export_receiver_locations)
        self.lineEdit_outfile.setObjectName("lineEdit_outfile")
        self.horizontalLayout_2.addWidget(self.lineEdit_outfile)
        self.pushButton_outfile = QtGui.QPushButton(export_receiver_locations)
        self.pushButton_outfile.setObjectName("pushButton_outfile")
        self.horizontalLayout_2.addWidget(self.pushButton_outfile)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.buttonBox = QtGui.QDialogButtonBox(export_receiver_locations)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(export_receiver_locations)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), export_receiver_locations.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), export_receiver_locations.reject)
        QtCore.QMetaObject.connectSlotsByName(export_receiver_locations)

    def retranslateUi(self, export_receiver_locations):
        export_receiver_locations.setWindowTitle(QtGui.QApplication.translate("export_receiver_locations", "Export to ASCII", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setToolTip(QtGui.QApplication.translate("export_receiver_locations", "<html><head/><body><p>Generate simple ASCII output file containing receiver traceIDs and locations known by SeisArray. Can be used as input file for Survey generation or SeisArray generation.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("export_receiver_locations", "Export interpolated receiver locations to a file", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("export_receiver_locations", "Browse for output file:", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_outfile.setText(QtGui.QApplication.translate("export_receiver_locations", "Browse", None, QtGui.QApplication.UnicodeUTF8))

