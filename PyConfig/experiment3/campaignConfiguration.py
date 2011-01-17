###############################################################################
# This file is part of openWNS (open Wireless Network Simulator)
# _____________________________________________________________________________
#
# Copyright (C) 2004-2011
# Chair of Communication Networks (ComNets)
# Kopernikusstr. 5, D-52074 Aachen, Germany
# phone: ++49-241-80-27910,
# fax: ++49-241-80-22242
# email: info@openwns.org
# www: http://www.openwns.org
# _____________________________________________________________________________
#
# openWNS is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License version 2 as published by the
# Free Software Foundation;
#
# openWNS is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import sys
import os

def searchPathToSDK(path):
    rootSign = ".thisIsTheRootOfWNS"
    while rootSign not in os.listdir(path):
        if path == os.sep:
            # arrived in root dir
            return None
        path, tail = os.path.split(path)
    return os.path.abspath(path)

pathToSDK = searchPathToSDK(os.path.abspath(os.path.dirname(sys.argv[0])))

if pathToSDK == None:
    print "Error! You are note within an openWNS-SDK. Giving up"
    exit(1)

sys.path.append(os.path.join(pathToSDK, "sandbox", "default", "lib", "python2.4", "site-packages"))

from openwns.wrowser.simdb.Parameters import Parameters, Bool, Int, Float, String


class Set(Parameters):
    simTime = Float()
    throughputPerStation = Int()
    reservationBlocks = Int()

# begin example "wimemac.tutorial.experiment3.campaignConfiguration.initialization"
params = Set()

params.simTime = 10.0
params.throughputPerStation = 40E6

for i in xrange(1,7):
    params.reservationBlocks = 2*i
    params.write()
# end example
