#!/usr/bin/env python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
#   Copyright 2017 Marcel Paffrath (Ruhr-Universitaet Bochum, Germany)
#
#   This file is part of ActiveSeismoPick3D
#----------------------------------------------------------------------------

import matplotlib.pyplot as plt
mtfile = open('mtimes.dat','r')
otfile = open('otimes.dat','r')
mtimes = mtfile.readlines()
otimes = otfile.readlines()

otimes = otimes[1:]

res = []

for i in range(len(mtimes)):
    res.append(float(mtimes[i].split()[4]) - float(otimes[i].split()[4]))

plt.plot(res, '.')
plt.show()
