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

from SimConfig import params
###################################
## Change basic configuration here:
###################################
# begin example "wimemac.tutorial.experiment1.config.simulationParameter"
class Configuration:
    maxSimTime = params.simTime
    ## must be < 250 (otherwise IPAddress out of range)
    numberOfStations = 2
    ## Throughput per station
    throughputPerStation = params.throughputPerStation
    ## Packet size for constant bit rate
    fixedPacketSize = 1480 * 8
    ## Channel Model
    CM = 2
    ## Default PhyMode
    defPhyMode = 7
# end example
    
    ## Signal frequency
    initFrequency = 3960
    ## Offset for SINR
    postSINRFactor = dB(5.0)
    ## Is Rate Adaption Used
    useRateAdaption = True
    ## Uses Multiple hops to reach target
    isForwarding = False
    

    ## Interference Optimization
    interferenceAwareness = False
    useMultipleStreams = False
    ##
    
    ##Relinquish Request
    patternAdaption = False
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
#myShadowing = rise.scenario.Shadowing.No()
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

#len(posList)+1, commonLoggerLevel)) 
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

#cbr = constanze.Constanze.CBR(configuration.maxSimTime/2, configuration.throughputPerStation, configuration.fixedPacketSize)
#ipBinding = constanze.Node.IPBinding(WNS.simulationModel.nodes[2].nl.domainName, WNS.simulationModel.nodes[3].nl.domainName)
#WNS.simulationModel.nodes[2].load.addTraffic(ipBinding, cbr)

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

#ip.evaluation.default.installEvaluation(sim = WNS,
#                                        maxPacketDelay = 0.5,     # s
#                                        maxPacketSize = 2000*8,   # Bit
#                                        maxBitThroughput = 10E6,  # Bit/s
#                                        maxPacketThroughput = 1E6 # Packets/s
#                                        )

#constanze.evaluation.default.installEvaluation(sim = WNS,
#                                               maxPacketDelay = 1.0,
#                                               maxPacketSize = 16000,
#                                               maxBitThroughput = 100e6,
#                                               maxPacketThroughput = 10e6,
#                                               delayResolution = 1000,
#                                               sizeResolution = 2000,
#                                               throughputResolution = 10000)

## Enable Warp2Gui output
#node = openwns.evaluation.createSourceNode(WNS, "wimemac.guiProbe")
#node.appendChildren(openwns.evaluation.generators.TextTrace("wimemac.guiText", ""))

###################################
## Configure probes
###################################


openwns.setSimulator(WNS)

