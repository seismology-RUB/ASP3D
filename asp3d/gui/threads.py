#!/usr/bin/env python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
#   Copyright 2017 Marcel Paffrath (Ruhr-Universitaet Bochum, Germany)
#
#   This file is part of ActiveSeismoPick3D
#----------------------------------------------------------------------------

import os
import multiprocessing
from PySide import QtCore


def setProgressBarBusy(progressBar=None):
    if progressBar:
        progressBar.setVisible(True)
        progressBar.setRange(0, 0)


def hideProgressBar(progressBar=None):
    if progressBar:
        progressBar.setVisible(False)
        progressBar.reset()


class Gen_SeisArray_Thread(QtCore.QThread):
    def __init__(self, parent, SeisArray, recfile, interpolate, progressBar):
        QtCore.QThread.__init__(self, parent)
        self.SeisArray = SeisArray
        self.recfile = recfile
        self.interpolate = interpolate
        self.success = None
        setProgressBarBusy(progressBar)

    def __del__(self):
        self.wait()

    def run(self):
        try:
            self.seisarray = self.SeisArray(self.recfile, self.interpolate)
            self.success = True
        except Exception as e:
            self.success = False
            self._exception = e

    def get_seisarray(self):
        return self.seisarray


class Gen_Survey_from_SA_Thread(QtCore.QThread):
    def __init__(self, parent, Survey, obsdir, seisArray, fstart, fend, progressBar):
        QtCore.QThread.__init__(self, parent)
        self.Survey = Survey
        self.obsdir = obsdir
        self.seisArray = seisArray
        self.fstart = fstart
        self.fend = fend
        self.success = None
        setProgressBarBusy(progressBar)

    def __del__(self):
        self.wait()

    def run(self):
        try:
            self.survey = self.Survey(self.obsdir, seisArray=self.seisArray,
                                      useDefaultParas=False, fstart=self.fstart,
                                      fend=self.fend)
            self.success = True
        except Exception as e:
            self.success = False
            self._exception = e

    def get_survey(self):
        return self.survey


class Gen_Survey_from_SR_Thread(QtCore.QThread):
    def __init__(self, parent, Survey, recfile, srcfile, obsdir, fstart, fend, progressBar):
        QtCore.QThread.__init__(self, parent)
        self.Survey = Survey
        self.recfile = recfile
        self.srcfile = srcfile
        self.obsdir = obsdir
        self.fstart = fstart
        self.fend = fend
        self.success = None
        setProgressBarBusy(progressBar)

    def __del__(self):
        self.wait()

    def run(self):
        try:
            self.survey = self.Survey(self.obsdir, self.srcfile, self.recfile,
                                      useDefaultParas=False,
                                      fstart=self.fstart, fend=self.fend)
            self.success = True
        except Exception as e:
            self.success = False
            self._exception = e

    def get_survey(self):
        return self.survey


class Multipicker_Thread(QtCore.QThread):
    finished = QtCore.Signal(str)

    def __init__(self, parent, func, shotlist, ncores, progressBar=None):
        QtCore.QThread.__init__(self, parent)
        self.progressBar = progressBar
        self.shotlist = shotlist
        self.ncores = ncores
        self.func = func
        self.success = None        
        setProgressBarBusy(self.progressBar)

    def __del__(self):
        self.wait()

    def run(self):
        try:
            pool = multiprocessing.Pool(self.ncores)
            result = pool.map_async(self.func, self.shotlist, callback=self.emitDone)
            pool.close()
            self.success = True
            return result        
        except Exception as e:
            self.success = False
            self._exception = e

    def emitDone(self, result):
        self.finished.emit('Done picking!')
        hideProgressBar(self.progressBar)


class FMTOMO_Thread(QtCore.QThread):
    finished = QtCore.Signal(str)

    def __init__(self, parent, fmtomo_window, interpolationMethod, cwd, fmtomoUtils, progressBar=None):
        QtCore.QThread.__init__(self, parent)
        self.fmtomo_window = fmtomo_window
        self.survey = fmtomo_window.survey
        self.interpolationMethod = interpolationMethod
        self.progressBar = progressBar
        self.cwd = cwd
        self.fmtomoUtils = fmtomoUtils
        self.success = None
        setProgressBarBusy(self.progressBar)

    def __del__(self):
        self.wait()

    def run(self):
        try:
            self.survey.seisarray.generateFMTOMOinputFromArray(self.fmtomo_window.propgrid, self.fmtomo_window.vgrid, (self.fmtomo_window.bbot, self.fmtomo_window.btop),
                                                               self.fmtomo_window.cushionfactor / 100., self.interpolationMethod,
                                                               customgrid=self.fmtomo_window.customgrid, writeVTK=True, showProgress=False)

            os.chdir(self.cwd)
        
            self.tomo = self.fmtomoUtils.Tomo3d(self.fmtomo_window.fmtomo_dir, self.fmtomo_window.simuldir)
            self.tomo.runTOMO3D(self.fmtomo_window.nproc, self.fmtomo_window.nIter)
            self.success = True
        except Exception as e:
            self.success = False
            self._exception = e

        hideProgressBar(self.progressBar)

        
### Works, but only spawns threads that do not seem to run in parallel!
# try:
#     import Queue as queue
# except ImportError:
#     import queue

# class multithread_picker(QtCore.QThread):
#     shutdown = QtCore.Signal(object)
#     def __init__(self, parent, survey, ncores, callback):
#         QtCore.QThread.__init__(self, parent)
#         self.survey = survey
#         self.mainUI = survey.gui.mainUI
#         self.queue = queue.Queue()
#         self.ncores = ncores
#         self.shutdown.connect(callback)
#         self.set_shotlist()
#         self.init_progress()
#         self.threads = []

#     def set_shotlist(self):
#         self.shotlist = self.gen_shotlist(self.survey)

#     def init_progress(self):
#         self.nshots = len(self.shotlist)
#         self.processed = 0
#         self.mainUI.progressBar.setRange(0, self.nshots)
#         self.mainUI.progressBar.setVisible(True)

#     def gen_shotlist(self, survey):
#         shotlist=[]
#         for shot in survey.data.values():
#             for traceID in shot.getTraceIDlist():
#                 shotlist.append((shot, traceID))
#         return shotlist

#     def handle_result(self, result):
#         val = result.val
#         if val is not None:
#             shot, traceID, pick = val
#             shot.setPick(traceID, pick, revised=False)
#             self.processed += 1
#             self.update_progress()
#         else:
#             self.nthreads -= 1
#             self.checkShutdown()

#     def update_progress(self):
#         self.mainUI.progressBar.setValue(self.processed)

#     def checkShutdown(self):
#         if self.nthreads <= 0:
#             self.shutdown.emit(None)#ResultObj(None))
#             hideProgressBar(self.mainUI.progressBar)

#     def process(self):
#         for i in range(self.ncores):
#             thread = PickThread(self.queue, self.handle_result)
#             self.threads.append(thread)
#             thread.start()

#         self.nthreads = len(self.threads)

#         for arg in self.shotlist:
#             self.queue.put(arg)

#         for _ in range(self.ncores): # Tell the workers to shut down
#             self.queue.put(None)


# class ResultObj(QtCore.QObject):
#     def __init__(self, val):
#         self.val = val


# class PickThread(QtCore.QThread):
#     finished = QtCore.Signal(object)
#     shutdown = QtCore.Signal(object)

#     def __init__(self, queue, callback, parent=None):
#         QtCore.QThread.__init__(self, parent)      
#         self.queue = queue
#         self.finished.connect(callback)
#         self.shutdown.connect(callback)

#     def run(self):
#         while True:
#             arg = self.queue.get() 
#             if arg is None: # None means exit
#                 self.shutdown.emit(ResultObj(None))
#                 print("Thread shutting down")
#                 return
#             self.picker(arg)    

#     def picker(self, shotAndTraceID):
#         shot, traceID = shotAndTraceID
#         pick = shot.pickTrace(traceID)
#         self.finished.emit(ResultObj((shot, traceID, pick)))
################################################################################################################################

#### Works giving results back each time worker is finished. Thus handling the results leads to freeze of the gui (also when using ResultHandlingThread).    
# class MultipickerThread(QtCore.QThread):
#     finished = QtCore.Signal(str)
#     def __init__(self, parent, func, survey, ncores, progressBar=None):
#         QtCore.QThread.__init__(self, parent)
#         self.parent = parent
#         self.progressBar = progressBar
#         self.survey = survey
#         self.shotlist = survey.data.values()
#         self.ncores = ncores
#         self.func = func
#         self.progressBar.setVisible(True)
#         self.progressBar.setRange(0, len(self.shotlist))
#         #setProgressBarBusy(self.progressBar)

#     def __del__(self):
#         self.wait()

#     def run(self):
#         pool = multiprocessing.Pool(self.ncores)
#         result = pool.imap(self.func, self.shotlist)
#         for i in range(len(self.shotlist)):
#             for item in self.result.next():
#                 shotnumber, traceID, pick = item
#                 self.survey.getShotForShotnumber(shotnumber).setPick(traceID, pick, revised=False)
#             self.progressBar.setValue(i+1)
#         # hr = HandleResultThread(self.parent, result, self.survey, self.progressBar)
#         # hr.run()
#         pool.close()
#         #return result
#         # pool = multiprocessing.Pool(self.ncores)
#         # result = pool.map_async(self.func, self.shotlist, callback=self.emitDone)
#         # pool.close()
#         # return result

#     def emitDone(self, result):
#         self.finished.emit('Done picking!')
#         hideProgressBar(self.progressBar)

# class HandleResultThread(QtCore.QThread):
#     def __init__(self, parent, result, survey, progressBar=None):
#         QtCore.QThread.__init__(self, parent)
#         self.result = result
#         self.survey = survey
#         self.shotlist = survey.data.values()
#         self.progressBar = progressBar

#     def __del__(self):
#         self.wait()

#     def run(self):
#         for i in range(len(self.shotlist)):
#             for item in self.result.next():
#                 shotnumber, traceID, pick = item
#                 self.survey.getShotForShotnumber(shotnumber).setPick(traceID, pick, revised=False)
#             self.progressBar.setValue(i+1)
################################################################################################################################
