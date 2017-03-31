#!/usr/bin/env python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
#   Copyright 2017 Marcel Paffrath (Ruhr-Universitaet Bochum, Germany)
#
#   This file is part of ActiveSeismoPick3D
#----------------------------------------------------------------------------

import matplotlib.pyplot as plt
infile = open('residuals.dat','r')
list = infile.readlines()

RMS = []; var = []; chi2 = []

for line in list:
    RMS.append(line.split()[0])
    var.append((line.split()[1]))
    chi2.append(line.split()[2])

fig, ax1 = plt.subplots()

ax1.plot(RMS, label = 'RMS', color = 'm')
ax1.plot(chi2, label = r'$\chi^2$', color = 'b')
ax1.plot(var, label = 'Var', color = 'r')
ax1.hlines(1, ax1.get_xlim()[0], ax1.get_xlim()[1], linestyles = 'dashed', label = '1')
ax1.set_xlabel('Iteration step')
ax1.set_yscale('log')
ax1.grid(True, 'major', linestyle = '-')
ax1.grid(True, 'minor', linestyle = '-', color = '0.5')

plt.legend()
plt.show()
