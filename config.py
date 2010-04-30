import openwns
import openwns.evaluation
import openwns.evaluation.default
from openwns.interval import Interval

import constanze.Constanze
import constanze.Node
import constanze.evaluation.default
import ip.Component

import ip
from ip.VirtualARP import VirtualARPServer
from ip.VirtualDHCP import VirtualDHCPServer
from ip.VirtualDNS import VirtualDNSServer
import ip.evaluation.default

import wimemac.support.Configuration
import wimemac.evaluation.wimemacProbes
import wimemac.evaluation.constanzeProbes

from openwns import dBm, dB

import rise.Scenario
import rise.scenario.FastFading
import rise.scenario.Propagation
import rise.scenario.Shadowing
import rise.scenario.Pathloss

import ofdmaphy.OFDMAPhy

###################################
## Change basic configuration here:
###################################
class Configuration:
    maxSimTime = 3.0
    ## must be < 250 (otherwise IPAddress out of range)
    numberOfStations = 3
    ## Throughput per station
    throughputPerStation = 105E6
    ## Packet size for constant bit rate
    fixedPacketSize = 1480 * 8
    ## Channel Model
    CM = 2
    ## Default PhyMode
    defPhyMode = 7
    
    ## Signal frequency
    initFrequency = 3960
    ## Offset for SINR
    postSINRFactor = dB(5.0)
    ## Is Rate Adaption Used
    useRateAdaption = True
    ## Uses Multiple hops to reach target
    isForwarding = False
    

    ## Interference Optimization
    interferenceAwareness = True
    useMultipleStreams = False
    ##
    
    ##Relinquish Request
    patternAdaption = True
    ##
    reservationBlocks = 2
    ##Distance between two reservation blocks
    ReservationGap = 2
        
    ## Szenario size
    sizeX = 50
    sizeY = 10  
  
    ## TimeSettling for probes
    settlingTimeGuard = 0.0
    ## Create Timeseries probes
    createTimeseriesProbes = False
    createSNRProbes = False
  
    commonLoggerLevel = 1
    dllLoggerLevel = 2

configuration = Configuration()

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
    minPathloss = dB(42), # pathloss at 1m distance
    outOfMinRange = rise.scenario.Pathloss.Constant("42 dB"),
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


WNS.simulationModel.nodes.append(nc.createVPS(configuration.numberOfStations+1, 1))

###################################
## Configure Stations Positions & Links
###################################

for i in range(configuration.numberOfStations):
    xCoord = i
    staConfig = wimemac.support.NodeCreator.STAConfig(
                        initFrequency = configuration.initFrequency,
                        position = openwns.geometry.Position(xCoord, configuration.sizeY / 2 ,0),
                        channelModel = configuration.CM,
                        numberOfStations = configuration.numberOfStations,
                        patternAdaption = configuration.patternAdaption,
                        reservationBlocks = configuration.reservationBlocks,
                        interferenceAwareness = configuration.interferenceAwareness,
                        useRateAdaption = configuration.useRateAdaption,
                        useMultipleStreams = configuration.useMultipleStreams,
                        isForwarding = configuration.isForwarding,
                        postSINRFactor = configuration.postSINRFactor,
                        defPhyMode = configuration.defPhyMode)

    station = nc.createSTA(idGen,
                      config = staConfig,
                      ReservationGap = configuration.ReservationGap,
                      loggerLevel = configuration.commonLoggerLevel,
                      dllLoggerLevel = configuration.dllLoggerLevel)
    WNS.simulationModel.nodes.append(station)

for i in range(1,configuration.numberOfStations+1):
    ipListenerBinding = constanze.Node.IPListenerBinding(WNS.simulationModel.nodes[i].nl.domainName)
    listener = constanze.Node.Listener(WNS.simulationModel.nodes[i].nl.domainName + ".listener")
    WNS.simulationModel.nodes[i].load.addListener(ipListenerBinding, listener)

cbr = constanze.Constanze.CBR(0.01, configuration.throughputPerStation, configuration.fixedPacketSize)
ipBinding = constanze.Node.IPBinding(WNS.simulationModel.nodes[1].nl.domainName, WNS.simulationModel.nodes[2].nl.domainName)
WNS.simulationModel.nodes[1].load.addTraffic(ipBinding, cbr)
cbr = constanze.Constanze.CBR(1.01, configuration.throughputPerStation, configuration.fixedPacketSize)
ipBinding = constanze.Node.IPBinding(WNS.simulationModel.nodes[1].nl.domainName, WNS.simulationModel.nodes[3].nl.domainName)
WNS.simulationModel.nodes[1].load.addTraffic(ipBinding, cbr)


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

wimemac.evaluation.wimemacProbes.installEvaluation(WNS, range(2, configuration.numberOfStations +2), configuration) # Begin with id2 because of the VPS
wimemac.evaluation.constanzeProbes.installEvaluation(WNS, range(2, configuration.numberOfStations +2), configuration)


###################################
## Configure probes
###################################


openwns.setSimulator(WNS)

