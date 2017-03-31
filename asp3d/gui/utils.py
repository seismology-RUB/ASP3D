#!/usr/bin/env python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
#   Copyright 2017 Marcel Paffrath (Ruhr-Universitaet Bochum, Germany)
#
#   This file is part of ActiveSeismoPick3D
#----------------------------------------------------------------------------

from PySide import QtCore, QtGui

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, inputlist, header, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.inputlist = inputlist
        self.header = header
        
    def rowCount(self, parent):
        return len(self.inputlist)
    
    def columnCount(self, parent):
        return len(self.inputlist[0])
    
    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        try:
            return self.inputlist[index.row()][index.column()]
        except IndexError:
            return None
    
    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None

    
def openFile(parent, name = 'Open'):
    dialog = QtGui.QFileDialog()
    filename = dialog.getOpenFileName(parent, name)
    if len(filename[0]) > 0:
        return filename[0]
    
def openFiles(parent, name = 'Open'):
    dialog = QtGui.QFileDialog()
    filenames = dialog.getOpenFileNames(parent, name)
    if len(filenames[0]) > 0:
        return filenames[0]

def saveFile(parent, name = 'Save'):
    dialog = QtGui.QFileDialog()
    filename = dialog.getSaveFileName(parent, name)
    if len(filename[0]) > 0:
        return filename[0]

def browseDir(parent, name = 'Open Directory'):
    dialog = QtGui.QFileDialog()
    directory = dialog.getExistingDirectory(parent, name)
    if len(directory) > 0:
        return directory

def getMaxCPU():
    import multiprocessing
    return multiprocessing.cpu_count()

def printDialogMessage(message):
    qmb = QtGui.QMessageBox()
    qmb.setText(message)
    qmb.setStandardButtons(QtGui.QMessageBox.Ok)
    qmb.setIcon(QtGui.QMessageBox.Warning)
    qmb.exec_()

def continueDialogExists(name):
    qmb = QtGui.QMessageBox()
    qmb.setText('%s object already exists. Overwrite?'%name)
    qmb.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
    qmb.setIcon(QtGui.QMessageBox.Warning)
    answer = qmb.exec_()
    if answer == 16384:
        return True
    else:
        return False

def continueDialogMessage(message):
    qmb = QtGui.QMessageBox()
    qmb.setText(message)
    qmb.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
    qmb.setIcon(QtGui.QMessageBox.Warning)
    answer = qmb.exec_()
    if answer == 1024:
        return True
    else:
        return False

def yesNoDialogMessage(message):
    qmb = QtGui.QMessageBox()
    qmb.setText(message)
    qmb.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
    qmb.setIcon(QtGui.QMessageBox.Warning)
    answer = qmb.exec_()
    if answer == 16384:
        return True
    else:
        return False

def yesNoCancelDialogMessage(message):
    qmb = QtGui.QMessageBox()
    qmb.setText(message)
    qmb.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No |
                           QtGui.QMessageBox.Cancel)
    qmb.setIcon(QtGui.QMessageBox.Warning)
    answer = qmb.exec_()
    if answer == 16384:
        return True
    elif answer == 65536:
        return False
    else:
        return

