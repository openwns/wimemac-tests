#! /usr/bin/python
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

# this is needed, so that the script can be called from everywhere
import os
import sys
base, tail = os.path.split(sys.argv[0])
os.chdir(base)

# Append the python sub-dir of WNS--main--x.y ...
sys.path.append(os.path.join('..', '..', '..', 'sandbox', 'default', 'lib', 'python2.4', 'site-packages'))

# ... because the module WNS unit test framework is located there.
import pywns.WNSUnit

testSuite = pywns.WNSUnit.TestSuite()

# create a system test
testSuite.addTest(pywns.WNSUnit.ProbesTestSuite(sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                                
                                                configFile = 'config.py',
                                                runSimulations = True,
						                        requireReferenceOutput = False,
                                                shortDescription = 'Basic WiMeMAC Test',
                                                disabled = False,
                                                disabledReason = ""))
                                                
testSuite.addTest(pywns.WNSUnit.ProbesTestSuite(sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                                configFile = 'config.py',
                                                runSimulations = True,
                                                shortDescription = 'WiMeMAC-Tutorial: Experiment 1',
                                                requireReferenceOutput = False,
                                                disabled = False,
                                                disabledReason = "",
                                                workingDir = "PyConfig/experiment1"))
                                                
testSuite.addTest(pywns.WNSUnit.ProbesTestSuite(sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                                configFile = 'config.py',
                                                runSimulations = True,
                                                shortDescription = 'WiMeMAC-Tutorial: Experiment 2',
                                                requireReferenceOutput = False,
                                                disabled = False,
                                                disabledReason = "",
                                                workingDir = "PyConfig/experiment2"))
                                                
testSuite.addTest(pywns.WNSUnit.ProbesTestSuite(sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                                configFile = 'config.py',
                                                runSimulations = True,
                                                shortDescription = 'WiMeMAC-Tutorial: Experiment 3',
                                                requireReferenceOutput = False,
                                                disabled = False,
                                                disabledReason = "",
                                                workingDir = "PyConfig/experiment3"))
                                                
testSuite.addTest(pywns.WNSUnit.ProbesTestSuite(sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                                configFile = 'config.py',
                                                runSimulations = True,
                                                shortDescription = 'WiMeMAC-Tutorial: Experiment 4',
                                                requireReferenceOutput = False,
                                                disabled = False,
                                                disabledReason = "",
                                                workingDir = "PyConfig/experiment4"))
                                                

if __name__ == '__main__':
    # This is only evaluated if the script is called by hand

    # if you need to change the verbosity do it here
    verbosity = 2

    pywns.WNSUnit.verbosity = verbosity

    # Create test runner
    testRunner = pywns.WNSUnit.TextTestRunner(verbosity=verbosity)

    # Finally, run the tests.
    testRunner.run(testSuite)
