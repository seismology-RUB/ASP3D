#!/usr/bin/env python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
#   Copyright 2017 Marcel Paffrath (Ruhr-Universitaet Bochum, Germany)
#
#   Several functions in this file are the work of Kueperkoch et al.
#
#   This file is part of ActiveSeismoPick3D
#----------------------------------------------------------------------------

import numpy as np
import matplotlib.pyplot as plt

from obspy import UTCDateTime, Stream

def _pickle_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)

    
def worker(func, input, cores='max', async=False):
    import multiprocessing

    if cores == 'max':
        cores = multiprocessing.cpu_count()

    pool = multiprocessing.Pool(cores)
    if async == True:
        result = pool.map_async(func, input)
    else:
        result = pool.map(func, input)
    pool.close()
    return result


def full_range(stream):
    '''
    takes a stream object and returns the latest end and the earliest start
    time of all contained trace objects
    :param stream: seismological data stream
    :type stream: `~obspy.core.stream.Stream`
    :return: minimum start time and maximum end time
    '''
    min_start = UTCDateTime()
    max_end = None
    for trace in stream:
        if trace.stats.starttime < min_start:
            min_start = trace.stats.starttime
        if max_end is None or trace.stats.endtime > max_end:
            max_end = trace.stats.endtime
    return min_start, max_end


def prepTimeAxis(stime, trace):
    '''
    takes a starttime and a trace object and returns a valid time axis for
    plotting
    :param stime: start time of the actual seismogram as UTCDateTime
    :param trace: seismic trace object
    :return: valid numpy array with time stamps for plotting
    '''
    nsamp = trace.stats.npts
    srate = trace.stats.sampling_rate
    tincr = trace.stats.delta
    etime = stime + nsamp / srate
    time_ax = np.arange(stime, etime, tincr)
    if len(time_ax) < nsamp:
        print('elongate time axes by one datum')
        time_ax = np.arange(stime, etime + tincr, tincr)
    elif len(time_ax) > nsamp:
        print('shorten time axes by one datum')
        time_ax = np.arange(stime, etime - tincr, tincr)
    if len(time_ax) != nsamp:
        raise ValueError('{0} samples of data \n '
                         '{1} length of time vector \n'
                         'delta: {2}'.format(nsamp, len(time_ax), tincr))
    return time_ax


def earllatepicker(X, nfac, TSNR, Pick1, iplot=None, stealth_mode=False):
    '''
    Function to derive earliest and latest possible pick after Diehl & Kissling (2009)
    as reasonable uncertainties. Latest possible pick is based on noise level,
    earliest possible pick is half a signal wavelength in front of most likely
    pick given by PragPicker or manually set by analyst. Most likely pick
    (initial pick Pick1) must be given.

    :param: X, time series (seismogram)
    :type:  `~obspy.core.stream.Stream`

    :param: nfac (noise factor), nfac times noise level to calculate latest possible pick
    :type: int

    :param: TSNR, length of time windows around pick used to determine SNR [s]
    :type: tuple (T_noise, T_gap, T_signal)

    :param: Pick1, initial (most likely) onset time, starting point for earllatepicker
    :type: float

    :param: iplot, if given, results are plotted in figure(iplot)
    :type: int
    '''

    assert isinstance(X, Stream), "%s is not a stream object" % str(X)

    LPick = None
    EPick = None
    PickError = None
    if stealth_mode is False:
        print('earllatepicker: Get earliest and latest possible pick'
              ' relative to most likely pick ...')

    x = X[0].data
    t = np.arange(0, X[0].stats.npts / X[0].stats.sampling_rate,
                  X[0].stats.delta)
    inoise = getnoisewin(t, Pick1, TSNR[0], TSNR[1])
    # get signal window
    isignal = getsignalwin(t, Pick1, TSNR[2])
    # remove mean
    x = x - np.mean(x[inoise])
    # calculate noise level
    nlevel = np.sqrt(np.mean(np.square(x[inoise]))) * nfac
    # get time where signal exceeds nlevel
    ilup, = np.where(x[isignal] > nlevel)
    ildown, = np.where(x[isignal] < -nlevel)
    if not ilup.size and not ildown.size:
        if stealth_mode is False:
            print ("earllatepicker: Signal lower than noise level!\n"
                   "Skip this trace!")
        return LPick, EPick, PickError
    il = min(np.min(ilup) if ilup.size else float('inf'),
             np.min(ildown) if ildown.size else float('inf'))
    LPick = t[isignal][il]

    # get earliest possible pick

    EPick = np.nan
    count = 0
    pis = isignal

    # if EPick stays NaN the signal window size will be doubled
    while np.isnan(EPick):
        if count > 0:
            if stealth_mode is False:
                print("\nearllatepicker: Doubled signal window size %s time(s) "
                      "because of NaN for earliest pick." % count)
            isigDoubleWinStart = pis[-1] + 1
            isignalDoubleWin = np.arange(isigDoubleWinStart,
                                         isigDoubleWinStart + len(pis))
            if (isigDoubleWinStart + len(pis)) < X[0].data.size:
                pis = np.concatenate((pis, isignalDoubleWin))
            else:
                if stealth_mode is False:
                    print("Could not double signal window. Index out of bounds.")
                break
        count += 1
        # determine all zero crossings in signal window (demeaned)
        zc = crossings_nonzero_all(x[pis] - x[pis].mean())
        # calculate mean half period T0 of signal as the average of the
        T0 = np.mean(np.diff(zc)) * X[0].stats.delta  # this is half wave length!
        EPick = Pick1 - T0  # half wavelength as suggested by Diehl et al.

    # get symmetric pick error as mean from earliest and latest possible pick
    # by weighting latest possible pick two times earliest possible pick
    diffti_tl = LPick - Pick1
    diffti_te = Pick1 - EPick
    PickError = symmetrize_error(diffti_te, diffti_tl)

    if iplot is not None:
        if iplot > 1:
            p = plt.figure(iplot)
            p1, = plt.plot(t, x, 'k')
            p2, = plt.plot(t[inoise], x[inoise])
            p3, = plt.plot(t[isignal], x[isignal], 'r')
            p4, = plt.plot([t[0], t[int(len(t)) - 1]], [nlevel, nlevel], '--k')
            p5, = plt.plot(t[isignal[zc]], np.zeros(len(zc)), '*g',
                           markersize=14)
            plt.legend([p1, p2, p3, p4, p5],
                       ['Data', 'Noise Window', 'Signal Window', 'Noise Level',
                        'Zero Crossings'],
                       loc='best')
            plt.plot([t[0], t[int(len(t)) - 1]], [-nlevel, -nlevel], '--k')
            plt.plot([Pick1, Pick1], [max(x), -max(x)], 'b', linewidth=2)
            plt.plot([LPick, LPick], [max(x) / 2, -max(x) / 2], '--k')
            plt.plot([EPick, EPick], [max(x) / 2, -max(x) / 2], '--k')
            plt.plot([Pick1 + PickError, Pick1 + PickError],
                     [max(x) / 2, -max(x) / 2], 'r--')
            plt.plot([Pick1 - PickError, Pick1 - PickError],
                     [max(x) / 2, -max(x) / 2], 'r--')
            plt.xlabel('Time [s] since %s' % X[0].stats.starttime)
            plt.yticks([])
            plt.title(
                'Earliest-/Latest Possible/Most Likely Pick & Symmetric Pick Error, %s' %
                X[0].stats.station)
            plt.show()
            raw_input()
            plt.close(p)

    return EPick, LPick, PickError


def getSNR(X, TSNR, t1, tracenum=0):
    '''
    Function to calculate SNR of certain part of seismogram relative to
    given time (onset) out of given noise and signal windows. A safety gap
    between noise and signal part can be set. Returns SNR and SNR [dB] and
    noiselevel.

    :param: X, time series (seismogram)
    :type:  `~obspy.core.stream.Stream`

    :param: TSNR, length of time windows [s] around t1 (onset) used to determine SNR
    :type: tuple (T_noise, T_gap, T_signal)

    :param: t1, initial time (onset) from which noise and signal windows are calculated
    :type: float
    '''

    assert isinstance(X, Stream), "%s is not a stream object" % str(X)

    x = X[tracenum].data
    npts = X[tracenum].stats.npts
    sr = X[tracenum].stats.sampling_rate
    dt = X[tracenum].stats.delta
    t = np.arange(0, npts / sr, dt)

    # get noise window
    inoise = getnoisewin(t, t1, TSNR[0], TSNR[1])

    # get signal window
    isignal = getsignalwin(t, t1, TSNR[2])
    if np.size(inoise) < 1:
        print ("getSNR: Empty array inoise, check noise window!")
        return
    elif np.size(isignal) < 1:
        print ("getSNR: Empty array isignal, check signal window!")
        return

    # demean over entire waveform
    x = x - np.mean(x[inoise])

    # calculate ratios
    # noiselevel = np.sqrt(np.mean(np.square(x[inoise])))
    # signallevel = np.sqrt(np.mean(np.square(x[isignal])))

    noiselevel = np.abs(x[inoise]).max()
    signallevel = np.abs(x[isignal]).max()

    if not noiselevel == 0:
        SNR = signallevel / noiselevel
    else:
        SNR = np.nan
    SNRdB = 10 * np.log10(SNR)

    return SNR, SNRdB, noiselevel


def getnoisewin(t, t1, tnoise, tgap):
    '''
    Function to extract indeces of data out of time series for noise calculation.
    Returns an array of indeces.

    :param: t, array of time stamps
    :type:  numpy array

    :param: t1, time from which relativ to it noise window is extracted
    :type: float

    :param: tnoise, length of time window [s] for noise part extraction
    :type: float

    :param: tgap, safety gap between t1 (onset) and noise window to
            ensure, that noise window contains no signal
    :type: float
    '''

    # get noise window
    inoise, = np.where((t <= max([t1 - tgap, 0])) \
                       & (t >= max([t1 - tnoise - tgap, 0])))
    if np.size(inoise) < 1:
        print ("getnoisewin: Empty array inoise, check noise window!")

    return inoise


def getsignalwin(t, t1, tsignal):
    '''
    Function to extract data out of time series for signal level calculation.
    Returns an array of indeces.

    :param: t, array of time stamps
    :type:  numpy array

    :param: t1, time from which relativ to it signal window is extracted
    :type: float

    :param: tsignal, length of time window [s] for signal level calculation
    :type: float
    '''

    # get signal window
    isignal, = np.where((t <= min([t1 + tsignal, len(t)])) \
                        & (t >= t1))
    if np.size(isignal) < 1:
        print ("getsignalwin: Empty array isignal, check signal window!")

    return isignal


def symmetrize_error(dte, dtl):
    """
    takes earliest and latest possible pick and returns the symmetrized pick
    uncertainty value
    :param dte: relative lower uncertainty
    :param dtl: relative upper uncertainty
    :return: symmetrized error
    """
    return (dte + 2 * dtl) / 3


def crossings_nonzero_all(data):
    pos = data > 0
    npos = ~pos
    return ((pos[:-1] & npos[1:]) | (npos[:-1] & pos[1:])).nonzero()[0]
