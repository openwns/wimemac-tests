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

import openwns
import openwns.evaluation
import openwns.evaluation.default
from openwns.interval import Interval

import constanze
import constanze.traffic
import constanze.node
import constanze.evaluation.default
import ip.Component

import ip
from ip.VirtualARP import VirtualARPServer
from ip.VirtualDHCP import VirtualDHCPServer
from ip.VirtualDNS import VirtualDNSServer
import ip.evaluation.default

import wimemac.support.Configuration
import wimemac.helper.Probes
import wimemac.evaluation.wimemacProbes
import wimemac.evaluation.constanzeProbes
import wimemac.evaluation.ip

import wimemac.lowerMAC

from openwns import dBm, dB

import rise.Scenario
import rise.scenario.FastFading
import rise.scenario.Propagation
import rise.scenario.Shadowing
import rise.scenario.Pathloss

import ofdmaphy.OFDMAPhy
import math


from openwns.wrowser.simdb.SimConfig import params

###################################
## Change basic configuration here:
###################################
# begin example "wimemac.tutorial.experiment2.config.simulationParameter"
class Configuration:
    maxSimTime = params.simTime
    ## must be < 250 (otherwise IPAddress out of range)
    numberOfStations = 2
    ## Throughput per station
    throughputPerStation = params.throughputPerStation
    ## Packet size for constant bit rate
    fixedPacketSize = 1480 * 8
    ## Default PhyMode
    defPhyMode = 7
# end example
    
    ## Signal frequency
    initFrequency = 3960

    # max allowed PER and additional offset for drp pattern
    maxPER = 0.03
    PEROffset = 0.00
    # drops unacknowledged packets after x retransmissions
    isDroppingAfterRetr = -1
    
    ## Number of TXOPs to be created
    reservationBlocks = 1
    deleteQueues = True
    
    ## Szenario size
    sizeX = 50
    sizeY = 10  
  
    commonLoggerLevel = 1
    dllLoggerLevel = 2


    ## Configure Probes
    settlingTimeGuard = 3.0

    createConstanzeProbes = True
    createChannelUsageProbe = True
    createMCSProbe = False
    createPERProbe = False

    createTimeseriesProbes = False
    createSNRProbes = False

    useDRPchannelAccess = True
    usePCAchannelAccess = False

    ## Is Rate Adaption Used
    useRateAdaptation = True
    ## Use Blocked MAS Reservation
    useRandomPattern = False



configuration = Configuration()

class STAConfig(wimemac.support.Transceiver.Station):
    def __init__(self, initFrequency, position):
        super(STAConfig, self).__init__(frequency = initFrequency, position = position)

        self.layer2.numberOfStations = configuration.numberOfStations
        managerConfig = wimemac.lowerMAC.ManagerConfig()
        managerConfig.useRandomPattern = configuration.useRandomPattern
        managerConfig.reservationBlocks = configuration.reservationBlocks
        managerConfig.useRateAdaptation = configuration.useRateAdaptation
        managerConfig.useDRPchannelAccess = configuration.useDRPchannelAccess
        managerConfig.usePCAchannelAccess = configuration.usePCAchannelAccess
        self.layer2.managerConfig = managerConfig
        
        self.layer2.defPhyMode = configuration.defPhyMode
        self.layer2.maxPER = configuration.maxPER
        self.layer2.patternPEROffset = configuration.PEROffset
        self.layer2.isDroppingAfterRetr = configuration.isDroppingAfterRetr
        self.layer2.deleteQueues = configuration.deleteQueues



## scenario setup
scenario = rise.Scenario.Scenario()

objs = []
## e.g. single wall
#objs.append(rise.scenario.Shadowing.LineSegment(openwns.geometry.Position(0.0, 1.0, 0.0),
#                                            openwns.geometry.Position(wallLength , 1.0, 0.0), 
#                                            attenuation = dB(100) ))

###################################
## End basic configuration
###################################


## create an instance of the WNS configuration
## The variable must be called WNS!!!!
WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE
WNS.maxSimTime = configuration.maxSimTime
                                             

## Radio channel propagation parameters
myPathloss = rise.scenario.Pathloss.PyFunction(
    validFrequencies = Interval(3100, 10600),
    validDistances = Interval(0.1, 100), #[m]
    offset = dB(-27.5522),
    freqFactor = 20,
    distFactor = 20,
    distanceUnit = "m", # only for the formula, not for validDistances
    minPathloss = dB(22.28), # pathloss at 1m distance
    outOfMinRange = rise.scenario.Pathloss.Constant("22.28 dB"),
    outOfMaxRange = rise.scenario.Pathloss.Deny(),
    scenarioWrap = False,
    sizeX = configuration.sizeX,
    sizeY = configuration.sizeY)
myShadowing = rise.scenario.Shadowing.Objects(obstructionList = objs)
myFastFading = rise.scenario.FastFading.No()
propagationConfig = rise.scenario.Propagation.Configuration(
    pathloss = myPathloss,
    shadowing = myShadowing,
    fastFading = myFastFading)
## End radio channel propagation parameters

## create an instance of the NodeCreator
nc = wimemac.support.NodeCreator.NodeCreator(propagationConfig)
idGen = wimemac.support.idGenerator()
ofdmaPhyConfig = WNS.modules.ofdmaPhy

## from ChannelManagerPool.py for 1 MeshChannel
managers = []
sys = ofdmaphy.OFDMAPhy.OFDMASystem('ofdma')
sys.Scenario = scenario
managers.append(sys)

ofdmaPhyConfig.systems.extend(managers)

#######################################
## Configure Stations Positions & Links
#######################################
    
for i in range(configuration.numberOfStations):

    xCoord = i
    staConfig = STAConfig(
                        initFrequency = configuration.initFrequency,
                        position = openwns.geometry.position.Position(xCoord, configuration.sizeY / 2 ,0))
    
    station = nc.createSTA(idGen,
                      config = staConfig,
                      loggerLevel = configuration.commonLoggerLevel,
                      dllLoggerLevel = configuration.dllLoggerLevel)
    WNS.simulationModel.nodes.append(station)

for i in range(configuration.numberOfStations):
    ipListenerBinding = constanze.node.IPListenerBinding(WNS.simulationModel.nodes[i].nl.domainName)
    listener = constanze.node.Listener(WNS.simulationModel.nodes[i].nl.domainName + ".listener")
    WNS.simulationModel.nodes[i].load.addListener(ipListenerBinding, listener)

cbr = constanze.traffic.CBR(0.01, configuration.throughputPerStation, configuration.fixedPacketSize)
ipBinding = constanze.node.IPBinding(WNS.simulationModel.nodes[0].nl.domainName, WNS.simulationModel.nodes[1].nl.domainName)
WNS.simulationModel.nodes[0].load.addTraffic(ipBinding, cbr)


###################################
## End Configure Stations
###################################

## one Virtual ARP Zone
varp = VirtualARPServer("vARP", "theOnlySubnet")
WNS.simulationModel.nodes = [varp] + WNS.simulationModel.nodes

vdhcp = VirtualDHCPServer("vDHCP@",
                          "theOnlySubnet",
                          "192.168.0.2", "192.168.254.253",
                          "255.255.0.0")

vdns = VirtualDNSServer("vDNS", "ip.DEFAULT.GLOBAL")
WNS.simulationModel.nodes.append(vdns)
WNS.simulationModel.nodes.append(vdhcp)

###################################
## Configure probes
###################################

wimemac.evaluation.wimemacProbes.installEvaluation(WNS, range(1, configuration.numberOfStations +1), configuration)
if configuration.createConstanzeProbes:
    wimemac.evaluation.constanzeProbes.installEvaluation(WNS, range(1, configuration.numberOfStations +1), configuration)


###################################
openwns.setSimulator(WNS)

