
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
import wimemac.evaluation.finalEvalProbes

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
    maxSimTime = 2.0
    ## must be < 250 (otherwise IPAddress out of range)
    numberOfStations = 3
    ## Throughput per station
    throughputPerStation = 50E6
    ## Packet size for constant bit rate
    fixedPacketSize = 1480 * 8
    ## Channel Model
    CM = 2
    ## Default PhyMode
    defPhyMode = 4
    
    ## Signal frequency
    initFrequency = 3960
    ## Offset for SINR
    postSINRFactor = dB(0.0)
   
    ## Uses Multiple hops to reach target
    isForwarding = False

    # max allowed PER and additional offset for drp pattern
    maxPER = 0.03
    PEROffset = 0.00
    # drops unacknowledged packets after x retransmissions
    isDroppingAfterRetr = -1
    
    ## Relinquish Request
    useRelinquishRequest = False
    ## Number of TXOPs to be created
    reservationBlocks = 1
    
    ## Szenario size
    sizeX = 50
    sizeY = 10  
  
    commonLoggerLevel = 1
    dllLoggerLevel = 2


    ## TimeSettling for probes
    settlingTimeGuard = 3.0
    ## Create Timeseries probes
    createTimeseriesProbes = False
    createSNRProbes = False

    # Used implementation method

    method = '3Blocked-MAS'
    #method = '1RateAdaptationOFF'
    
    useDRPchannelAccess = True
    usePCAchannelAccess = True

    #########################
    ## Implementation methods
    print "Implementation method is : " , method
    if method == '1RateAdaptationOFF':
        ## Is Rate Adaption Used
        useRateAdaptation = False
        useRandomPattern = True
        ## Interference Optimization
        interferenceAwareness = False
        useMultipleStreams = False
    if method == '2Random-MAS':
        ## Is Rate Adaption Used
        useRateAdaptation = True
        useRandomPattern = True
        ## Interference Optimization
        interferenceAwareness = False
        useMultipleStreams = False
    if method == '3Blocked-MAS':
        ## Is Rate Adaption Used
        useRateAdaptation = True
        useRandomPattern = False
        ## Interference Optimization
        interferenceAwareness = False
        useMultipleStreams = False
    if method == '4IA-Random-MAS':
        ## Is Rate Adaption Used
        useRateAdaptation = True
        useRandomPattern = True
        ## Interference Optimization
        interferenceAwareness = True
        useMultipleStreams = True
    if method == '5IA-Blocked-MAS':
        ## Is Rate Adaption Used
        useRateAdaptation = True
        useRandomPattern = False
        ## Interference Optimization
        interferenceAwareness = True
        useMultipleStreams = True
    else:
        assert method in ('1RateAdaptationOFF','2Random-MAS','3Blocked-MAS','4IA-Random-MAS','5IA-Blocked-MAS')

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

#len(posList)+1, commonLoggerLevel)) 
WNS.simulationModel.nodes.append(nc.createVPS(configuration.numberOfStations+1, 1))

#######################################
## Configure Stations Positions & Links
#######################################

for i in range(configuration.numberOfStations):
    xCoord = i*1
    staConfig = wimemac.support.NodeCreator.STAConfig(
                        initFrequency = configuration.initFrequency,
                        position = openwns.geometry.position.Position(xCoord, configuration.sizeY / 2 ,0),
                        channelModel = configuration.CM,
                        numberOfStations = configuration.numberOfStations,
                        interferenceAwareness = configuration.interferenceAwareness,
                        useRandomPattern = configuration.useRandomPattern,
                        useRateAdaptation = configuration.useRateAdaptation,
                        useMultipleStreams = configuration.useMultipleStreams,
                        useRelinquishRequest = configuration.useRelinquishRequest,
                        useDRPchannelAccess = configuration.useDRPchannelAccess,
                        usePCAchannelAccess = configuration.usePCAchannelAccess,
                        isForwarding = configuration.isForwarding,
                        postSINRFactor = configuration.postSINRFactor,
                        reservationBlocks = configuration.reservationBlocks,
                        defPhyMode = configuration.defPhyMode,
                        maxPER = configuration.maxPER,
                        patternPEROffset = configuration.PEROffset,
                        isDroppingAfterRetr = configuration.isDroppingAfterRetr)

    station = nc.createSTA(idGen,
                      config = staConfig,
                      loggerLevel = configuration.commonLoggerLevel,
                      dllLoggerLevel = configuration.dllLoggerLevel)
    WNS.simulationModel.nodes.append(station)

for i in range(1,configuration.numberOfStations+1):
    ipListenerBinding = constanze.Node.IPListenerBinding(WNS.simulationModel.nodes[i].nl.domainName)
    listener = constanze.Node.Listener(WNS.simulationModel.nodes[i].nl.domainName + ".listener")
    WNS.simulationModel.nodes[i].load.addListener(ipListenerBinding, listener)

#cbr = constanze.Constanze.CBR(0.01, configuration.throughputPerStation, configuration.fixedPacketSize)
cbr = constanze.traffic.Poisson(offset = 0.01, throughput = configuration.throughputPerStation, packetSize = configuration.fixedPacketSize)
ipBinding = constanze.Node.IPBinding(WNS.simulationModel.nodes[1].nl.domainName, WNS.simulationModel.nodes[2].nl.domainName)
WNS.simulationModel.nodes[1].load.addTraffic(ipBinding, cbr)


#cbr = constanze.Constanze.CBR(1.01, configuration.throughputPerStation, configuration.fixedPacketSize)
cbr = constanze.traffic.Poisson(offset = 1.01, throughput = configuration.throughputPerStation, packetSize = configuration.fixedPacketSize)
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

#wimemac.evaluation.wimemacProbes.installEvaluation(WNS, range(2, configuration.numberOfStations +2), configuration) # Begin with id2 because of the VPS
wimemac.evaluation.constanzeProbes.installEvaluation(WNS, range(2, configuration.numberOfStations +2), configuration)
#wimemac.evaluation.finalEvalProbes.installEvaluation(WNS, range(2, configuration.numberOfStations +2), configuration)

## Enable Warp2Gui output
node = openwns.evaluation.createSourceNode(WNS, "wimemac.guiProbe")
node.appendChildren(openwns.evaluation.generators.TextTrace("wimemac.guiText", ""))

###################################
## Configure probes
###################################


openwns.setSimulator(WNS)

