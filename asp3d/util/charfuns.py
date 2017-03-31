#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created Oct/Nov 2014

Implementation of the Characteristic Functions (CF) published and described in:

Kueperkoch, L., Meier, T., Lee, J., Friederich, W., & EGELADOS Working Group, 2010:
Automated determination of P-phase arrival times at regional and local distances
using higher order statistics, Geophys. J. Int., 181, 1159-1170

Kueperkoch, L., Meier, T., Bruestle, A., Lee, J., Friederich, W., & EGELADOS
Working Group, 2012: Automated determination of S-phase arrival times using
autoregressive prediction: application ot local and regional distances, Geophys. J. Int.,
188, 687-702.

:author: MAGS2 EP3 working group
"""

import numpy as np
from obspy.core import Stream


class CharacteristicFunction(object):
    '''
    SuperClass for different types of characteristic functions.
    '''

    def __init__(self, data, cut, t2=None, order=None, t1=None, fnoise=None, stealthMode=False):
        '''
        Initialize data type object with information from the original
        Seismogram.

        :param: data
        :type: `~obspy.core.stream.Stream`

        :param: cut
        :type: tuple

        :param: t2
        :type: float

        :param: order
        :type: int

        :param: t1
        :type: float (optional, only for AR)

        :param: fnoise
        :type: float (optional, only for AR)
        '''

        assert isinstance(data, Stream), "%s is not a stream object" % str(data)

        self.orig_data = data
        self.dt = self.orig_data[0].stats.delta
        self.setCut(cut)
        self.setTime1(t1)
        self.setTime2(t2)
        self.setOrder(order)
        self.setFnoise(fnoise)
        self.setARdetStep(t2)
        self.calcCF(self.getDataArray())
        self.arpara = np.array([])
        self.xpred = np.array([])
        self._stealthMode = stealthMode

    def __str__(self):
        return '''\n\t{name} object:\n
        Cut:\t\t{cut}\n
        t1:\t{t1}\n
        t2:\t{t2}\n
        Order:\t\t{order}\n
        Fnoise:\t{fnoise}\n
        ARdetStep:\t{ardetstep}\n
        '''.format(name=type(self).__name__,
                   cut=self.getCut(),
                   t1=self.getTime1(),
                   t2=self.getTime2(),
                   order=self.getOrder(),
                   fnoise=self.getFnoise(),
                   ardetstep=self.getARdetStep[0]())

    def getCut(self):
        return self.cut

    def setCut(self, cut):
        self.cut = cut

    def getTime1(self):
        return self.t1

    def setTime1(self, t1):
        self.t1 = t1

    def getTime2(self):
        return self.t2

    def setTime2(self, t2):
        self.t2 = t2

    def getARdetStep(self):
        return self.ARdetStep

    def setARdetStep(self, t1):
        if t1:
            self.ARdetStep = []
            self.ARdetStep.append(t1 / 4)
            self.ARdetStep.append(int(np.ceil(self.getTime2() / self.getIncrement()) / 4))

    def getOrder(self):
        return self.order

    def setOrder(self, order):
        self.order = order

    def getIncrement(self):
        """
        :rtype : int
        """
        return self.dt

    def getTimeArray(self):
        incr = self.getIncrement()
        self.TimeArray = np.arange(0, len(self.getCF()) * incr, incr) + self.getCut()[0]
        return self.TimeArray

    def getFnoise(self):
        return self.fnoise

    def setFnoise(self, fnoise):
        self.fnoise = fnoise

    def getCF(self):
        return self.cf

    def getXCF(self):
        return self.xcf

    def _getStealthMode(self):
        return self._stealthMode

    def getDataArray(self, cut=None):
        '''
        If cut times are given, time series is cut from cut[0] (start time)
        till cut[1] (stop time) in order to calculate CF for certain part
        only where you expect the signal!
        input: cut (tuple) ()
        cutting window
        '''
        if cut is not None:
            if len(self.orig_data) == 1:
                if self.cut[0] == 0 and self.cut[1] == 0:
                    start = 0
                    stop = len(self.orig_data[0])
                elif self.cut[0] == 0 and self.cut[1] is not 0:
                    start = 0
                    stop = self.cut[1] / self.dt
                else:
                    start = self.cut[0] / self.dt
                    stop = self.cut[1] / self.dt
                zz = self.orig_data.copy()
                z1 = zz[0].copy()
                zz[0].data = z1.data[int(start):int(stop)]
                data = zz
                return data
            elif len(self.orig_data) == 2:
                if self.cut[0] == 0 and self.cut[1] == 0:
                    start = 0
                    stop = min([len(self.orig_data[0]), len(self.orig_data[1])])
                elif self.cut[0] == 0 and self.cut[1] is not 0:
                    start = 0
                    stop = min([self.cut[1] / self.dt, len(self.orig_data[0]),
                                len(self.orig_data[1])])
                else:
                    start = max([0, self.cut[0] / self.dt])
                    stop = min([self.cut[1] / self.dt, len(self.orig_data[0]),
                                len(self.orig_data[1])])
                hh = self.orig_data.copy()
                h1 = hh[0].copy()
                h2 = hh[1].copy()
                hh[0].data = h1.data[int(start):int(stop)]
                hh[1].data = h2.data[int(start):int(stop)]
                data = hh
                return data
            elif len(self.orig_data) == 3:
                if self.cut[0] == 0 and self.cut[1] == 0:
                    start = 0
                    stop = min([self.cut[1] / self.dt, len(self.orig_data[0]),
                                len(self.orig_data[1]), len(self.orig_data[2])])
                elif self.cut[0] == 0 and self.cut[1] is not 0:
                    start = 0
                    stop = self.cut[1] / self.dt
                else:
                    start = max([0, self.cut[0] / self.dt])
                    stop = min([self.cut[1] / self.dt, len(self.orig_data[0]),
                                len(self.orig_data[1]), len(self.orig_data[2])])
                hh = self.orig_data.copy()
                h1 = hh[0].copy()
                h2 = hh[1].copy()
                h3 = hh[2].copy()
                hh[0].data = h1.data[int(start):int(stop)]
                hh[1].data = h2.data[int(start):int(stop)]
                hh[2].data = h3.data[int(start):int(stop)]
                data = hh
                return data
        else:
            data = self.orig_data.copy()
            return data

    def calcCF(self, data=None):
        self.cf = data


class AICcf(CharacteristicFunction):
    '''
    Function to calculate the Akaike Information Criterion (AIC) after
    Maeda (1985).
    :param: data, time series (whether seismogram or CF)
    :type: tuple

    Output: AIC function
    '''

    def calcCF(self, data):

        # if self._getStealthMode() is False:
        #    print 'Calculating AIC ...'
        x = self.getDataArray()
        xnp = x[0].data
        nn = np.isnan(xnp)
        if len(nn) > 1:
            xnp[nn] = 0
        datlen = len(xnp)
        k = np.arange(1, datlen)
        cf = np.zeros(datlen)
        cumsumcf = np.cumsum(np.power(xnp, 2))
        i = np.where(cumsumcf == 0)
        cumsumcf[i] = np.finfo(np.float64).eps
        cf[k] = ((k - 1) * np.log(cumsumcf[k] / k) + (datlen - k + 1) *
                 np.log((cumsumcf[datlen - 1] - cumsumcf[k - 1]) / (datlen - k + 1)))
        cf[0] = cf[1]
        inf = np.isinf(cf)
        ff = np.where(inf == True)
        if len(ff) >= 1:
            cf[ff] = 0

        self.cf = cf - np.mean(cf)
        self.xcf = x


class HOScf(CharacteristicFunction):
    '''
    Function to calculate skewness (statistics of order 3) or kurtosis
    (statistics of order 4), using one long moving window, as published
    in Kueperkoch et al. (2010).
    '''

    def calcCF(self, data):

        x = self.getDataArray(self.getCut())
        xnp = x[0].data
        nn = np.isnan(xnp)
        if len(nn) > 1:
            xnp[nn] = 0
        if self.getOrder() == 3:  # this is skewness
            # if self._getStealthMode() is False:
            #    print 'Calculating skewness ...'
            y = np.power(xnp, 3)
            y1 = np.power(xnp, 2)
        elif self.getOrder() == 4:  # this is kurtosis
            # if self._getStealthMode() is False:
            #    print 'Calculating kurtosis ...'
            y = np.power(xnp, 4)
            y1 = np.power(xnp, 2)

        # Initialisation
        # t2: long term moving window
        ilta = int(round(self.getTime2() / self.getIncrement()))
        lta = y[0]
        lta1 = y1[0]
        # moving windows
        LTA = np.zeros(len(xnp))
        for j in range(0, len(xnp)):
            if j < 4:
                LTA[j] = 0
            elif j <= ilta:
                lta = (y[j] + lta * (j - 1)) / j
                lta1 = (y1[j] + lta1 * (j - 1)) / j
            else:
                lta = (y[j] - y[j - ilta]) / ilta + lta
                lta1 = (y1[j] - y1[j - ilta]) / ilta + lta1
            # define LTA
            if self.getOrder() == 3:
                LTA[j] = lta / np.power(lta1, 1.5)
            elif self.getOrder() == 4:
                LTA[j] = lta / np.power(lta1, 2)

        nn = np.isnan(LTA)
        if len(nn) > 1:
            LTA[nn] = 0
        self.cf = LTA
        self.xcf = x
