# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
#   Copyright 2017 Marcel Paffrath (Ruhr-Universitaet Bochum, Germany)
#
#   This file is part of ActiveSeismoPick3D
#----------------------------------------------------------------------------

import math
import numpy as np
import os
import sys
from datetime import datetime

from asp3d.core import seismicArrayPreparation
from asp3d.core import seismicshot
from asp3d.gui.threads import Multipicker_Thread
from asp3d.util.surveyUtils import cleanUp
from asp3d.util.utils import worker


def picker(st_tuple):
    shot, traceID = st_tuple
    return (shot.getShotnumber(), traceID, shot.pickTrace(traceID))


class Survey(object):
    def __init__(self, path, sourcefile=None, receiverfile=None, seisArray=None, useDefaultParas=False, fstart=None,
                 fend=None):
        '''
        The Survey Class contains all shots [class: Seismicshot] of a survey
        as well as the aquisition geometry and the topography.

        It contains methods to pick all traces of all shots.

        It contains several methods e.g. for plotting of all picks (and postprocessing),
        creating plots for all shots.
        '''
        self.data = {}
        self.seisarray = seisArray
        self._topography = None
        self._recfile = receiverfile
        self._sourcefile = sourcefile
        self._obsdir = path
        self._generateSurvey(fstart, fend)
        self._initiate_SRfiles()
        if useDefaultParas == True:
            self.setParametersForAllShots()
        self._removeAllEmptyTraces()
        self._updateShots()
        self.setInitialPickwindow()
        self.picked = False

    def _coordsFromSeisArray(self):
        self._receiverCoords = self.seisarray.getReceiverCoordinates()
        self._sourceCoords = self.seisarray.getSourceCoordinates()

    def _coordsFromFiles(self):
        self._receiversFromFile()
        self._sourcesFromFile()

    def _receiversFromFile(self):
        self._receiverCoords = {}
        reclist = open(self.getReceiverfile(), 'r').readlines()
        for line in reclist:
            line = line.split()
            traceID = int(line[0])
            x = float(line[1])
            y = float(line[2])
            z = float(line[3])
            self._receiverCoords[traceID] = (x, y, z)

    def _sourcesFromFile(self):
        self._sourceCoords = {}
        reclist = open(self.getSourcefile(), 'r').readlines()
        for line in reclist:
            line = line.split()
            sourceID = int(line[0])
            x = float(line[1])
            y = float(line[2])
            z = float(line[3])
            self._sourceCoords[sourceID] = (x, y, z)

    def _initiate_SRfiles(self):
        if self._recfile == None and self._sourcefile == None:
            if self.seisarray == None:
                raise RuntimeError('No SeisArray defined. No source or receiver file given.')
            self._coordsFromSeisArray()
        else:
            self._coordsFromFiles()
            self.loadArray(self._obsdir, self._recfile, self._sourcefile)
        for shotnumber in self.data.keys():
            shot = self.data[shotnumber]
            shot.setShotnumber(shotnumber)
            shot.setReceiverCoords(self._receiverCoords)
            shot.setSourceCoords(self._sourceCoords[shotnumber])
        if self.check2D():
            print('Survey is two dimensional!')
            self.twoDim = True
        else:
            self.twoDim = False

    def _generateSurvey(self, fstart=None, fend=None):
        shot_dict = {}
        shotlist = self.getShotlist()
        obsfiles = []
        for shotnumber in shotlist:  # loop over data files
            # generate filenames and read manual picks to a list
            # fileending = '.sg2'
            if fend == None:
                fend = '_pickle.dat'
            obsfile=os.path.join(self._obsdir, fstart + str(shotnumber)) + fend
            if not os.path.exists(obsfile):
                print('File {filename} does not exist'.format(filename=obsfile))
                continue
            obsfiles.append((shotnumber, obsfile))
            
        for shotnumber, obsfile in obsfiles:
            if obsfile not in shot_dict.keys():
                shot_dict[shotnumber] = []
            shot_dict[shotnumber] = seismicshot.SeismicShot(obsfile)
            shot_dict[shotnumber].setParameters('shotnumber', shotnumber)

        if not len(obsfiles) > 0:
            raise ValueError('No files found.')
        
        self.data = shot_dict
        print ("Generated Survey object for %d shots" % len(shotlist))
        print ("Total number of traces: %d \n" % self.countAllTraces())

    def _removeAllEmptyTraces(self):
        '''
        Removes traces of the dataset that are not found in the input receiver files.
        '''
        logfile = 'removeEmptyTraces.out'
        count = 0
        for shot in self.data.values():
            removed = shot.removeEmptyTraces()
            if removed is not None:
                if count == 0: outfile = open(logfile, 'w')
                count += 1
                outfile.writelines('shot: %s, removed empty traces: %s\n'
                                   % (shot.getShotnumber(), removed))
        print ("\nremoveEmptyTraces: Finished! Removed %d traces" % count)
        if count > 0:
            print ("See %s for more information "
                   "on removed traces." % (logfile))
            outfile.close()

    def _updateShots(self):
        '''
        Removes traces that do not exist in the dataset for any reason,
        but were set in the input files.
        '''
        logfile = 'updateShots.out'
        count = 0
        countTraces = 0
        for shot in self.data.values():
            del_traceIDs = shot.updateTraceList()
            if len(del_traceIDs) > 0:
                if count == 0: outfile = open(logfile, 'w')
                count += 1
                countTraces += len(del_traceIDs)
                outfile.writelines("shot: %s, removed traceID(s) %s because "
                                   "they were not found in the corresponding stream\n"
                                   % (shot.getShotnumber(), del_traceIDs))

        print ("\nupdateShots: Finished! Updated %d shots and removed "
               "%d traces" % (count, countTraces))
        if count > 0:
            print ("See %s for more information "
                   "on removed traces." % (logfile))
            outfile.close()

    def check2D(self):
        if self.seisarray is None:
            print('Check2D: No SeisArray defined')
            return
        if self.seisarray.check2D():
            return True
        else:
            return False

    def updateSeisArray(self, seisArray):
        if not type(seisArray) == seismicArrayPreparation.SeisArray:
            print('Wrong data type.')
            return
        self.seisarray = seisArray
        self._initiate_SRfiles()

    def setParametersForAllShots(self, cutwindow=(0, 0.2), tmovwind=0.3,
                                 tsignal=0.03, tgap=0.0007):
        if (cutwindow == (0, 0.2) and tmovwind == 0.3 and
                    tsignal == 0.03 and tgap == 0.0007):
            print ("Warning: Standard values used for "
                   "setParamters. This might not be clever.")
        for shot in self.data.values():
            shot.setCut(cutwindow)
            shot.setTmovwind(tmovwind)
            shot.setTsignal(tsignal)
            shot.setTgap(tgap)
            shot.setOrder(order=4)
        print ("setParametersForAllShots: Parameters set to:\n"
               "cutwindow = %s, tMovingWindow = %f, tsignal = %f, tgap = %f"
               % (cutwindow, tmovwind, tsignal, tgap))

    def loadArrayFromPickle(self, filename):
        from asp3d.core.seismicArrayPreparation import SeisArray
        array = SeisArray.from_pickle(filename)
        self.seisarray = array

    def loadArray(self, path, receiverfile, sourcefile):
        from asp3d.core.seismicArrayPreparation import SeisArray

        array = SeisArray(os.path.join(path, receiverfile))
        array.addSourceLocations(os.path.join(path, sourcefile))
        self.seisarray = array

    def setManualPicksFromFiles(self, directory='picks'):
        '''
        Read manual picks from *.pck files in a directory.
        Can be used for comparison of automatic and manual picks.

        The * must be identical with the shotnumber.
        '''
        for shot in self.data.values():
            shot.setManualPicksFromFile(directory)

    def getDiffsFromManual(self):
        '''
        Returns a dictionary with the differences between manual and automatic pick for all shots.
        Key: Seismicshot [object]
        '''
        diffs = {}
        for shot in self.data.values():
            if not shot in diffs.keys():
                diffs[shot] = {}
            for traceID in shot.getTraceIDlist():
                if shot.getPickFlag(traceID) and shot.getManualPickFlag(
                        traceID) == 1:
                    diffs[shot][traceID] = shot.getPick(
                        traceID) - shot.getManualPick(traceID)
        return diffs

    def plotDiffs(self):
        '''
        Creates a plot of all Picks colored by the
        difference between automatic and manual pick.
        '''
        import matplotlib.pyplot as plt
        diffs = []
        dists = []
        mpicks = []
        picks = []
        diffsDic = self.getDiffsFromManual()
        for shot in self.data.values():
            for traceID in shot.getTraceIDlist():
                if shot.getPickFlag(traceID) and shot.getManualPickFlag(
                        traceID) == 1:
                    dists.append(shot.getDistance(traceID))
                    mpicks.append(shot.getManualPick(traceID))
                    picks.append(shot.getPick(traceID))
                    diffs.append(diffsDic[shot][traceID])

        labelm = 'manual picks'
        labela = 'automatic picks'

        fig = plt.figure()
        ax = fig.add_subplot(111)

        sc_a = ax.scatter(dists, picks, c='0.5', s=10, edgecolors='none',
                          label=labela, alpha=0.3)
        sc = ax.scatter(dists, mpicks, c=diffs, s=5, edgecolors='none',
                        label=labelm)
        cbar = plt.colorbar(sc, fraction=0.05)
        cbar.set_label(labelm)
        ax.set_xlabel('Distance [m]')
        ax.set_ylabel('Time [s]')
        ax.text(0.5, 0.95, 'Plot of all MANUAL picks', transform=ax.transAxes,
                horizontalalignment='center')
        plt.legend()

    def plotHist(self, nbins=20, ax=None):
        '''
        Plot a histogram of the difference between automatic and manual picks.
        '''
        import matplotlib.pyplot as plt
        plt.interactive(True)
        diffs = []
        if ax == None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
        for shot in self.data.values():
            for traceID in shot.getTraceIDlist():
                if shot.getPickFlag(traceID) and shot.getManualPickFlag(
                        traceID) == 1:
                    diffs.append(self.getDiffsFromManual()[shot][traceID])
        hist = plt.hist(diffs, nbins, histtype='step', normed=True,
                        stacked=True)
        plt.title(
            'Histogram of the differences between automatic and manual pick')
        plt.xlabel('Difference in time (auto - manual) [s]')
        return diffs

    def pickAllShots(self, vmin=333, vmax=5500, folm=0.6, HosAic='hos',
                     aicwindow=(15, 0), cores=1, threading=False, gui=None, repick=False):
        '''
        Automatically pick all traces of all shots of the survey.

        :param: vmin, vmax, minimum (maximum) permitted apparent velocity on direct path between src and rec
        :type: real

        :param: folm, fraction of local maximum for HOS pick (0.6 = 60% of the highest maximum)
        :type: real

        :param: HosAic, pick with hos only ('hos') or use AIC ('aic')
        :type: string

        :param: aicwindow, window around the initial pick to search for local AIC min (samples)
        :type: tuple
        '''
        starttime = datetime.now()
        count = 0
        tpicksum = starttime - starttime

        shotlist = []

        if repick:
            self.clearAllPicks()

        if threading:
            self.gui = gui

        print('pickAllShots: Setting pick parameters...')
        for shot in self.data.values():
            shot.setVmin(vmin)
            shot.setVmax(vmax)
            count += 1
            shot.setPickParameters(folm=folm, method=HosAic, aicwindow=aicwindow)
            for traceID in shot.getTraceIDlist():
                st_tuple =(shot, traceID)
                shotlist.append(st_tuple)
            

        print('pickAllShots: Starting to pick...')
        tstartpick = datetime.now()
        if cores > 1:
            print('Picking parallel on %s cores.' % cores)
        elif cores == 1:
            print('Picking serial on one core.')
        else:
            raise ValueError('cores must be >= 1')
        if threading:
            # self.mtp_obj = multithread_picker(parent = self.gui.mainwindow, survey = self,
            #                                   ncores = cores, callback = self.finishPicking)
            # self.mtp_obj.process()
            mpt = Multipicker_Thread(self.gui.mainwindow, picker, shotlist, cores, self.gui.mainUI.progressBar)
            self.pickstarttime = starttime
            self.results = mpt.run()
            mpt.finished.connect(self.finishMultipickerThread)
        else:
            picks = worker(picker, shotlist, cores)
            self.finishPicking(picks, threading=False, starttime=tstartpick)

    def clearAllPicks(self):
        '''
        Clear all Picks for all shots that are part of the survey.data
        '''
        for shot in self.data.values():
            for traceID in shot.getTraceIDlist():
                shot.removePick(traceID)

    def finishMultipickerThread(self):
        picks = self.results.get()
        self.finishPicking(picks, True, self.pickstarttime)
        del (self.results)
        del (self.pickstarttime)

    def finishPicking(self, picks=None, threading=True, starttime=None):
        print('Done!')
        print('\npickAllShots: Finished\n')

        if picks:
            for item in picks:
                shotnumber, traceID, pick = item
                self.getShotForShotnumber(shotnumber).setPick(traceID, pick, revised=False)

                    # tpicksum += (datetime.now() - tstartpick);
                    # tpick = tpicksum / count
                    # tremain = (tpick * (len(self.getShotDict()) - count))
                    # tend = datetime.now() + tremain
                    # progress = float(count) / float(len(self.getShotDict())) * 100
                    # self._update_progress(shot.getShotname(), tend, progress)

        if starttime:
            tpick = datetime.now() - starttime
            print('Finished picking after %s [H:MM:SS].' % tpick)

        self.filterSNR()
        self.setEarllate()

        self.picked = True
        ntraces = self.countAllTraces()
        pickedtraces = self.countAllPickedTraces()
        print('Picked %s / %s traces (%d %%)\n'
              % (pickedtraces, ntraces,
                 float(pickedtraces) / float(ntraces) * 100.))
        if threading:
            self.gui.finishAutopicker()

    def filterSNR(self):
        print('Starting filterSNR...')
        for shot in self.data.values():
            for traceID in shot.getTraceIDlist():
                shot.setSNR(traceID)
                # if shot.getSNR(traceID)[0] < snrthreshold:
                if shot.getPick(traceID) <= 0:
                    shot.removePick(traceID)
                if shot.getSNR(traceID)[0] < shot.getSNRthreshold(traceID):
                    shot.removePick(traceID)

    def setEarllate(self):
        print('Starting setEarllate...')
        for shot in self.data.values():
            for traceID in shot.getTraceIDlist():
                # set epp and lpp if SNR > 1 (else earllatepicker cant set values)
                if shot.getSNR(traceID)[0] > 1:
                    shot.setEarllatepick(traceID)

    def cleanBySPE(self, maxSPE):
        '''
        Sets all picks as invalid if they exceed a certain value of the symmetric pick error.
        '''
        for shot in self.data.values():
            for traceID in shot.getTraceIDlist():
                if shot.getPickFlag(traceID):
                    if shot.getSymmetricPickError(traceID) > maxSPE:
                        shot.setPickFlag(traceID, False)

    def plotSPE(self):
        '''
        Plots the symmetric pick error sorted by magnitude.
        '''
        import matplotlib.pyplot as plt
        spe = []
        for shot in self.data.values():
            for traceID in shot.getTraceIDlist():
                if shot.getPickFlag(traceID):
                    spe.append(shot.getSymmetricPickError(traceID))
        spe.sort()
        plt.plot(spe, label='SPE')
        plt.ylabel('Symmetric Pickerror')
        plt.legend()

    def recover(self):
        '''
        Recovers all manually removed picks. Still regards SNR threshold.
        '''
        print('Recovering survey...')
        numpicks = 0
        for shot in self.data.values():
            for traceID in shot.getTraceIDlist():
                if not shot.getPickFlag(traceID):
                    shot.setPickFlag(traceID, True)
                    if shot.getSNR(traceID)[0] < shot.getSNRthreshold(traceID):
                        shot.removePick(traceID)
                    else:
                        numpicks += 1
        print('Recovered %d picks' % numpicks)

    def setArtificialPick(self, traceID, pick):
        '''
        Sets an artificial pick for a certain receiver (traceID) for all shots.
        '''
        for shot in self.data.values():
            shot.setPick(traceID, pick, revised=True)
            shot.setPickwindow(traceID, shot.getCut())

    def setInitialPickwindow(self):
        for shot in self.data.values():
            length_differs = False
            for index, traceID in enumerate(shot.getTraceIDlist()):
                stats = shot.stream.traces[index].stats
                if index == 0:
                    pickwindow_0 = (0, (stats.endtime - stats.starttime))
                pickwindow = (0, (stats.endtime - stats.starttime))
                if not pickwindow == pickwindow_0:
                    length_differs = True
                    print('Warning: individual trace length differs for shot %s' % shot.getShotnumber())
                shot.setPickwindow(traceID, pickwindow)
            if length_differs:
                print('Warning: Can not set a consistent CUT-window for all traces of shot %s' % shot.getShotnumber())
            shot.setCut(pickwindow)

    def countAllTraces(self):
        '''
        Returns the number of traces in total.
        '''
        numtraces = 0
        for shot in self.getShotlist():
            for rec in self.getReceiverlist():
                numtraces += 1

        return numtraces

    def getShotlist(self):
        '''
        Returns a list of all shotnumbers contained in the set Sourcefile.
        '''
        if self._recfile == None and self._sourcefile == None:
            if self.seisarray == None:
                raise RuntimeError('No SeisArray defined. No source or receiver file given.')
            return self.seisarray.getSourceCoordinates().keys()

        filename = self.getSourcefile()
        srcfile = open(filename, 'r')
        shotlist = []
        for line in srcfile.readlines():
            line = line.split()
            shotlist.append(int(line[0]))

        return shotlist

    def getReceiverlist(self):
        '''
        Returns a list of all trace IDs contained in the set Receiverfile.
        '''
        if self._recfile == None and self._sourcefile == None:
            if self.seisarray == None:
                raise RuntimeError('No SeisArray defined. No source or receiver file given.')
            return self.seisarray.getReceiverCoordinates().keys()

        filename = self.getReceiverfile()
        recfile = open(filename, 'r')
        reclist = []
        for line in recfile.readlines():
            line = line.split()
            reclist.append(int(line[0]))

        return reclist

    def getShotDict(self):
        return self.data

    def getShot(self, shotnumber):
        return self.data[shotnumber]

    def getSourcefile(self):
        return self._sourcefile

    def getReceiverfile(self):
        return self._recfile

    def getPath(self):
        return self._obsdir

    def getStats(self):
        '''
        Generates and returns a dictionary containing statistical information
        of the survey.
        
        Key: shotnumber
        '''
        info_dict = {}
        for shot in self.data.values():
            pickedTraces = 0
            snrlist = []
            dist = []
            numtraces = len(shot.getTraceIDlist())
            for traceID in shot.getTraceIDlist():
                snrlist.append(shot.getSNR(traceID)[0])
                dist.append(shot.getDistance(traceID))
                if shot.getPickFlag(traceID):
                    pickedTraces += 1
            info_dict[shot.getShotnumber()] = {'numtraces': numtraces,
                                               'picked traces': [pickedTraces,
                                                                 '%2.2f %%' % (
                                                                     float(
                                                                         pickedTraces) /
                                                                     float(
                                                                         numtraces) * 100)],
                                               'mean SNR': np.mean(snrlist),
                                               'mean distance': np.mean(dist)}

        return info_dict

    def getShotForShotnumber(self, shotnumber):
        '''
        Returns Seismicshot [object] of a certain shotnumber if possible.
        '''
        for shot in self.data.values():
            if shot.getShotnumber() == shotnumber:
                return shot

    def exportFMTOMO(self, directory='FMTOMO_export', sourcefile='input_sf.in',
                     ttFileExtension='.tt'):
        '''
        Exports all picks into a directory as travel time files readable by FMTOMO obsdata.
        '''

        def getAngle(distance):
            PI = np.pi
            R = 6371.
            angle = distance * 180 / (PI * R)
            return angle

        count = 0
        fmtomo_factor = 1000  # transforming [m/s] -> [km/s]
        LatAll = []
        LonAll = []
        DepthAll = []
        srcfile = open(directory + '/' + sourcefile, 'w')
        srcfile.writelines('%10s\n' % len(self.data))  # number of sources
        for shotnumber in self.getShotlist():
            shot = self.getShotForShotnumber(shotnumber)
            ttfilename = str(
                shotnumber) + ttFileExtension  # filename of travel time file for this shot
            (x, y, z) = shot.getSrcLoc()  # getSrcLoc returns (x, y, z)
            srcfile.writelines('%10s %10s %10s\n' % (
                getAngle(y), getAngle(x), (-1) * z))  # transform to lat, lon, depth
            LatAll.append(getAngle(y))
            LonAll.append(getAngle(x))
            DepthAll.append((-1) * z)
            srcfile.writelines('%10s\n' % 1)
            srcfile.writelines('%10s %10s %10s\n' % (1, 1, ttfilename))
            ttfile = open(directory + '/' + ttfilename, 'w')
            traceIDlist = shot.getTraceIDlist()
            traceIDlist.sort()
            ttfile.writelines(str(self.countPickedTraces(shot)) + '\n')
            for traceID in traceIDlist:
                if shot.getPickFlag(traceID):
                    pick = shot.getPick(traceID) * fmtomo_factor
                    delta = shot.getSymmetricPickError(traceID) * fmtomo_factor
                    (x, y, z) = shot.getRecLoc(traceID)
                    ttfile.writelines('%20s %20s %20s %10s %10s\n' % (
                        getAngle(y), getAngle(x), (-1) * z, pick, delta))
                    LatAll.append(getAngle(y))
                    LonAll.append(getAngle(x))
                    DepthAll.append((-1) * z)
                    count += 1
            ttfile.close()
        srcfile.close()
        msg = 'Wrote output for {0} traces\n' \
              'WARNING: output generated for FMTOMO-obsdata. Obsdata seems ' \
              'to take Lat, Lon, Depth and creates output for FMTOMO as ' \
              'Depth, Lat, Lon\nDimensions of the seismic Array, ' \
              'transformed for FMTOMO, are Depth({1}, {2}), Lat({3}, {4}), ' \
              'Lon({5}, {6})'.format(count,
                                     min(DepthAll),
                                     max(DepthAll),
                                     min(LatAll),
                                     max(LatAll),
                                     min(LonAll),
                                     max(LonAll))
        print(msg)

    def countPickedTraces(self, shot):
        '''
        Counts all picked traces of a shot (type Seismicshot).
        '''
        count = 0
        for traceID in shot.getTraceIDlist():
            if shot.getPickFlag(traceID):
                count += 1
        return count

    def countAllPickedTraces(self):
        '''
        Counts all picked traces of the survey.
        '''
        count = 0
        if not self.picked:
            return count

        for shot in self.data.values():
            for traceID in shot.getTraceIDlist():
                if shot.getPickFlag(traceID):
                    count += 1
        return count

    def countAllRevisedTraces(self):
        '''
        Counts all picked traces of the survey.
        '''
        count = 0
        if not self.picked:
            return count

        for shot in self.data.values():
            for traceID in shot.getTraceIDlist():
                if shot.getRevised(traceID):
                    count += 1
        return count

    def plotAllShots(self, rows=3, columns=4, mode='3d'):
        '''
        Plots all shots as Matrices with the color corresponding to the traveltime for each receiver.
        IMPORTANT NOTE: Topography (z - coordinate) is not considered in the diagrams!
        '''
        import matplotlib.pyplot as plt
        plt.interactive(True)

        fig = plt.figure()
        ax = fig.add_subplot(111)

        figPerSubplot = columns * rows

        index = 1

        for shotnumber in self.getShotlist():
            if index <= figPerSubplot:
                ax = fig.add_subplot(rows, columns, index)
                if mode == '3d':
                    self.getShot(shotnumber).matshow(ax=ax, colorbar=False,
                                                     annotations=True,
                                                     legend=False)
                elif mode == '2d':
                    self.getShot(shotnumber).plot2dttc(ax)
                    self.getShot(shotnumber).plotmanual2dttc(ax)
                index += 1
            if index > figPerSubplot:
                fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0,
                                    hspace=0)
                fig = plt.figure()
                index = 1

        fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0,
                            hspace=0)

    def plotAllPicks(self, plotRemoved=False, colorByVal='log10SNR', ax=None,
                     cbar=None, refreshPlot=False):
        '''
        Plots all picks over the distance between source and receiver. Returns (ax, region).
        Picks can be checked and removed by using region class (asp3d.core.postprocessing.regions)

        :param: plotRemoved, if True plots traces that were picked but removed from the survey (flag = False)
        :type: logical

        :param: colorByVal, can be "log10SNR", "pickerror", or "spe"
        :type: str

        Examples:

        regions.chooseRectangles():
         - lets the user choose several rectangular regions in the plot

        regions.plotTracesInRegions():
         - creates plots (shot.plot_traces) for all traces in the active regions (i.e. chosen by e.g. chooseRectangles)

        regions.setActiveRegionsForDeletion():
         - highlights all shots in a the active regions for deletion

        regions.deleteMarkedPicks():
         - deletes the picks (pick flag set to False) for all shots set for deletion

        regions.deselectSelection(number):
         - deselects the region of number = number

        '''

        import matplotlib.pyplot as plt
        plt.interactive(True)
        from asp3d.core.postprocessing import regions

        dist, pick, snrlog, pickerror, spe = self.preparePlotAllPicks(plotRemoved)

        color = {'log10SNR': snrlog,
                 'pickerror': pickerror,
                 'spe': spe}
        self.color = color
        if refreshPlot is False:
            ax, cbar, sc, label = self.createPlot(dist, pick, color[colorByVal],
                                                  label='%s' % colorByVal)
            region = regions(ax, cbar, self)
            ax.legend()
            return (ax, region)
        if refreshPlot is True:
            ax, cbar, sc, label= self.createPlot(dist, pick, color[colorByVal],
                                                 label='%s' % colorByVal, ax=ax,
                                                 cbar=cbar)
            ax.legend()
            return ax

    def preparePlotAllPicks(self, plotRemoved=False):
        dist = []
        pick = []
        snrlog = []
        pickerror = []
        spe = []

        for shot in self.data.values():
            for traceID in shot.getTraceIDlist():
                if plotRemoved == False:
                    if shot.getPickFlag(
                            traceID) or plotRemoved == True:
                        dist.append(shot.getDistance(traceID))
                        pick.append(shot.getPick(traceID))
                        snrlog.append(math.log10(shot.getSNR(traceID)[0]))
                        pickerror.append(shot.getPickError(traceID))
                        spe.append(shot.getSymmetricPickError(traceID))

        return dist, pick, snrlog, pickerror, spe

    def createPlot(self, dist, pick, inkByVal, label=None, ax=None, cbar=None):
        '''
        Used by plotAllPicks.
        '''
        import matplotlib.pyplot as plt
        # plt.interactive(True)
        cm = plt.cm.jet
        if ax is None:
            print('Generating new plot...')
            fig = plt.figure()
            ax = fig.add_subplot(111)
            sc = ax.scatter(dist, pick, cmap=cm, c=inkByVal, s=5,
                            edgecolors='none', label=label)
            cbar = fig.colorbar(sc, fraction=0.05)
            cbar.set_label(label)
            ax.set_xlabel('Distance [m]')
            ax.set_ylabel('Time [s]')
            ax.text(0.5, 0.95, 'Plot of all picks', transform=ax.transAxes,
                    horizontalalignment='center')
        else:
            sc = ax.scatter(dist, pick, cmap=cm, c=inkByVal, s=5,
                            edgecolors='none', label=label)
            if cbar is not None:
                cbar.ax.clear()
                cbar = ax.figure.colorbar(sc, cax=cbar.ax)
                cbar.set_label(label)
            # if cbar is 'init':
            #     cbar = ax.figure.colorbar(sc, fraction=0.05)
            #     cbar.set_label(label)                
            ax.set_xlabel('Distance [m]')
            ax.set_ylabel('Time [s]')
            ax.text(0.5, 0.95, 'Plot of all picks', transform=ax.transAxes,
                    horizontalalignment='center')
        return ax, cbar, sc, label

    def _update_progress(self, shotname, tend, progress):
        sys.stdout.write(
            'Working on shot %s. ETC is %02d:%02d:%02d [%2.2f %%]\r' % (
                shotname,
                tend.hour,
                tend.minute,
                tend.second,
                progress))
        sys.stdout.flush()

    def saveSurvey(self, filename='survey.pickle'):
        '''
        Save Survey object to a file. 
        Can be loaded by using Survey.from_pickle(filename).
        '''
        try:
            import cPickle
        except ImportError:
            import _pickle as cPickle
        cleanUp(self)
        outfile = open(filename, 'wb')

        cPickle.dump(self, outfile, -1)
        print('saved Survey to file %s' % (filename))

    @staticmethod
    def from_pickle(filename):
        try:
            import cPickle
        except ImportError:
            import _pickle as cPickle
        infile = open(filename, 'rb')
        survey = cPickle.load(infile)
        print('Loaded %s' % filename)
        return survey
