#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import matplotlib
import sys
import os

matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4'] = 'PySide'

from asp3d.core import activeSeismoPick, seismicArrayPreparation
from asp3d.util import surveyUtils
from asp3d.gui.layouts.asp3d_layout import *
from asp3d.gui.windows import Gen_SeisArray_window, Gen_Survey_from_SA_window, Gen_Survey_from_SR_window, \
    Call_autopicker_window, Call_FMTOMO_window, Call_VTK_window, Merge_Shots_window, Postprocessing_window, \
    Export2ascii_window, ExportRecLoc_window, Plot_shot_window, Plot_shots_window
from asp3d.gui.utils import *

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

class GUI(object):
    def __init__(self):
        self.mainwindow = MainWindow
        self.mainUI = ui
        self.connectButtons()
        self.connectActions()
        self.survey = None
        self.seisarray = None
        self.seisArrayFigure = None
        self.cancelpixmap = self.mainwindow.style().standardPixmap(QtGui.QStyle.SP_DialogCancelButton)
        self.applypixmap = self.mainwindow.style().standardPixmap(QtGui.QStyle.SP_DialogApplyButton)
        self.initIcons()
        self.addArrayPlot()
        self.addSurfacePlot()
        self.addStatPlots()
        self.setInitStates()
        self.mainUI.progressBar.setVisible(False)
        self.printSurveyTextbox()
        self.printSeisArrayTextbox()
        self.initWindowObjects()

    def initIcons(self):
        core_dir = os.path.split(activeSeismoPick.__file__)[0]
        maindir = os.path.split(core_dir)[0]
        mainPM = QtGui.QPixmap(os.path.join(maindir, 'gui', 'icon.png'))
        self.mainwindow.setWindowIcon(mainPM)
        
        pmOpen = self.mainwindow.style().standardPixmap(QtGui.QStyle.SP_DirOpenIcon)
        iconOpen = QtGui.QIcon()
        iconOpen.addPixmap(pmOpen)
        
        pmSave = self.mainwindow.style().standardPixmap(QtGui.QStyle.SP_DialogSaveButton)
        iconSave = QtGui.QIcon()
        iconSave.addPixmap(pmSave)

        pmNew = self.mainwindow.style().standardPixmap(QtGui.QStyle.SP_FileIcon)
        iconNew = QtGui.QIcon()
        iconNew.addPixmap(pmNew)

        pmClose = self.mainwindow.style().standardPixmap(QtGui.QStyle.SP_TitleBarCloseButton)
        iconClose = QtGui.QIcon()
        iconClose.addPixmap(pmClose)

        pmWarn = QtGui.QMainWindow().style().standardPixmap(QtGui.QStyle.SP_MessageBoxWarning)
        self.iconWarn = QtGui.QIcon()
        self.iconWarn.addPixmap(pmWarn)

        self.iconClear = QtGui.QIcon()

        self.mainUI.actionGenerate_new_Survey.setIcon(iconNew)
        self.mainUI.actionGenerate_new_Seismic_Array.setIcon(iconNew)
        self.mainUI.actionSave_Survey.setIcon(iconSave)
        self.mainUI.actionSave_Seismic_Array.setIcon(iconSave)        
        self.mainUI.actionLoad_Survey.setIcon(iconOpen)
        self.mainUI.actionLoad_Seismic_Array.setIcon(iconOpen)
        self.mainUI.actionExit.setIcon(iconClose)
        
    def initWindowObjects(self):
        self.gsa = None
        self.gssa = None
        self.gssr = None
        self.autopicker = None
        self.fmtomo = None
        self.vtktools = None
        self.mergeshots = None
        self.postprocessing = None
        self.export2ascii = None
        self.exportRec = None
        self.pmsw = None

    def setInitStates(self):
        self.setPickState(False)
        self.setSurveyState(False)
        self.setSeisArrayState(False)
        self.setConnected2SurveyState(False)

    def connectButtons(self):
        QtCore.QObject.connect(self.mainUI.actionGenerate_new_Seismic_Array, QtCore.SIGNAL("triggered()"),
                               self.gen_seisarray)
        QtCore.QObject.connect(self.mainUI.actionLoad_Seismic_Array, QtCore.SIGNAL("triggered()"),
                               self.load_seisarray_dialog)
        QtCore.QObject.connect(self.mainUI.actionSave_Seismic_Array, QtCore.SIGNAL("triggered()"), self.save_seisarray)
        QtCore.QObject.connect(self.mainUI.actionLoad_Survey, QtCore.SIGNAL("triggered()"), self.load_survey_dialog)
        QtCore.QObject.connect(self.mainUI.actionSave_Survey, QtCore.SIGNAL("triggered()"), self.save_survey)
        QtCore.QObject.connect(self.mainUI.actionConnect_to_Survey, QtCore.SIGNAL("triggered()"), self.connect2Survey)
        QtCore.QObject.connect(self.mainUI.actionInterpolate_Receivers, QtCore.SIGNAL("triggered()"),
                               self.interpolate_receivers)
        QtCore.QObject.connect(self.mainUI.actionGenerate_new_Survey, QtCore.SIGNAL("triggered()"), self.gen_survey)
        QtCore.QObject.connect(self.mainUI.actionAutomatic_Picking, QtCore.SIGNAL("triggered()"), self.startPicker)
        QtCore.QObject.connect(self.mainUI.actionPostprocessing, QtCore.SIGNAL("triggered()"), self.postprocessing)
        QtCore.QObject.connect(self.mainUI.actionASCII_File, QtCore.SIGNAL("triggered()"), self.exportPicks2ASCII)
        QtCore.QObject.connect(self.mainUI.actionExport_Receiver_Locations, QtCore.SIGNAL("triggered()"),
                               self.exportRecLocs)
        QtCore.QObject.connect(self.mainUI.actionStart_FMTOMO_Simulation, QtCore.SIGNAL("triggered()"),
                               self.startFMTOMO)
        QtCore.QObject.connect(self.mainUI.actionVTK_Visualization, QtCore.SIGNAL("triggered()"), self.startVTKtools)
        QtCore.QObject.connect(self.mainUI.actionMerge_Shots, QtCore.SIGNAL("triggered()"), self.startMergeShots)
        QtCore.QObject.connect(self.mainUI.actionExit, QtCore.SIGNAL("triggered()"),
                               app.closeAllWindows)  # self.exitApp)
        QtCore.QObject.connect(self.mainUI.actionFullscreen, QtCore.SIGNAL("triggered()"), self.fullscreen)
        QtCore.QObject.connect(self.mainUI.actionPlotAllShots, QtCore.SIGNAL("triggered()"), self.plotAllShots)
        QtCore.QObject.connect(self.mainUI.comboBox_stats, QtCore.SIGNAL("activated(int)"), self.refreshPickedWidgets)
        QtCore.QObject.connect(self.mainUI.shot_left, QtCore.SIGNAL("clicked()"), self.decreaseShotnumber)
        QtCore.QObject.connect(self.mainUI.shot_right, QtCore.SIGNAL("clicked()"), self.increaseShotnumber)
        QtCore.QObject.connect(self.mainUI.plot_shot, QtCore.SIGNAL("clicked()"), self.plotSingleShot)

    def connectActions(self):
        self.mainUI.textBox_terminal_err.textChanged.connect(self.warnError)
        self.mainUI.textBox_terminal_err.selectionChanged.connect(self.clearError)
        self.mainUI.tabWidget.currentChanged[int].connect(self.clearError)
        self.mainUI.textBox_terminal.textChanged.connect(self.scrollTextbox)
        self.mainUI.textBox_terminal_err.textChanged.connect(self.scrollTextbox_err)        

    def scrollTextbox(self):
        self.mainUI.textBox_terminal.moveCursor(QtGui.QTextCursor.End)
        
    def scrollTextbox_err(self):
        self.mainUI.textBox_terminal_err.moveCursor(QtGui.QTextCursor.End)
        
    def warnError(self):
        self.mainUI.tabWidget.setTabIcon(1, self.iconWarn)

    def clearError(self):
        self.mainUI.tabWidget.setTabIcon(1, self.iconClear)
        
    def fullscreen(self):
        if self.mainUI.actionFullscreen.isChecked():
            MainWindow.showFullScreen()
        else:
            MainWindow.showNormal()

    def gen_seisarray(self):
        self.disconnectSA = False
        if self.checkSeisArrayState():
            if not continueDialogExists('Seismic Array'):
                return
        if self.checkConnected2SurveyState():
            if not continueDialogMessage('Seismic Array connected to present Survey.\n'
                                         'Continuation will disconnect the Seismic Array.'):
                return
            else:
                self.survey.seisarray = None
                self.disconnectSA = True

        if self.gsa is None:
            self.gsa = Gen_SeisArray_window(self.mainwindow, self.mainUI)
        else:
            self.gsa.start_dialog()

        if self.gsa.executed:
            self.gsa.gen_SA_thread.connect(self.gsa.gen_SA_thread, QtCore.SIGNAL("finished()"), self.activate_seisarray)

    def activate_seisarray(self):
        if self.gsa.gen_SA_thread.success:
            print('Setting SeisArray status to active.')
            self.seisarray = self.gsa.get_seisarray()
            if self.disconnectSA:
                self.setConnected2SurveyState(False)
            self.setSeisArrayState(True)

    def gen_survey(self):
        if self.checkSurveyState():
            if not continueDialogExists('Survey'):
                return
        if self.checkSeisArrayState():
            if len(self.seisarray.getSourceCoordinates()) > 0:
                if yesNoDialogMessage('Use geometry information of active Seismic Array?'):
                    if self.gssa is None:
                        self.gssa = Gen_Survey_from_SA_window(self.mainwindow, self.mainUI, self.seisarray)
                    else:
                        self.gssa.start_dialog()
                        self.gssa.update_seisarray(self.seisarray)
                    if self.gssa.executed:
                        self.gssa.gsa_thread.connect(self.gssa.gsa_thread, QtCore.SIGNAL("finished()"),
                                                     self.activate_survey_sa)
                    return
            else:
                if not printDialogMessage('Can not use current Seismic Array,'
                                          ' because there are no sources given.'):
                    return
        if self.gssr is None:
            self.gssr = Gen_Survey_from_SR_window(self.mainwindow, self.mainUI)
        else:
            self.gssr.start_dialog()
        if self.gssr.executed:
            self.gssr.gsr_thread.connect(self.gssr.gsr_thread, QtCore.SIGNAL("finished()"), self.activate_survey_sr)

    def activate_survey_sa(self):
        if self.gssa.gsa_thread.success:
            self.survey = self.gssa.get_survey()
            print('Setting Survey status to active.')
            self.initNewSurvey()
            self.setConnected2SurveyState(True)
            self.setPickState(False)

    def activate_survey_sr(self):
        if self.gssr.gsr_thread.success:
            del self.survey
            del self.seisarray
            self.survey = self.gssr.get_survey()
            self.seisarray = self.survey.seisarray
            print('Setting Survey status to active.')
            self.initNewSurvey()
            self.setSeisArrayState(True)
            self.setConnected2SurveyState(True)

    def initNewSurvey(self):
        self.survey.setArtificialPick(0, 0)  # artificial pick at source origin
        self.setSurveyState(True)
        self.setPickState(False)

    def addArrayPlot(self):
        self.seisArrayFigure = Figure()
        self.seisArrayCanvas = FigureCanvas(self.seisArrayFigure)
        self.seisArrayToolbar = NavigationToolbar(self.seisArrayCanvas, self.mainwindow)
        self.mainUI.verticalLayout_sa_tbar.addWidget(self.seisArrayToolbar)
        self.mainUI.verticalLayout_sa_plot.addWidget(self.seisArrayCanvas)
        self.seisArrayToolbar.setOrientation(QtCore.Qt.Vertical)
        self.seisArrayToolbar.setFixedWidth(35)

    def addSurfacePlot(self):
        self.surfaceFigure = Figure()
        self.surfaceCanvas = FigureCanvas(self.surfaceFigure)
        self.mainUI.horizontalLayout_surf.addWidget(self.surfaceCanvas)

    def addStatPlots(self):
        self.statFigure_left = Figure()
        self.statCanvas_left = FigureCanvas(self.statFigure_left)
        self.statToolbar_left = NavigationToolbar(self.statCanvas_left, self.mainwindow)
        self.mainUI.verticalLayout_rec_tbar.addWidget(self.statToolbar_left)
        self.mainUI.verticalLayout_rec_plot.addWidget(self.statCanvas_left)
        self.statToolbar_left.setOrientation(QtCore.Qt.Vertical)
        self.statToolbar_left.setFixedWidth(35)

        self.statFigure_right = Figure()
        self.statCanvas_right = FigureCanvas(self.statFigure_right)
        self.statToolbar_right = NavigationToolbar(self.statCanvas_right, self.mainwindow)
        self.mainUI.verticalLayout_shot_tbar.addWidget(self.statToolbar_right)
        self.mainUI.verticalLayout_shot_plot.addWidget(self.statCanvas_right)
        self.statToolbar_right.setOrientation(QtCore.Qt.Vertical)
        self.statToolbar_right.setFixedWidth(35)

        self.addItems2StatsComboBox()

    def addItems2StatsComboBox(self):
        self.mainUI.comboBox_stats.insertItem(0, 'picked traces')
        self.mainUI.comboBox_stats.insertItem(1, 'mean SNR')
        self.mainUI.comboBox_stats.insertItem(2, 'median SNR')
        self.mainUI.comboBox_stats.insertItem(3, 'mean SPE')
        self.mainUI.comboBox_stats.insertItem(4, 'median SPE')
        self.enablePickedTools(False)

    def addItems2ShotsComboBox(self):
        shotnumbers = list(self.survey.data.keys())
        shotnumbers.sort()
        for index, shotnumber in enumerate(shotnumbers):
            self.mainUI.comboBox_shots.insertItem(index, 'Shot: %s' % shotnumber)
        self.mainUI.comboBox_shots.setMaxCount(len(shotnumbers))
        
    def increaseShotnumber(self):
        currentIndex = self.mainUI.comboBox_shots.currentIndex()
        maxindex = self.mainUI.comboBox_shots.maxCount() - 1
        if currentIndex == maxindex:
            self.mainUI.comboBox_shots.setCurrentIndex(0)
        else:
            self.mainUI.comboBox_shots.setCurrentIndex(currentIndex + 1)

    def decreaseShotnumber(self):
        currentIndex = self.mainUI.comboBox_shots.currentIndex()
        maxindex = self.mainUI.comboBox_shots.maxCount() - 1
        if currentIndex == 0:
            self.mainUI.comboBox_shots.setCurrentIndex(maxindex)
        else:
            self.mainUI.comboBox_shots.setCurrentIndex(currentIndex - 1)

    def plotSingleShot(self):
        try:
            shotnumber = int(self.mainUI.comboBox_shots.currentText().split()[1])
        except IndexError:
            QtGui.QMessageBox.information(self.mainwindow, "Warning!", "Could not find corresponding Shot!")
            return
        self.psw = Plot_shot_window(self, self.survey, shotnumber)
        QtCore.QObject.connect(self.psw.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.refreshPickedWidgets)
        self.psw.plot()

    def plotAllShots(self):
        if self.pmsw is None:
            if not continueDialogMessage('Warning: Plotting all {} shots is not yet a thread and generates a figure window '
                                         'for each shot which might be very ressource intensive. '
                                         'Do you want to continue? (Please do not panic '
                                         'if the GUI freezes for a minute.)'.format(len(self.survey.data))):
                return
            self.pmsw = Plot_shots_window(self, self.survey)
            QtCore.QObject.connect(self.pmsw.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.refreshPickedWidgets)
            self.pmsw.plot()
        else:
            self.pmsw.start_widget()

    def addArrayAxes(self):
        self.seisArrayAx = self.seisArrayFigure.add_subplot(111)

    def addSurfaceAxes(self):
        self.surfaceAx = self.surfaceFigure.add_subplot(111, projection='3d')

    def addStatAxes(self):
        self.statAx_left = self.statFigure_left.add_subplot(111)
        self.statAx_right = self.statFigure_right.add_subplot(111)

    def enablePickedTools(self, bool, twoDim=False):
        self.mainUI.comboBox_stats.setEnabled(bool)
        self.statToolbar_left.setEnabled(bool)
        self.statToolbar_right.setEnabled(bool)
        if not twoDim:
            self.mainUI.comboBox_shots.setEnabled(bool)
            self.mainUI.shot_left.setEnabled(bool)
            self.mainUI.shot_right.setEnabled(bool)
            self.mainUI.plot_shot.setEnabled(bool)
        if bool == False:
            self.mainUI.comboBox_shots.clear()

    def replotArray(self):
        self.seisArrayFigure.clf()
        self.addArrayAxes()
        self.plotArray()
        self.seisArrayCanvas.draw()

    def replotSurface(self):
        self.surfaceFigure.clf()
        self.addSurfaceAxes()
        self.plotSurface()
        self.surfaceCanvas.draw()

    def plotArray(self):
        self.seisarray.plotArray2D(self.seisArrayAx, highlight_measured=True, plot_topo=True,
                                   twoDim=self.seisarray.twoDim)

    def plotSurface(self):
        if not self.seisarray.twoDim:
            self.seisarray.plotSurface3D(ax=self.surfaceAx, exag=True)
        self.seisarray.plotArray3D(ax=self.surfaceAx, legend=False, markersize=3)

    def InitPickedWidgets(self):
        if self.checkPickState():
            surveyUtils.plotScatterStats4Receivers(self.survey, self.mainUI.comboBox_stats.currentText(),
                                                   self.statAx_left, twoDim=self.survey.twoDim)
            surveyUtils.plotScatterStats4Shots(self.survey, self.mainUI.comboBox_stats.currentText(),
                                               self.statAx_right, twoDim=self.survey.twoDim)
            self.addItems2ShotsComboBox()

    def refreshPickedWidgets(self):
        self.currentShotIndex = self.mainUI.comboBox_shots.currentIndex()
        self.clearPickFigures()
        self.addStatAxes()
        self.InitPickedWidgets()
        self.drawPickFigures()
        self.mainUI.comboBox_shots.setCurrentIndex(self.currentShotIndex)
        self.printSurveyTextbox(False)
        self.psw = None

    def printSurveyTextbox(self, init=True):
        if init == True:
            surveytup = (0, 0, 0, 0, 0)
        else:
            survey = self.survey
            nshots = len(survey.getShotlist())
            tt = survey.countAllTraces()
            pt = survey.countAllPickedTraces()
            rt = survey.countAllRevisedTraces()
            rate = float(pt) / float(tt) * 100
            surveytup = (nshots, tt, pt, rate, rt)
        surveyTitle = 'SURVEY:\n'
        surveyText = 'Number of Sources: %s\nTotal Traces: %s\nPicked Traces: %s (%4.2f%%)\n' \
                     'Manually Revised Traces: %s' % surveytup
        string = surveyTitle + surveyText
        self.mainUI.textBox_survey.setText(string)

    def printSeisArrayTextbox(self, init=True):
        if init == True:
            seistup = (0, 0, 0)
        else:
            seisarray = self.seisarray
            nshots = len(seisarray.getSourceCoordinates())
            nrec = len(seisarray.getReceiverCoordinates())
            nadd = len(seisarray.getMeasuredTopo())
            seistup = (nshots, nrec, nadd)
        seisArrayTitle = 'SEISARRAY:\n'
        seisArrayText = 'Sources: %s\nReceivers: %s\nAdditional Points:%s' % seistup
        string = seisArrayTitle + seisArrayText
        self.mainUI.textBox_seisarray.setText(string)

    def interpolate_receivers(self):
        if not self.checkSeisArrayState():
            printDialogMessage('No Seismic Array defined.')
            return
        self.seisarray.interpolateAll()
        self.refreshSeisArrayWidgets()

    def refreshSeisArrayWidgets(self):
        self.replotArray()
        self.replotSurface()
        self.printSeisArrayTextbox(init=False)

    def connect2Survey(self):
        if not self.checkSurveyState():
            printDialogMessage('No Survey defined.')
            return
        if not self.checkSeisArrayState():
            printDialogMessage('Got no Seismic Array.')
            return
        if self.checkConnected2SurveyState():
            if not yesNoDialogMessage('Existing Survey already got Seismic Array object. Continue?'):
                return
        self.survey.seisarray = self.seisarray
        self.setConnected2SurveyState(True)
        self.survey._initiate_SRfiles()
        self.printSurveyTextbox(init=False)
        print('Connected Seismic Array to active Survey. It is now part of the Survey object.')
        QtGui.QMessageBox.information(self.mainwindow, "Done!", "Done connecting Seismic Array to Survey object!")

    def startPicker(self):
        if not self.checkSurveyState():
            printDialogMessage('No Survey defined.')
            return

        if self.autopicker is None:
            self.autopicker = Call_autopicker_window(gui=self, survey=self.survey)
        else:
            self.autopicker.start_dialog(repick=True)
            self.autopicker.update_survey(self.survey)
        if not self.autopicker.threading:
            self.finishAutopicker()

    def finishAutopicker(self):
        if self.autopicker.executed:
            self.setPickState(True)
            self.printSurveyTextbox(init=False)

    def startFMTOMO(self):
        if not self.checkSurveyState():
            printDialogMessage('No Survey defined.')
            return
        if not self.checkPickState():
            printDialogMessage('Survey not picked.')
            return

        if self.fmtomo is None:
            self.fmtomo = Call_FMTOMO_window(self.mainwindow, self.mainUI, self.survey)
        else:
            self.fmtomo.start_dialog()
            self.fmtomo.update_survey(self.survey)

    def startVTKtools(self):
        if self.vtktools is None:
            self.vtktools = Call_VTK_window(self.mainwindow)
        else:
            self.vtktools.start_dialog()

    def startMergeShots(self):
        if self.mergeshots is None:
            self.mergeshots = Merge_Shots_window(self.mainwindow)
        else:
            self.mergeshots.start_dialog()

    def postprocessing(self):
        if not self.checkSurveyState():
            printDialogMessage('No Survey defined.')
            return
        if not self.checkPickState():
            printDialogMessage('No Picks found.')
            return
        self.postprocessing = Postprocessing_window(self, self.survey)
        # self.survey.plotAllPicks()
        # self.refreshPickedWidgets() # wait until finished

    # def repicking(self):
    #     region = self.postprocessing.getRegion()
    #     self.repicking = []
    #     for shot in region.getShotsFound():
    #         for traceID in 
    #         self.repicking.append(Repicking(self.mainwindow, region, shot

    def exportPicks2ASCII(self):
        if not self.checkSurveyState():
            printDialogMessage('No Survey defined.')
            return
        if not self.checkPickState():
            printDialogMessage('No Picks found.')
            return
        if self.export2ascii is None:
            self.export2ascii = Export2ascii_window(gui=self, survey=self.survey)
        else:
            self.export2ascii.start_dialog()

    def exportRecLocs(self):
        if not self.checkSeisArrayState():
            printDialogMessage('No SeisArray defined.')
            return
        if self.exportRec is None:
            self.exportRec = ExportRecLoc_window(gui=self, seisarray=self.seisarray)
        else:
            self.exportRec.start_dialog()

    def load_survey_dialog(self):
        if self.checkSurveyState():
            if not continueDialogExists('Survey'):
                return
        filename = openFile(self.mainwindow, 'Load Survey object from file')
        if filename is None:
            return
        self.load_survey(filename)

    def load_survey(self, filename):
        try:
            survey = activeSeismoPick.Survey.from_pickle(filename)
        except:
            printDialogMessage('Could not load object %s.' % filename)
            return
        if not type(survey) == activeSeismoPick.Survey:
            printDialogMessage('Wrong input file of type %s, expected %s.'
                               % (type(survey), activeSeismoPick.Survey))
            return
        if self.checkSeisArrayState() and survey.seisarray is not None:
            if not yesNoDialogMessage('Survey got existing Seismic Array.'
                                      ' Do you want to overwrite the current Seismic Array?'):
                printDialogMessage('Aborted.')
                return
        try:
            del(self.survey)
        except:
            pass
        self.survey = survey
        self.setSurveyState(True)
        if self.survey.picked:
            self.setPickState(True)
        else:
            self.setPickState(False)
        if self.survey.seisarray != None:
            self.seisarray = self.survey.seisarray
            self.setConnected2SurveyState(True)
            self.setSeisArrayState(True)
            printDialogMessage('Loaded Survey with active Seismic Array.')
        else:
            self.setConnected2SurveyState(False)
            self.setSeisArrayState(False)
            printDialogMessage('Loaded Survey.')

    def load_seisarray_dialog(self):
        self.disconnectSA = False
        if self.checkSeisArrayState():
            if not continueDialogExists('Seismic Array'):
                return
        if self.checkConnected2SurveyState():
            if not continueDialogMessage('Seismic Array connected to present Survey.\n'
                                         'Continuation will disconnect the Seismic Array.'):
                return
            else:
                self.survey.seisarray = None
                self.disconnectSA = True

        filename = openFile(self.mainwindow, 'Load SeisArray object from file')
        if filename is None:
            return
        self.load_seisarray(filename, self.disconnectSA)

    def load_seisarray(self, filename, disconnect):
        try:
            seisarray = seismicArrayPreparation.SeisArray.from_pickle(filename)
        except:
            printDialogMessage('Could not load object %s.' % filename)
            return
        if not type(seisarray) == seismicArrayPreparation.SeisArray:
            printDialogMessage('Wrong input file of type %s, expected %s.'
                               % (type(seisarray), seismicArrayPreparation.SeisArray))
            return
        if disconnect:
            self.setConnected2SurveyState(False)
        self.seisarray = seisarray
        self.setSeisArrayState(True)

    def save_seisarray(self):
        if not self.checkSeisArrayState():
            printDialogMessage('No Seismic Array defined.')
            return
        filename = saveFile(self.mainwindow, 'Choose output filename for SeisArray object')
        if filename is None:
            return
        self.seisarray.saveSeisArray(filename)

    def save_survey(self):
        if not self.checkSurveyState():
            printDialogMessage('No Survey defined.')
            return
        filename = saveFile(self.mainwindow, 'Choose output filename for Survey object')
        if filename is None:
            return
        self.survey.saveSurvey(filename)
        return True

    def setSurveyState(self, state):
        if state == True:
            self.mainUI.survey_active.setPixmap(self.applypixmap)
            self.printSurveyTextbox(init=False)
        elif state == False:
            self.mainUI.survey_active.setPixmap(self.cancelpixmap)

    def checkSurveyState(self):
        if self.survey == None:
            return False
        else:
            return True

    def checkSeisArrayState(self):
        if self.seisarray == None:
            return False
        else:
            return True

    def setPickState(self, state):
        if state == True and self.checkSurveyState():
            self.mainUI.picked_active.setPixmap(self.applypixmap)
            self.refreshPickedWidgets()
            self.enablePickedTools(True, self.survey.twoDim)
            self.survey.picked = True
        elif state == True and self.checkSurveyState() is False:
            printDialogMessage('No Survey defined.')
            return
        elif state == False:
            self.mainUI.picked_active.setPixmap(self.cancelpixmap)
            if self.checkSurveyState():
                self.clearPickFigures()
                self.drawPickFigures()
                self.enablePickedTools(False)
                self.survey.picked = False

    def clearPickFigures(self):
        self.statFigure_left.clf()
        self.statFigure_right.clf()

    def drawPickFigures(self):
        self.statCanvas_left.draw()
        self.statCanvas_right.draw()

    def setSeisArrayState(self, state):
        if state == True:
            self.mainUI.seisarray_active.setPixmap(self.applypixmap)
            self.refreshSeisArrayWidgets()
            self.seisArrayToolbar.setEnabled(True)
        elif state == False:
            self.mainUI.seisarray_active.setPixmap(self.cancelpixmap)
            self.seisArrayToolbar.setEnabled(False)
            if self.seisArrayFigure is not None:
                self.seisArrayFigure.clf()

    def setConnected2SurveyState(self, state):
        if state == True:
            self.mainUI.seisarray_on_survey_active.setPixmap(self.applypixmap)
        elif state == False:
            self.mainUI.seisarray_on_survey_active.setPixmap(self.cancelpixmap)

    def checkConnected2SurveyState(self):
        if self.checkSurveyState():
            if self.survey.seisarray != None:
                return True
        else:
            return False

    def checkPickState(self):
        if not self.survey:
            printDialogMessage('No Survey defined.')
            return
        return self.survey.picked

    def exitApp(self):
        if self.checkSurveyState():
            ans = yesNoCancelDialogMessage('Do you want to save the current Survey?')
            if ans == None:
                return
            elif ans == True:
                if not self.save_survey():
                    return
        QtCore.QCoreApplication.instance().quit()


class EmittingStream(QtCore.QObject):
    textWritten = QtCore.Signal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass


class My_mainwindow(QtGui.QMainWindow):
    def __init__(self, debug_mode=False):
        super(My_mainwindow, self).__init__()
        #check for ipython, which does not work with redirecting stdout and stderr
        if not debug_mode:
            self.connectStdout()
            
    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Message',
                                           "Are you sure to quit ActiveSeismoPick3D?", QtGui.QMessageBox.Yes |
                                           QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            if not gui.exitApp():
                event.ignore()
        else:
            event.ignore()

    def writeOutputToTextOut(self, text):
        ui.textBox_terminal.append(text)

    def writeOutputToTextErr(self, text):
        ui.textBox_terminal_err.append(text)

    def connectStdout(self):
        sys.stdout = EmittingStream()
        sys.stderr = EmittingStream()
        self.connect(sys.stdout, QtCore.SIGNAL('textWritten(QString)'), self.writeOutputToTextOut)
        self.connect(sys.stderr, QtCore.SIGNAL('textWritten(QString)'), self.writeOutputToTextErr)

    def disconnectStdout(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        self.disconnect(sys.stdout, QtCore.SIGNAL('textWritten(QString)'), self.writeOutputToTextOut)
        self.disconnect(sys.stderr, QtCore.SIGNAL('textWritten(QString)'), self.writeOutputToTextErr)
        


def create_window(window_class, debug_mode=False):
    app_created = False
    app = QtCore.QCoreApplication.instance()
    #check for existing app (when using ipython)
    if app is None:
        app = QtGui.QApplication(sys.argv)
        app_created = True
    app.references = set()
    if not app_created or debug_mode:
        window = window_class(True)
    else:
        window = window_class(False)
    app.references.add(window)
    window.show()
    return window, app, app_created


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Load existing Survey or SeisArray object.')
    parser.add_argument('-s', dest='filename_survey', help='Survey input file',
                        default=None)
    parser.add_argument('-a', dest='filename_seisarray', help='Seisarray input file',
                        default=None)
    parser.add_argument('--debug-mode', dest='debug_mode', action='store_true', help='Plot output to terminal',
                        default=False)
    args = parser.parse_args()
    MainWindow, app, app_created = create_window(My_mainwindow, args.debug_mode)
    # MainWindow = My_mainwindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.showMaximized()
    gui = GUI()
    if args.filename_survey:
        gui.load_survey(args.filename_survey)
    if args.filename_seisarray:
        gui.load_seisarray(args.filename_seisarray, disconnect=True)
    if app_created:
        sys.exit(app.exec_())
