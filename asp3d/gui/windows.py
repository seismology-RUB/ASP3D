#!/usr/bin/env python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
#   Copyright 2017 Marcel Paffrath (Ruhr-Universitaet Bochum, Germany)
#
#   This file is part of ActiveSeismoPick3D
#----------------------------------------------------------------------------

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
from obspy.core import read as obsread

from asp3d.core.activeSeismoPick import Survey
from asp3d.core.seismicArrayPreparation import SeisArray
from asp3d.core.postprocessing import regions
from asp3d.gui.layouts.export2ascii_layout import Ui_export2ascii
from asp3d.gui.layouts.export_receiver_locations_layout import Ui_export_receiver_locations
from asp3d.gui.layouts.fmtomo_parameters_layout import Ui_fmtomo_parameters
from asp3d.gui.layouts.generate_seisarray_layout import Ui_generate_seisarray
from asp3d.gui.layouts.generate_survey_layout import Ui_generate_survey
from asp3d.gui.layouts.generate_survey_layout_minimal import Ui_generate_survey_minimal
from asp3d.gui.layouts.merge_shots_layout import Ui_merge_shots
from asp3d.gui.layouts.picking_parameters_layout import Ui_picking_parameters
from asp3d.gui.layouts.plot_shots_layout import Ui_plot_shots
from asp3d.gui.layouts.postprocessing_layout import Ui_postprocessing
from asp3d.gui.layouts.repicking_layout import Ui_repicking
from asp3d.gui.layouts.vtk_tools_layout import Ui_vtk_tools
from asp3d.gui.utils import *
from asp3d.util import fmtomoUtils, surveyUtils
from asp3d.gui.threads import Gen_SeisArray_Thread, Gen_Survey_from_SA_Thread, Gen_Survey_from_SR_Thread, FMTOMO_Thread, hideProgressBar

matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4'] = 'PySide'

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class Gen_SeisArray_window(object):
    def __init__(self, mainwindow, mainUI):
        self.mainwindow = mainwindow
        self.mainUI = mainUI
        self.seisarray = None
        self.srcfile = None
        self.recfile = None
        self.ptsfile = None
        self.init_dialog()
        self.start_dialog()

    def init_dialog(self):
        qdialog = QtGui.QDialog(self.mainwindow)
        ui = Ui_generate_seisarray()
        ui.setupUi(qdialog)
        self.ui = ui
        self.qdialog = qdialog
        self.connectButtons()

    def start_dialog(self):
        if self.qdialog.exec_():
            self.refresh_selection()
            if self.ui.radioButton_interpolatable.isChecked():
                self.gen_SA_thread = Gen_SeisArray_Thread(self.mainwindow, SeisArray, self.recfile, True,
                                                          self.mainUI.progressBar)
                # self.seisarray = seismicArrayPreparation.SeisArray(self.recfile, True)
            elif self.ui.radioButton_normal.isChecked():
                self.gen_SA_thread = Gen_SeisArray_Thread(self.mainwindow, SeisArray, self.recfile, False,
                                                          self.mainUI.progressBar)
                # self.seisarray = seismicArrayPreparation.SeisArray(self.recfile, False)
            self.gen_SA_thread.start()
            self.executed = True
            self.gen_SA_thread.connect(self.gen_SA_thread, QtCore.SIGNAL("finished()"), self._finalizeSeisarray)
        else:
            self.refresh_selection()
            self.executed = False

    def refresh_selection(self):
        self.srcfile = self.ui.lineEdit_src.text()
        self.recfile = self.ui.lineEdit_rec.text()
        self.ptsfile = self.ui.lineEdit_pts.text()

    def get_seisarray(self):
        if self.seisarray is not None:
            return self.seisarray

    def connectButtons(self):
        QtCore.QObject.connect(self.ui.pushButton_rec, QtCore.SIGNAL("clicked()"), self.chooseMeasuredRec)
        QtCore.QObject.connect(self.ui.pushButton_src, QtCore.SIGNAL("clicked()"), self.chooseMeasuredSrc)
        QtCore.QObject.connect(self.ui.pushButton_obs, QtCore.SIGNAL("clicked()"), self.chooseMeasuredPts)

    def chooseMeasuredSrc(self):
        text=openFile(self.mainwindow, 'Open measured sources file')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_src.setText(text)

    def chooseMeasuredRec(self):
        text=openFile(self.mainwindow, 'Open measured receivers file')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_rec.setText(text)

    def chooseMeasuredPts(self):
        text=openFile(self.mainwindow, 'Open measured points file')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_pts.setText(text)

    def _finalizeSeisarray(self):
        hideProgressBar(self.mainUI.progressBar)
        if self.gen_SA_thread.success:
            self.seisarray = self.gen_SA_thread.get_seisarray()
            if len(self.srcfile) > 0:
                self.seisarray.addSourceLocations(self.srcfile)
            if len(self.ptsfile) > 0:
                self.seisarray.addMeasuredTopographyPoints(self.ptsfile)
            QtGui.QMessageBox.information(self.mainwindow, "Done!", "Done generating SeisArray object!")
        else:
            exception = self.gen_SA_thread._exception
            QtGui.QMessageBox.information(self.mainwindow, "Done!", "Could not generate SeisArray object!\nReason:{}".format(exception))
            raise exception
        
        
class Gen_Survey_from_SA_window(object):
    def __init__(self, mainwindow, mainUI, seisarray):
        self.mainwindow = mainwindow
        self.mainUI = mainUI
        self.seisarray = seisarray
        self.survey = None
        self.obsdir = None
        self.fstart = 'shot'
        self.fend = '.dat'
        self.init_dialog()
        self.start_dialog()

    def init_dialog(self):
        qdialog = QtGui.QDialog(self.mainwindow)
        ui = Ui_generate_survey_minimal()
        ui.setupUi(qdialog)
        self.ui = ui
        self.qdialog = qdialog
        self.connectButtons()

    def start_dialog(self):
        if self.qdialog.exec_():
            self.refresh_selection()
            self.gsa_thread = Gen_Survey_from_SA_Thread(self.mainwindow, Survey, self.obsdir, self.seisarray,
                                                        self.fstart, self.fend, self.mainUI.progressBar)
            self.gsa_thread.start()
            self.executed = True
            self.gsa_thread.connect(self.gsa_thread, QtCore.SIGNAL("finished()"), self._finalizeSurvey)
        else:
            self.refresh_selection()
            self.executed = False

    def update_seisarray(self, seisarray):
        self.seisarray = seisarray

    def refresh_selection(self):
        self.obsdir = self.ui.lineEdit_obs.text()
        self.fstart = self.ui.fstart.text()
        self.fend = self.ui.fend.text()

    def get_survey(self):
        return self.survey

    def connectButtons(self):
        QtCore.QObject.connect(self.ui.pushButton_obs, QtCore.SIGNAL("clicked()"), self.chooseObsdir)

    def chooseObsdir(self):
        text=browseDir(self.mainwindow, 'Choose directory containing waveform data.')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_obs.setText(text)

    def _finalizeSurvey(self):
        hideProgressBar(self.mainUI.progressBar)
        if self.gsa_thread.success:
            self.survey = self.gsa_thread.get_survey()
            QtGui.QMessageBox.information(self.mainwindow, "Done!", "Done generating Survey object!")
        else:
            exception = self.gsa_thread._exception
            QtGui.QMessageBox.information(self.mainwindow, "Error!", "Could not generate Survey object!\nReason:{}".format(exception))
            raise exception
        

class Gen_Survey_from_SR_window(object):
    def __init__(self, mainwindow, mainUI):
        self.mainwindow = mainwindow
        self.mainUI = mainUI
        self.survey = None
        self.obsdir = None
        self.srcfile = None
        self.recfile = None
        self.fstart = 'shot'
        self.fend = '.dat'
        self.init_dialog()
        self.start_dialog()

    def init_dialog(self):
        qdialog = QtGui.QDialog(self.mainwindow)
        ui = Ui_generate_survey()
        ui.setupUi(qdialog)
        self.ui = ui
        self.qdialog = qdialog
        self.connectButtons()

    def start_dialog(self):
        if self.qdialog.exec_():
            self.refresh_selection()
            if not self.check_selection():
                self.executed = False
                printDialogMessage('Could not create Survey. Not enough input files given.')
                return
            try:
                del(self.survey)
            except:
                self.survey = None
            self.gsr_thread = Gen_Survey_from_SR_Thread(self.mainwindow, Survey, self.recfile, self.srcfile,
                                                        self.obsdir, self.fstart, self.fend, self.mainUI.progressBar)
            self.gsr_thread.start()
            self.executed = True
            self.gsr_thread.connect(self.gsr_thread, QtCore.SIGNAL("finished()"), self._finalizeSurvey)
        else:
            self.refresh_selection()
            self.executed = False

    def refresh_selection(self):
        self.obsdir = self.ui.lineEdit_obs.text()
        self.srcfile = self.ui.lineEdit_src.text()
        self.recfile = self.ui.lineEdit_rec.text()
        self.fstart = self.ui.fstart.text()
        self.fend = self.ui.fend.text()

    def check_selection(self):
        if self.obsdir == '' or self.srcfile == '' or self.recfile == '':
            return False
        return True

    def get_survey(self):
        return self.survey

    def connectButtons(self):
        QtCore.QObject.connect(self.ui.pushButton_obs, QtCore.SIGNAL("clicked()"), self.chooseObsdir)
        QtCore.QObject.connect(self.ui.pushButton_src, QtCore.SIGNAL("clicked()"), self.chooseSourcefile)
        QtCore.QObject.connect(self.ui.pushButton_rec, QtCore.SIGNAL("clicked()"), self.chooseRecfile)

    def chooseObsdir(self):
        text=browseDir(self.mainwindow, 'Choose observation directory')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_obs.setText(text)

    def chooseSourcefile(self):
        text=openFile(self.mainwindow, 'Open source file')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_src.setText(text)

    def chooseRecfile(self):
        text=openFile(self.mainwindow, 'Open receiver file')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_rec.setText(text)

    def _finalizeSurvey(self):
        hideProgressBar(self.mainUI.progressBar)
        if self.gsr_thread.success:
            self.survey = self.gsr_thread.get_survey()
            QtGui.QMessageBox.information(self.mainwindow, "Done!", "Done generating Survey object!")
        else:
            exception = self.gsr_thread._exception
            QtGui.QMessageBox.information(self.mainwindow, "Error!", "Could not generate Survey object!\nReason:{}".format(exception))
            raise exception



class Call_autopicker_window(object):
    def __init__(self, gui, survey):
        self.gui = gui
        self.mainwindow = gui.mainwindow
        self.mainUI = gui.mainUI
        self.survey = survey
        self.maxSRdist = None
        self.snrPoint = None
        self.dists_p = []
        self.snr_p = []
        self.lines = []
        self.init_dialog()
        self._exception=None
        self.refresh_selection()
        self.enableDynSNR(False)
        self.plotSNR(refresh=True)
        self.plotTraceInit()
        self.start_dialog()

    def init_dialog(self):
        qdialog = QtGui.QDialog(self.mainwindow)
        ui = Ui_picking_parameters()
        ui.setupUi(qdialog)
        ui.ncores.setMaximum(getMaxCPU())
        self.ui = ui
        self.qdialog = qdialog
        self.initSNRplot()
        self.initTraceplot()
        self.connectButtons()

    def getMaxSRdist(self):
        if self.maxSRdist is not None:
            return self.maxSRdist
        else:
            SRdists = []
            for shot in self.survey.data.values():
                for traceID in shot.getTraceIDlist():
                    SRdists.append(shot.getDistance(traceID))
            self.maxSRdist = max(SRdists)
            return self.maxSRdist

    def update_survey(self, survey):
        self.survey = survey

    def initSNRplot(self):
        self.snrFig = Figure()
        self.snrCanvas = FigureCanvas(self.snrFig)
        self.ui.vlayout_plot.addWidget(self.snrCanvas)
        self.snrToolbar = NavigationToolbar(self.snrCanvas, self.mainwindow)
        self.ui.vlayout_plot.addWidget(self.snrToolbar)

    def initTraceplot(self):
        self.traceFig = Figure()
        self.traceCanvas = FigureCanvas(self.traceFig)
        self.ui.verticalLayout_trace_plot.addWidget(self.traceCanvas)
        self.traceToolbar = NavigationToolbar(self.traceCanvas, self.mainwindow)
        self.ui.verticalLayout_trace_plot.addWidget(self.traceToolbar)
        self.traceToolbar.home = self.autoscale_TrPlot

        shotnumbers = list(self.survey.data.keys())
        shotnumbers.sort()
        for index, shotnumber in enumerate(shotnumbers):
            self.ui.comboBox_shots.insertItem(index, str(shotnumber))
        self.ui.comboBox_shots.setMaxCount(len(shotnumbers))
        self.ui.comboBox_shots.setCurrentIndex(0)
        self.refresh_comboBox_traces()
        self.ui.comboBox_traces.setCurrentIndex(0)

    def prepSNRfig(self, refresh=True):
        fig = self.snrFig
        if fig.axes == []:
            ax = fig.add_subplot(111)
            xlim = None
            ylim = None
        else:
            ax = fig.axes[0]
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
        # ax.clear()
        if not refresh:
            self.plotPicks(ax)
            self.clear_lines()
        else:
            self.clear_lines()

        return fig, ax, xlim, ylim

    def plotTrace(self):
        fig=self.traceFig
        fig.clear()
        self.refresh_selection()

        shot=self.init_example_shot()
        self.example_shot = shot
        try:
            self.trPlot_ax1, self.trPlot_ax2 = shot.plot_traces(self.example_traceID, figure=fig, buttons=False,
                                                                cursor=False, showDetails=True, xlim=self.xlim, ylim=self.ylim)
        except Exception as e:
            print('Could not create example plot. Reason: {}'.format(e))
            return
        self.plotExamplePick(shot)
        fig.canvas.draw()
        self.set_eta_text()

    def plotTraceRefr(self):
        self.xlim=self.trPlot_ax1.get_xlim()
        self.ylim=self.trPlot_ax1.get_ylim()
        self.plotTrace()
        
    def plotTraceInit(self):
        self.xlim=None
        self.ylim=None
        self.plotTrace()

    def plotAutoRefr(self):
        if self.ui.checkBox_auto_refresh.isChecked():
            self.plotTraceRefr()

    def plotAutoInit(self):
        if self.ui.checkBox_auto_refresh.isChecked():
            self.plotTraceInit()
            
    def plotExamplePick(self, shot):
        if self.snrPoint:
            self.snrPoint.remove()
        snrax = self.snrFig.axes[0]
        self.snrPoint = snrax.plot(shot.getDistance(self.example_traceID),
                                   shot.getSNR(self.example_traceID)[0], 'ro', markersize=5)[0]
        self.snrCanvas.draw()

    def set_eta_text(self):
        self.refresh_selection()
        ntraces=self.survey.countAllTraces()
        shot=self.example_shot
        traceID=self.example_traceID
        ncores=self.ncores
        nshots=len(self.survey.data)
        eta=shot.pickduration[traceID]*ntraces/ncores
        text='Extrapolated duration for picking of {a} traces on {b} cores: {c}[H:MM:SS]'.format(a=ntraces, b=ncores, c=eta)
        self.ui.label_eta.setText(text)
        
    def autoscale_TrPlot(self):
        self.trPlot_ax1.autoscale()
        
    def init_example_shot(self):
        self.example_shotnumber=int(self.ui.comboBox_shots.currentText())
        self.example_traceID=int(self.ui.comboBox_traces.currentText())
        shot = self.survey.data[self.example_shotnumber]

        if self.AIC:
            shot.setMethod('aic')
        else:
            shot.setMethod('hos')
        shot.setOrder(order=4)
        shot.setVmin(self.vmin)
        shot.setVmax(self.vmax)
        shot.setCut(self.cutwindow)
        shot.setTmovwind(self.tmovwind)
        shot.setTsignal(self.tsignal)
        shot.setTgap(self.tgap)
        shot.setFolm(self.folm/100.)
        shot.setAicwindow(self.aicwindow)
        try:
            pick = shot.pickTrace(self.example_traceID)
        except Exception as e:
            print('Could not init example pick for shot {}, traceID {}:'.format(shot.getShotnumber(),
                                                                                self.example_traceID), e)
            return shot
        shot.setPick(self.example_traceID, pick)
        shot.setSNR(self.example_traceID)
        shot.setEarllatepick(self.example_traceID)

        return shot

    def refresh_comboBox_traces(self):
        self.ui.comboBox_traces.clear()
        shot=self.survey.getShotForShotnumber(int(self.ui.comboBox_shots.currentText()))
        traceIDs=shot.getTraceIDlist()
        for index, traceID in enumerate(traceIDs):
            self.ui.comboBox_traces.insertItem(index, str(traceID))
        self.ui.comboBox_traces.setMaxCount(len(traceIDs))
        self.ui.comboBox_traces.setCurrentIndex(0)
        
    def clear_lines(self):
        for line in self.lines:
            line.remove()
        self.lines = []

    def finishFigure(self, ax, xlim, ylim):
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

    def finishNewFigure(self, ax):
        xlim = None
        ylim = None
        ax.set_xlabel('Distance [m]')
        ax.set_ylabel('SNR')
        return xlim, ylim

    def plotPicks(self, ax):
        if self.survey.picked:
            if self.dists_p == [] or self.snr_p == []:
                for shot in self.survey.data.values():
                    for traceID in shot.getTraceIDlist():
                        self.dists_p.append(shot.getDistance(traceID))
                        self.snr_p.append(shot.getSNR(traceID)[0])

            ax.scatter(self.dists_p, self.snr_p, s=5, c='k', alpha=1)

    def plotConstSNR(self, refresh=True):
        fig, ax, xlim, ylim = self.prepSNRfig(refresh)

        snrthreshold = float(self.ui.doubleSpinBox_constSNR.value())
        line = ax.hlines(snrthreshold, 0, self.getMaxSRdist(), 'b', linewidth=1)
        self.lines.append(line)

        if refresh == False:
            xlim, ylim = self.finishNewFigure(ax)

        if self.survey.picked:
            self.finishFigure(ax, xlim, ylim)

        self.snrCanvas.draw()

    def plotDynSNR(self, refresh=True):
        fig, ax, xlim, ylim = self.prepSNRfig(refresh)
        snrthresholds = []
        shiftSNR = float(self.ui.shift_snr.value())
        shiftDist = float(self.ui.shift_dist.value())
        p1 = float(self.ui.p1.value())
        p2 = float(self.ui.p2.value())
        dists = np.arange(0, self.getMaxSRdist() + 1, 1)

        for dist in dists:
            dist += shiftDist
            snrthresholds.append(surveyUtils.snr_fit_func(surveyUtils.get_fit_fn(p1, p2), dist, shiftSNR))
        self.lines = ax.plot(dists, snrthresholds, 'b', linewidth=1)

        if refresh == False:
            xlim, ylim = self.finishNewFigure(ax)

        if self.survey.picked:
            self.finishFigure(ax, xlim, ylim)

        self.snrCanvas.draw()

    def plotSNR(self, refresh=True):
        if self.ui.radioButton_const.isChecked():
            self.plotConstSNR(refresh)
        if self.ui.radioButton_dyn.isChecked():
            self.plotDynSNR(refresh)

    def snr_toggle(self):
        if self.ui.radioButton_const.isChecked():
            self.enableDynSNR(False)
            self.enableConstSNR(True)
        if self.ui.radioButton_dyn.isChecked():
            self.enableConstSNR(False)
            self.enableDynSNR(True)
        self.plotSNR(refresh=True)

    def enableDynSNR(self, bool):
        self.ui.shift_dist.setEnabled(bool)
        self.ui.shift_snr.setEnabled(bool)
        self.ui.p1.setEnabled(bool)
        self.ui.p2.setEnabled(bool)

    def enableConstSNR(self, bool):
        self.ui.doubleSpinBox_constSNR.setEnabled(bool)

    def start_dialog(self, repick=False):
        self.plotSNR(refresh=False)
        if self.qdialog.exec_():
            if self.gui.checkPickState():
                if not yesNoDialogMessage('Survey already picked. Continue?'):
                    return
            self.refresh_selection()

            if self.AIC == True:
                HosAic = 'aic'
            else:
                HosAic = 'hos'

            if self.ui.radioButton_dyn.isChecked():
                surveyUtils.setDynamicFittedSNR(self.survey.getShotDict(), shiftdist=self.shiftDist,
                                                shiftSNR=self.shiftSNR, p1=self.p1, p2=self.p2)
            elif self.ui.radioButton_const.isChecked():
                surveyUtils.setConstantSNR(self.survey.getShotDict(),
                                           snrthreshold=self.ui.doubleSpinBox_constSNR.value())

            self.survey.setParametersForAllShots(cutwindow=self.cutwindow,
                                                 tmovwind=self.tmovwind,
                                                 tsignal=self.tsignal,
                                                 tgap=self.tgap)

            self.survey.pickAllShots(vmin=self.vmin, vmax=self.vmax,
                                     folm=self.folm / 100., HosAic=HosAic,
                                     aicwindow=self.aicwindow, cores=self.ncores,
                                     threading=self.threading, gui=self.gui,
                                     repick=repick)

            # QtGui.qApp.processEvents() # test
            self.executed = True
            self.clear_lines()
        else:
            self.refresh_selection()
            self.executed = False
            self.clear_lines()

    def refreshFolm(self):
        self.ui.label_folm.setText('%s %%' % self.ui.slider_folm.value())

    def refresh_selection(self):
        self.ncores = int(self.ui.ncores.value())
        self.vmin = float(self.ui.lineEdit_vmin.text())
        self.vmax = float(self.ui.lineEdit_vmax.text())
        self.folm = float(self.ui.slider_folm.value())
        self.AIC = self.ui.checkBox_AIC.isChecked()
        self.threading = self.ui.checkBox_threading.isChecked()
        self.aicwindow = (int(self.ui.lineEdit_aicleft.text()), int(self.ui.lineEdit_aicright.text()))
        self.shiftSNR = float(self.ui.shift_snr.value())
        self.shiftDist = float(self.ui.shift_dist.value())
        self.p1 = float(self.ui.p1.value())
        self.p2 = float(self.ui.p2.value())
        self.cutwindow = (self.ui.doubleSpinBox_cut_left.value(), self.ui.doubleSpinBox_cut_right.value())
        self.tmovwind = self.ui.doubleSpinBox_tmovwind.value()
        self.tsignal = self.ui.doubleSpinBox_tsignal.value()
        self.tgap = self.ui.doubleSpinBox_tgap.value()

    def connectButtons(self):
        QtCore.QObject.connect(self.ui.slider_folm, QtCore.SIGNAL("valueChanged(int)"), self.refreshFolm)
        QtCore.QObject.connect(self.ui.shift_snr, QtCore.SIGNAL("valueChanged(int)"), self.plotSNR)
        QtCore.QObject.connect(self.ui.shift_dist, QtCore.SIGNAL("valueChanged(int)"), self.plotSNR)
        QtCore.QObject.connect(self.ui.p1, QtCore.SIGNAL("valueChanged(double)"), self.plotSNR)
        QtCore.QObject.connect(self.ui.p2, QtCore.SIGNAL("valueChanged(double)"), self.plotSNR)
        QtCore.QObject.connect(self.ui.doubleSpinBox_constSNR, QtCore.SIGNAL("valueChanged(double)"), self.plotSNR)
        QtCore.QObject.connect(self.ui.radioButton_const, QtCore.SIGNAL("clicked()"), self.snr_toggle)
        QtCore.QObject.connect(self.ui.radioButton_dyn, QtCore.SIGNAL("clicked()"), self.snr_toggle)
        QtCore.QObject.connect(self.ui.doubleSpinBox_cut_left, QtCore.SIGNAL("valueChanged(double)"),
                               self.updateCutBorders)
        QtCore.QObject.connect(self.ui.doubleSpinBox_cut_right, QtCore.SIGNAL("valueChanged(double)"),
                               self.updateCutBorders)

        QtCore.QObject.connect(self.ui.doubleSpinBox_cut_left, QtCore.SIGNAL("valueChanged(double)"),
                               self.plotAutoRefr)
        QtCore.QObject.connect(self.ui.doubleSpinBox_cut_right, QtCore.SIGNAL("valueChanged(double)"),
                               self.plotAutoRefr)
        QtCore.QObject.connect(self.ui.doubleSpinBox_tmovwind, QtCore.SIGNAL("valueChanged(double)"),
                               self.plotAutoRefr)
        QtCore.QObject.connect(self.ui.doubleSpinBox_tsignal, QtCore.SIGNAL("valueChanged(double)"),
                               self.plotAutoRefr)
        QtCore.QObject.connect(self.ui.doubleSpinBox_tgap, QtCore.SIGNAL("valueChanged(double)"),
                               self.plotAutoRefr)

        #new style connection is much better!
        self.ui.lineEdit_vmin.textChanged[str].connect(self.plotAutoRefr)        
        self.ui.lineEdit_vmax.textChanged[str].connect(self.plotAutoRefr)
        self.ui.lineEdit_aicleft.textChanged[str].connect(self.plotAutoRefr)
        self.ui.lineEdit_aicright.textChanged[str].connect(self.plotAutoRefr)
        self.ui.checkBox_AIC.stateChanged[int].connect(self.plotAutoRefr)
        self.ui.comboBox_shots.activated[int].connect(self.refresh_comboBox_traces)
        self.ui.comboBox_shots.activated[int].connect(self.plotAutoInit)
        self.ui.comboBox_traces.activated[int].connect(self.plotAutoInit)
        self.ui.slider_folm.sliderReleased.connect(self.plotAutoRefr)
        self.ui.ncores.valueChanged[int].connect(self.set_eta_text)
        self.ui.pushButton_refreshPlot.clicked.connect(self.plotTraceRefr)
        
    def updateCutBorders(self):
        self.ui.doubleSpinBox_cut_left.setMaximum(self.ui.doubleSpinBox_cut_right.value())
        self.ui.doubleSpinBox_cut_right.setMinimum(self.ui.doubleSpinBox_cut_left.value())

    def chooseObsdir(self):
        text=browseDir(self.mainwindow, 'Choose observation directory.')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_obs.setText(text)

    def chooseSourcefile(self):
        text=openFile(self.mainwindow, 'Open source file')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_src.setText(text)

    def chooseRecfile(self):
        text=openFile(self.mainwindow, 'Open receiver file')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_rec.setText(text)


class Export2ascii_window(object):
    def __init__(self, gui, survey):
        self.gui = gui
        self.mainwindow = gui.mainwindow
        self.mainUI = gui.mainUI
        self.survey = survey
        self.init_dialog()
        self.refresh_selection()
        self.start_dialog()

    def init_dialog(self):
        qdialog = QtGui.QDialog(self.mainwindow)
        ui = Ui_export2ascii()
        ui.setupUi(qdialog)
        self.ui = ui
        self.qdialog = qdialog
        self.connectButtons()

    def start_dialog(self):
        if self.qdialog.exec_():
            self.refresh_selection()
            if not os.path.exists(self.outfolder):
                printDialogMessage('Output folder does not exist. Aborted.')
                return
            for shot in self.survey.data.values():
                filewritten = False
                outfilename = os.path.join(self.outfolder, str(shot.getShotnumber()) + '.pck')
                if os.path.exists(outfilename):
                    print('Warning: output file %s exists. Skipping' % outfilename)
                    continue
                outfile = open(outfilename, 'w')
                for traceID in shot.getTraceIDlist():
                    if shot.getPickFlag(traceID):
                        if self.addPickerror:
                            line = '%3i    %5.5f    %5.5f\n' % (
                            traceID, shot.getPick(traceID), shot.getPickError(traceID))
                        else:
                            line = '%3i    %5.5f\n' % (traceID, shot.getPick(traceID))
                    elif not shot.getPickFlag(traceID) and self.addInvalidValue:
                        if self.addPickerror:
                            line = '%3i    %5.5s    %5.5s\n' % (traceID, self.invalidValue, self.invalidValue)
                        else:
                            line = '%3i    %5.5s\n' % (traceID, self.invalidValue)
                    outfile.write(line)
                    filewritten = True
                if filewritten:
                    print('Wrote picks to file %s' % outfilename)
                outfile.close()
            self.executed = True
        else:
            self.refresh_selection()
            self.executed = False

    def refresh_selection(self):
        self.outfolder = self.ui.lineEdit_outfolder.text()
        self.addInvalidValue = self.ui.checkBox_add_invalid.isChecked()
        self.invalidValue = self.ui.lineEdit_invalid_value.text()
        self.addPickerror = self.ui.checkBox_add_pickerror.isChecked()

    def connectButtons(self):
        QtCore.QObject.connect(self.ui.pushButton_outfolder, QtCore.SIGNAL("clicked()"), self.chooseOutdir)
        QtCore.QObject.connect(self.ui.checkBox_add_invalid, QtCore.SIGNAL("stateChanged(int)"),
                               self.toggleInvalidValue)

    def chooseOutdir(self):
        text=browseDir(self.mainwindow, 'Choose output directory.')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_outfolder.setText(text)

    def toggleInvalidValue(self):
        self.ui.lineEdit_invalid_value.setEnabled(self.ui.checkBox_add_invalid.isChecked())


class ExportRecLoc_window(object):
    def __init__(self, gui, seisarray):
        self.gui = gui
        self.mainwindow = gui.mainwindow
        self.mainUI = gui.mainUI
        self.seisarray = seisarray
        self.init_dialog()
        self.refresh_selection()
        self.start_dialog()

    def init_dialog(self):
        qdialog = QtGui.QDialog(self.mainwindow)
        ui = Ui_export_receiver_locations()
        ui.setupUi(qdialog)
        self.ui = ui
        self.qdialog = qdialog
        self.connectButtons()

    def start_dialog(self):
        if self.qdialog.exec_():
            self.refresh_selection()
            self.seisarray.exportAll(self.outfile)
            self.executed = True
        else:
            self.refresh_selection()
            self.executed = False

    def refresh_selection(self):
        self.outfile = self.ui.lineEdit_outfile.text()

    def connectButtons(self):
        QtCore.QObject.connect(self.ui.pushButton_outfile, QtCore.SIGNAL("clicked()"), self.chooseOutfile)

    def chooseOutfile(self):
        text=saveFile(self.mainwindow, 'Choose output file')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_outfile.setText(text)


class Call_FMTOMO_window(object):
    def __init__(self, mainwindow, mainUI, survey):
        self.mainwindow = mainwindow
        self.mainUI = mainUI
        self.survey = survey
        self.init_dialog()
        self.refresh_selection()
        self.start_dialog()

    def init_dialog(self):
        qdialog = QtGui.QDialog(self.mainwindow)
        ui = Ui_fmtomo_parameters()
        ui.setupUi(qdialog)
        ui.nproc.setMaximum(getMaxCPU())
        self.ui = ui
        self.qdialog = qdialog
        self.connectButtons()

    def start_dialog(self):
        if self.qdialog.exec_():
            self.refresh_selection()

            if not os.path.isdir(self.picks_dir):
                err = os.mkdir(self.picks_dir)  # error not handled yet

            self.survey.exportFMTOMO(self.picks_dir)

            cwd = os.getcwd()
            interpolationMethod = 'linear'
            os.chdir(self.simuldir)
            if self.survey.seisarray.twoDim:
                interpolationMethod = 'nearest'

            self.fmtomo_thread=FMTOMO_Thread(self.mainwindow, self, interpolationMethod, cwd, fmtomoUtils, self.mainUI.progressBar)

            self.fmtomo_thread.start()
            self.executed = True
            self.fmtomo_thread.connect(self.fmtomo_thread, QtCore.SIGNAL("finished()"), self.finishSimulation)


            # self.survey.seisarray.generateFMTOMOinputFromArray(self.propgrid, self.vgrid, (self.bbot, self.btop),
            #                                                    self.cushionfactor / 100., interpolationMethod,
            #                                                    customgrid=self.customgrid, writeVTK=True)
            # os.chdir(cwd)

            # tomo = fmtomoUtils.Tomo3d(self.fmtomo_dir, self.simuldir)
            # tomo.runTOMO3D(self.nproc, self.nIter)
            
            # self.executed = True
        else:
            self.refresh_selection()
            self.executed = False

    def update_survey(self, survey):
        self.survey = survey

    def refresh_selection(self):
        self.fmtomo_dir = self.ui.fmtomo_dir.text()
        self.nIter = int(self.ui.nIter.value())
        self.nproc = int(self.ui.nproc.value())
        self.btop = float(self.ui.btop.text())
        self.bbot = float(self.ui.bbot.text())
        self.propgrid = (int(self.ui.pgrid_x.value()), int(self.ui.pgrid_y.value()), int(self.ui.pgrid_z.value()))
        self.vgrid = (int(self.ui.invgrid_x.value()), int(self.ui.invgrid_y.value()), int(self.ui.invgrid_z.value()))
        self.cushionfactor = float(self.ui.cushion.value())
        self.elevation = float(self.ui.elevation.value())
        self.customgrid = self.ui.customgrid.text()
        self.simuldir = self.ui.simuldir.text()
        self.picks_dir = os.path.join(self.simuldir, 'picks')

    def connectButtons(self):
        QtCore.QObject.connect(self.ui.browse_tomodir, QtCore.SIGNAL("clicked()"), self.chooseFMTOMOdir)
        QtCore.QObject.connect(self.ui.browse_customgrid, QtCore.SIGNAL("clicked()"), self.chooseCustomgrid)
        QtCore.QObject.connect(self.ui.browse_simuldir, QtCore.SIGNAL("clicked()"), self.chooseSimuldir)

    def chooseFMTOMOdir(self):
        text=browseDir(self.mainwindow, 'Choose directory containing FMTOMO binaries')
        if not text: return
        if text[0] != '':
            self.ui.fmtomo_dir.setText(text)

    def chooseCustomgrid(self):
        text=openFile(self.mainwindow, 'Choose earth model')
        if not text: return
        if text[0] != '':
            self.ui.customgrid.setText(text)

    def chooseSimuldir(self):
        text=browseDir(self.mainwindow, 'Choose simulation directory')
        if not text: return
        if text[0] != '':
            self.ui.simuldir.setText(text)

    def finishSimulation(self):
        if self.fmtomo_thread.success:
            printDialogMessage('Finished FMTOMO simulation.\nUse |Tools| -> |VTK visualization| to visualize results.')
        else:
            exception = self.fmtomo_thread._exception
            printDialogMessage('Could not finish FMTOMO simulation.\nReason:{}'.format(exception))
        raise exception
    

class Call_VTK_window(object):
    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        self.init_dialog()
        self.refresh_selection()
        self.start_dialog()

    def init_dialog(self):
        qdialog = QtGui.QDialog(self.mainwindow)
        ui = Ui_vtk_tools()
        ui.setupUi(qdialog)
        self.ui = ui
        self.qdialog = qdialog
        self.connectButtons()

    def start_dialog(self):
        self.qdialog.exec_()
        self.refresh_selection()

    def refresh_selection(self):
        self.vg = self.ui.lineEdit_vg.text()
        self.vgout = self.ui.lineEdit_vgout.text()
        self.rays = self.ui.lineEdit_rays.text()
        self.raysout = self.ui.lineEdit_raysout.text()

    def checkVgStartButton(self):
        ui = self.ui
        if ui.radioButton_rel.isChecked():
            if ui.lineEdit_vg.text() != '' and ui.lineEdit_vgref.text() != '':
                ui.start_vg.setEnabled(True)
            else:
                ui.start_vg.setEnabled(False)
        if ui.radioButton_abs.isChecked():
            if ui.lineEdit_vg.text() != '':
                ui.start_vg.setEnabled(True)
            else:
                ui.start_vg.setEnabled(False)

    def checkRaysStartButton(self):
        ui = self.ui
        if ui.lineEdit_rays.text() != '' and ui.lineEdit_raysout.text() != '':
            ui.start_rays.setEnabled(True)
        else:
            ui.start_rays.setEnabled(False)

    def connectButtons(self):
        QtCore.QObject.connect(self.ui.pushButton_vg, QtCore.SIGNAL("clicked()"), self.chooseVgrid)
        QtCore.QObject.connect(self.ui.pushButton_vgref, QtCore.SIGNAL("clicked()"), self.chooseVgridref)
        QtCore.QObject.connect(self.ui.pushButton_rays, QtCore.SIGNAL("clicked()"), self.chooseRaysIn)
        QtCore.QObject.connect(self.ui.pushButton_raysout, QtCore.SIGNAL("clicked()"), self.chooseRaysOutDir)
        QtCore.QObject.connect(self.ui.pushButton_vtkout, QtCore.SIGNAL("clicked()"), self.newFileVTK)
        QtCore.QObject.connect(self.ui.pushButton_parav, QtCore.SIGNAL("clicked()"), self.openFileParaview)
        QtCore.QObject.connect(self.ui.start_vg, QtCore.SIGNAL("clicked()"), self.startvgvtk)
        QtCore.QObject.connect(self.ui.start_rays, QtCore.SIGNAL("clicked()"), self.startraysvtk)
        QtCore.QObject.connect(self.ui.radioButton_rel, QtCore.SIGNAL("clicked()"), self.activateVgref)
        QtCore.QObject.connect(self.ui.radioButton_abs, QtCore.SIGNAL("clicked()"), self.deactivateVgref)

    def openFileParaview(self):
        os.system('paraview %s &' % self.ui.lineEdit_vgout.text())

    def activateVgref(self):
        self.ui.lineEdit_vgref.setEnabled(True)
        self.ui.pushButton_vgref.setEnabled(True)

    def deactivateVgref(self):
        self.ui.lineEdit_vgref.setEnabled(False)
        self.ui.pushButton_vgref.setEnabled(False)

    def chooseVgrid(self):
        text=openFile(self.mainwindow, 'Choose velocity grid (it#/vgrids.in)')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_vg.setText(text)
        self.checkVgStartButton()

    def chooseVgridref(self):
        text=openFile(self.mainwindow, 'Choose reference velocity grid (vgridsref.in)')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_vgref.setText(text)
        self.checkVgStartButton()

    def chooseRaysIn(self):
        text=openFile(self.mainwindow, 'Choose rays input file (rays.dat)')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_rays.setText(text)
        self.checkRaysStartButton()

    def chooseRaysOutDir(self):
        text=browseDir(self.mainwindow, 'Choose output directory for rays')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_raysout.setText(text)
        self.checkRaysStartButton()

    def startvgvtk(self):
        ui = self.ui
        if ui.lineEdit_vgout.text() == '':
            return
        outfilename=ui.lineEdit_vgout.text()
        if outfilename.split('.')[-1] != 'vtk':
            outfilename+='.vtk'
        if ui.radioButton_abs.isChecked():
            fmtomoUtils.vgrids2VTK(inputfile=ui.lineEdit_vg.text(),
                                   outputfile=outfilename,
                                   absOrRel='abs')
        elif ui.radioButton_rel.isChecked():
            fmtomoUtils.vgrids2VTK(inputfile=ui.lineEdit_vg.text(),
                                   outputfile=outfilename,
                                   absOrRel='rel',
                                   inputfileref=ui.lineEdit_vgref.text())

    def startraysvtk(self):
        ui = self.ui
        fmtomoUtils.rays2VTK(ui.lineEdit_rays.text(), ui.lineEdit_raysout.text())

    def newFileVTK(self):
        text=saveFile(self.mainwindow, 'Choose output vtk filename')
        if not text: return
        if text[0] != '':
            self.ui.lineEdit_vgout.setText(text)


class Postprocessing_window(object):
    def __init__(self, gui, survey):
        self.gui = gui
        self.mainwindow = gui.mainwindow
        self.survey = survey
        self.init_widget()
        self.start_widget()
        self.inkByVal = 'snrlog'

    def init_widget(self):
        qwidget = QtGui.QWidget()
        ui = Ui_postprocessing()
        ui.setupUi(qwidget)
        self.ui = ui
        self.qwidget = qwidget
        self.initPlot()
        self.newPlot()
        self.connectButtons()
        self.region = regions(self.ax, self.cbar, self.survey, qt_interface=True)

    def getRegion(self):
        return self.region

    def start_widget(self):
        self.qwidget.showMaximized()

    def initPlot(self):
        self.qwidget.closeEvent = self.close
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ui.verticalLayout_plot.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self.mainwindow)
        self.ui.verticalLayout_plot.addWidget(self.toolbar)

    def newPlot(self):
        ax = self.figure.add_subplot(111)
        dists, picks, snrlog, pe, spe = self.survey.preparePlotAllPicks(plotRemoved=False)
        self.dists = dists
        self.picks = picks
        self.inkDict = {'snrlog': snrlog,
                        'pe': pe,
                        'spe': spe}

        ax, cbar, sc, label = self.survey.createPlot(dists, picks, snrlog, label='log10(SNR)', ax=ax, cbar=None)
        self.cbar = self.figure.colorbar(sc, ax=ax, label=label, fraction=0.05)
        self.ax = ax
        self.draw()

    def refreshPlot(self):
        self.ax.clear()
        ax = self.ax
        ax, cbar, sc = self.survey.createPlot(self.dists, self.picks, self.inkDict[self.inkByVal],
                                              self.inkByVal, ax=ax, cbar=self.cbar)
        # self.cbar = self.figure.colorbar(sc, fraction=0.05)
        self.draw()

    def update_survey(self, survey):
        self.survey = survey

    def get_survey(self):
        return self.survey

    def draw(self):
        self.canvas.draw()

    def connectButtons(self):
        QtCore.QObject.connect(self.ui.pushButton_rect, QtCore.SIGNAL("clicked()"), self.rectSelector)
        QtCore.QObject.connect(self.ui.pushButton_poly, QtCore.SIGNAL("clicked()"), self.choosePoly)
        QtCore.QObject.connect(self.ui.pushButton_plot, QtCore.SIGNAL("clicked()"), self.plotPicks)
        QtCore.QObject.connect(self.ui.pushButton_delete, QtCore.SIGNAL("clicked()"), self.deleteSelected)
        QtCore.QObject.connect(self.ui.pushButton_undo, QtCore.SIGNAL("clicked()"), self.undoSelection)
        QtCore.QObject.connect(self.ui.pushButton_snr, QtCore.SIGNAL("clicked()"), self.refrSNR)
        QtCore.QObject.connect(self.ui.pushButton_pe, QtCore.SIGNAL("clicked()"), self.refrPE)
        QtCore.QObject.connect(self.ui.pushButton_spe, QtCore.SIGNAL("clicked()"), self.refrSPE)

    def rectSelector(self):
        if self.ui.pushButton_rect.isChecked():
            self.chooseRect()
        else:
            self.abortRect()
        
    def chooseRect(self):
        self.rect = self.region.chooseRectangles()

    def choosePoly(self):
        self.region.choosePolygon()

    def abortRect(self):
        self.ui.pushButton_rect.setChecked(False)
        self.disconnectRect()
        
    def disconnectRect(self):
        self.region.disconnectRect()

    def disconnectPoly(self):
        self.region.disconnectPoly()

    def plotPicks(self):
        self.repickingQt = self.region.plotTracesInActiveRegions(qt=True, qtMainwindow=self.qwidget,
                                                                 maxfigures=int(self.ui.max_figures.value()))

    def deleteSelected(self):
        self.region.setAllActiveRegionsForDeletion()
        message = 'All marked picks will be deleted!'
        if continueDialogMessage(message):
            self.region.deleteAllMarkedPicks()
        else:
            self.region.refreshFigure()

    def undoSelection(self):
        self.region.deselectLastSelection()

    def refrSNR(self):
        self.region.refreshLog10SNR()

    def refrPE(self):
        self.region.refreshPickerror()

    def refrSPE(self):
        self.region.refreshSPE()

    def close(self, event=None):
        self.qwidget.close()
        self.gui.refreshPickedWidgets()

        
class Repicking_window(object):
    def __init__(self, mainwindow, shot, traceID, matshowax=None):
        self.mainwindow = mainwindow
        self.matshowax = matshowax
        self.shot = shot
        self.traceID = traceID
        self.init_widget()
        self.start_widget()

    def init_widget(self):
        qwidget = QtGui.QWidget()
        ui = Ui_repicking()
        ui.setupUi(qwidget)
        self.ui = ui
        self.qwidget = qwidget
        self.initPlot()
        self.plot()
        self.connectButtons()

    def start_widget(self):
        self.qwidget.show()

    def connectButtons(self):
        QtCore.QObject.connect(self.ui.pushButton_repick, QtCore.SIGNAL("clicked()"), self.repickMode)
        QtCore.QObject.connect(self.ui.pushButton_delete, QtCore.SIGNAL("clicked()"), self.delete)
        QtCore.QObject.connect(self.ui.pushButton_done, QtCore.SIGNAL("clicked()"), self.close)

    def initPlot(self):
        self.qwidget.closeEvent = self.close
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ui.verticalLayout_plot.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self.mainwindow)
        self.ui.verticalLayout_plot.addWidget(self.toolbar)

    def plot(self):
        self.shot.plot_traces(self.traceID, figure=self.figure, buttons=False)
        self.draw()

    def draw(self):
        self.canvas.draw()

    def repickMode(self):
        if self.ui.pushButton_repick.isChecked():
            self.repick()
        else:
            self.abort()
        
    def repick(self):
        shot = self.shot
        self.ui.pushButton_repick.setStyleSheet("background-color: red")
        def onclick(event):
            shot.setPick(self.traceID, event.xdata, revised=True)
            if shot.getSNR(self.traceID)[0] > 1:
                shot.setEarllatepick(self.traceID)
            self.update()
            self.abort()

        self.cid = self.canvas.mpl_connect('button_press_event', onclick)

    def abort(self):
        self.ui.pushButton_repick.setChecked(False)
        self.ui.pushButton_repick.setStyleSheet("background-color: None")        
        try:
            self.canvas.mpl_disconnect(self.cid)
        except:
            pass
        
    def close(self, event=None):
        self.shot.setRevised(self.traceID, True)
        self.qwidget.close()
        self.refresh_matshow()

    def refresh_matshow(self):
        if self.matshowax:
            self.shot.matshow(fig=self.shot.matshowfig, qt=True, qtMainwindow=self.mainwindow, refresh=True)

    def delete(self):
        self.shot.removePick(self.traceID, revised=True)
        self.update()

    def update(self):
        self.figure.clear()
        self.plot()


class Merge_Shots_window(object):
    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        self.filenames_added = {}  # 'Part': []}
        self.maxNarrays = 1
        self.init_dialog()

        # self.refresh_selection()
        self.start_dialog()
        # NO ATTRIBUTES HERE

    def init_dialog(self):
        qdialog = QtGui.QDialog(self.mainwindow)
        ui = Ui_merge_shots()
        ui.setupUi(qdialog)
        self.ui = ui
        self.qdialog = qdialog
        self.connectButtons()
        self.connect()
        self.disableSaveButton()
        self.updateTable()
        ui.lineEdit_input.setReadOnly(True)

    def start_dialog(self):
        self.enableInput(True)
        self.qdialog.exec_()

        # self.refresh_selection()

    # def refresh_selection(self):
    #     self.vg = self.ui.lineEdit_vg.text()
    #     self.vgout = self.ui.lineEdit_vgout.text()
    #     self.rays = self.ui.lineEdit_rays.text()
    #     self.raysout = self.ui.lineEdit_raysout.text()

    def connectButtons(self):
        QtCore.QObject.connect(self.ui.pushButton_browse, QtCore.SIGNAL("clicked()"), self.getFile)
        QtCore.QObject.connect(self.ui.pushButton_add, QtCore.SIGNAL("clicked()"), self.addToShots)
        QtCore.QObject.connect(self.ui.pushButton_merge, QtCore.SIGNAL("clicked()"), self.getShotsAndMerge)
        QtCore.QObject.connect(self.ui.pushButton_save, QtCore.SIGNAL("clicked()"), self.saveMergedShots)

    def connect(self):
        QtCore.QObject.connect(self.ui.spinBox_nshots, QtCore.SIGNAL("valueChanged(int)"), self.checkNshotsMismatch)
        QtCore.QObject.connect(self.ui.spinBox_part, QtCore.SIGNAL("valueChanged(int)"), self.checkNshotsMismatch)
        QtCore.QObject.connect(self.ui.checkBox_general, QtCore.SIGNAL("stateChanged(int)"), self.toggleGeneralSettings)

    def checkNshotsMismatch(self):
        nsBox = self.getNshots()
        nsTable = self.countTableFilled()
        self.ui.spinBox_nshots.setMinimum(max(1, nsTable))
        self.updateTable()
        if nsBox < nsTable:
            QtGui.QMessageBox.information(self.qdialog, 'Error!', 'Cannot further reduce number of shots.')

    def countTableFilled(self):
        nsTableMax = 0
        for lst in self.filenames_added.values():
            nsTable = 0
            for item in lst:
                if not item == []:
                    nsTable += 1
            if nsTable > nsTableMax:
                nsTableMax = nsTable
        return nsTableMax

    def getNshots(self):
        return self.ui.spinBox_nshots.value()

    def getPartNumber(self):
        return self.ui.spinBox_part.value()

    def setMaxNarrays(self, value):
        self.maxNarrays = value
        self.ui.spinBox_part.setMaximum(value)

    def setText(self, text):
        self.ui.lineEdit_input.setText(text)

    def enableSaveButton(self):
        self.ui.pushButton_save.setEnabled(True)

    def disableSaveButton(self):
        self.ui.pushButton_save.setEnabled(False)

    def enableInput(self, bool):
        self.ui.checkBox_general.setEnabled(bool)
        self.ui.lineEdit_input.setEnabled(bool)
        self.ui.pushButton_browse.setEnabled(bool)
        self.ui.pushButton_add.setEnabled(bool)
        self.ui.pushButton_merge.setEnabled(bool)
        self.ui.label_2.setEnabled(bool)
        self.ui.label.setEnabled(bool)
        self.ui.spinBox_part.setEnabled(bool)
        self.ui.spinBox_nshots.setEnabled(bool)

    def toggleGeneralSettings(self):
        if self.ui.checkBox_general.isChecked():
            self.enableGeneralSettings(True)
        else:
            self.enableGeneralSettings(False)

    def enableGeneralSettings(self, bool):
        self.ui.lineEdit_network.setEnabled(bool)
        self.ui.lineEdit_station.setEnabled(bool)
        self.ui.lineEdit_location.setEnabled(bool)
        self.ui.label_network.setEnabled(bool)
        self.ui.label_station.setEnabled(bool)
        self.ui.label_location.setEnabled(bool)

    def getFile(self):
        fnlist = openFiles(self.mainwindow, 'Open input files')  # real filenames (absolute path)
        if not fnlist:
            self.setText(None)
            return
        filenames = []
        for filename in fnlist:
            fpath, fname = os.path.split(filename)
            filenames.append((fpath, fname))

        text = ''
        for filename in filenames:
            text += filename[1] + ' '
        self.setText(text)

        self.filenames = filenames

    def addFilesToTable(self):
        warning = []
        arraynum = self.getPartNumber()
        if not arraynum in self.filenames_added.keys():
            self.filenames_added[arraynum] = []
            length = 0
        else:
            length = len(self.filenames_added[arraynum])
        if (len(self.filenames) + length) > self.getNshots():
            QtGui.QMessageBox.information(self.qdialog, 'Error!',
                                          'Cannot have more files than maximum number of shots.')
            return False

        in_use = []
        for arraynum in self.filenames_added.keys():
            for filename in self.filenames_added[arraynum]:
                in_use.append(filename)

        for filename in self.filenames:
            if not filename in in_use:
                self.filenames_added[arraynum].append(filename)
            else:
                warning.append(filename[1] + ' ')
        if len(warning) > 0:
            QtGui.QMessageBox.information(self.qdialog, 'Warning!',
                                          'Files: "%s" will not be added because they are already in use.' % warning)
        del (self.filenames)
        return True

    def addToShots(self):
        self.checkNshotsMismatch()
        if not self.addFilesToTable():
            return
        nextVal = self.getPartNumber() + 1
        self.setMaxNarrays(max(nextVal, self.maxNarrays))
        self.updateTable()
        self.setText(None)

    def genInputList(self):
        filenames = self.filenames_added
        # header = filenames.keys()
        # header.sort()
        datalist = []
        for column in range(self.maxNarrays):
            for row in range(self.getNshots()):
                if column == 0:
                    datalist.append([])
                key = column + 1
                try:
                    filename = filenames[key][row][1]
                except:
                    filename = ' '
                datalist[row].append(filename)
        # for key in header:
        #     for index, fns in enumerate(filenames[key]):
        #         filename = fns[1]
        #         if key == 1:
        #             datalist[index] = []
        #         datalist[index].append(filename)
        return datalist  # , header

    def genTableModel(self, inputlist, header):
        return TableModel(self.qdialog, inputlist, header)

    def updateTable(self, tm=None):
        tv = self.ui.tableView
        if not tm:
            inputlist = self.genInputList()
            if inputlist:
                header = range(1, self.maxNarrays + 1)
                header[0] = 'main'
                tm = self.genTableModel(inputlist, header)
        if tm:
            tv.setModel(tm)
            tv.resizeColumnsToContents()
            header = tv.horizontalHeader()
            header.setResizeMode(QtGui.QHeaderView.Stretch)
            tv.selectColumn(self.getPartNumber() - 1)
            return True

    def getShotsAndMerge(self):
        self.enableInput(False)
        keys = [key for key in self.filenames_added.keys()]
        keys.sort()
        merged_shots = []
        for index in range(self.getNshots()):
            shotlist = []
            main_path, main_filename = self.filenames_added[1][index]
            for key in keys:
                filepath, filename = self.filenames_added[key][index]
                shot = obsread(os.path.join(filepath, filename))
                shotlist.append(shot)
            merged_shots.append((self.mergeShots(shotlist), main_path, self.modifyFilename(main_filename)))
        self.merged_shots = merged_shots
        self.completeMerge()

    def modifyFilename(self, filename, mod='_merged.'):
        fn_prev = ''
        fname = filename.split('.')
        for fn in fname[:1]:
            fn_prev += fn
        filename_new = fn_prev + mod + fname[-1]
        return filename_new

    def completeMerge(self):
        QtGui.QMessageBox.information(self.qdialog, 'Done!', 'Finished merge operation.')
        filenames_out = []
        for shot, filepath, filename in self.merged_shots:
            filenames_out.append([filename])
        tm = self.genTableModel(filenames_out, ['MERGED SHOTS'])
        self.updateTable(tm)
        self.filenames_added = {}
        self.enableSaveButton()

    def mergeShots(self, shotlist):
        main_shot = shotlist[0]
        for trace in main_shot.traces:
            self.editAttributes(trace)
        n_prev_traces = len(main_shot.traces)  # start with main shot traces
        for shot in shotlist[1:]:
            for trace in shot.traces:
                self.editAttributes(trace, n_prev_traces)
            main_shot += shot
            ntraces_shot = len(shot.traces)
            n_prev_traces += ntraces_shot

        return main_shot

    def saveMergedShots(self):
        direc = browseDir(self.mainwindow, 'Choose output directory for merged shots')
        if not direc:
            return
        for shot, filepath, filename in self.merged_shots:
            shot.write(os.path.join(direc, filename), format='PICKLE')
        QtGui.QMessageBox.information(self.qdialog, 'Done!', 'Wrote %s shots to %s.' % (len(self.merged_shots), direc))
        self.disableSaveButton()
        self.setMaxNarrays(1)

    def editAttributes(self, trace, addInt=0):
        # adopt seg2 attributes
        for attrib in trace.stats.seg2:
            trace.stats[attrib.lower()] = trace.stats.seg2[attrib]
        # transform channel number
        trace.stats.channel = unicode(int(trace.stats.seg2['CHANNEL_NUMBER']) + addInt)
        # set misc
        trace.stats.network = unicode(self.ui.lineEdit_network.text())
        trace.stats.station = unicode(self.ui.lineEdit_station.text())
        trace.stats.location = unicode(self.ui.lineEdit_location.text())
        trace.stats.comments = unicode('merged pseude shot')
        trace.stats._format = unicode('PICKLE')
        trace.stats.pop('seg2')
        trace.stats.pop('channel_number')
        trace.stats.pop('source_location')


class Plot_shot_window(object):
    def __init__(self, gui, survey, shotnumber):
        self.parentgui = gui
        self.mainwindow = gui.mainwindow
        self.survey = survey
        self.shotnumber = shotnumber
        self.init_widget()
        self.start_widget()

    def init_widget(self):
        qwidget = QtGui.QWidget()
        qwidget.closeEvent = self.close
        ui = Ui_plot_shots()
        ui.setupUi(qwidget)
        self.ui = ui
        self.qwidget = qwidget

    def start_widget(self, maximized=False):
        self.qwidget.show()

    def plot(self):
        plt.interactive(False)
        shot = self.survey.data[self.shotnumber]
        fig = plt.figure()
        canvas = fig.canvas
        self.ui.gridLayout.addWidget(canvas)
        shot.matshow(fig=fig, qt=True, qtMainwindow=self.mainwindow)
        
    def close(self, event=None):
        self.qwidget.close()
        self.parentgui.refreshPickedWidgets()


class Plot_shots_window(object):
    def __init__(self, gui, survey):
        self.parentgui = gui
        self.mainwindow = gui.mainwindow
        self.survey = survey
        self.init_widget()
        self.start_widget()

    def init_widget(self):
        qwidget = QtGui.QWidget()
        qwidget.closeEvent = self.close
        ui = Ui_plot_shots()
        ui.setupUi(qwidget)
        self.ui = ui
        self.qwidget = qwidget

    def start_widget(self, maximized=False):
        self.qwidget.showMaximized()

    def plot(self, rows=2, columns=3):
        figPerPlot = columns * rows
        shotlist = list(self.survey.getShotlist())
        shotlist.sort()
        nshots = len(shotlist)
        index = 0

        plt.interactive(False)

        tabs = QtGui.QTabWidget()
        self.ui.gridLayout.addWidget(tabs)

        for shotnumber in shotlist:
            shot = self.survey.getShot(shotnumber)

            if not index % (figPerPlot):
                row = 0
                column = 0
                start = shotlist[index]
                if nshots < index + figPerPlot:
                    end = shotlist[-1]
                else:
                    end = shotlist[index + figPerPlot - 1]
                name = '[{0} - {1}]'.format(start, end)
                grid = self.initNewTab(tabs, name)

            fig = plt.figure()
            canvas = fig.canvas
            grid.addWidget(canvas, row, column)
            shot.matshow(fig=fig, qt=True, qtMainwindow=self.mainwindow)
            index += 1
            column += 1
            if column == columns:
                row += 1
                column = 0

    def initNewTab(self, tabs, name):
        tab = QtGui.QWidget()
        tabs.addTab(tab, name)
        grid = QtGui.QGridLayout()
        tab.setLayout(grid)
        return grid

    def close(self, event=None):
        self.qwidget.close()
        self.parentgui.refreshPickedWidgets()
        
