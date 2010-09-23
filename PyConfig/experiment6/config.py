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

import random
import math

from openwns.wrowser.simdb.SimConfig import params

random.seed(params.Seed)
###################################
## Change basic configuration here:
###################################
class Configuration:
    maxSimTime = params.simTime
    ## must be < 250 (otherwise IPAddress out of range)
    numberOfLinkspWPAN = params.numberOfLinkspWPAN
    numberOfStations = params.numberOfLinkspWPAN*2*5
    ## Throughput per station
    throughputPerStation = params.offeredLoadpLink
    ## Packet size for constant bit rate
    fixedPacketSize = 1480 * 8
    ## Channel Model
    CM = 2
    ## Default PhyMode
    defPhyMode = 7
    
    ## Signal frequency
    initFrequency = 3960
    ## Offset for SINR
    postSINRFactor = dB(0.0)

    maxPER = 0.03
    isDroppingAfterRetr = -1
    ## Uses Multiple hops to reach target
    isForwarding = False

    ## Relinquish Request
    useRelinquishRequest = False
    ## Number of TXOPs to be created
    reservationBlocks = 1
    deleteQueues = True
    
    #########################
    ## Implementation methods
    print "Implementation method is : " , params.method
    if params.method == '1RateAdaptationOFF':
        useLinkEstimation = False
        ## Is Rate Adaption Used
        useRateAdaptation = False
        useRandomPattern = True
        ## Interference Optimization
        interferenceAwareness = False
        useMultipleStreams = False
    if params.method == '2Random-MAS':
        useLinkEstimation = False
        ## Is Rate Adaptation Used
        useRateAdaptation = True
        useRandomPattern = True
        ## Interference Optimization
        interferenceAwareness = False
        useMultipleStreams = False
    if params.method == '3Blocked-MAS':
        useLinkEstimation = False
        ## Is Rate Adaptation Used
        useRateAdaptation = True
        useRandomPattern = False
        ## Interference Optimization
        interferenceAwareness = False
        useMultipleStreams = False
    if params.method == '4IA-Random-MAS':
        useLinkEstimation = True
        ## Is Rate Adaptation Used
        useRateAdaptation = True
        useRandomPattern = True
        ## Interference Optimization
        interferenceAwareness = True
        useMultipleStreams = True
    if params.method == '5IA-Blocked-MAS':
        useLinkEstimation = True
        ## Is Rate Adaptation Used
        useRateAdaptation = True
        useRandomPattern = False
        ## Interference Optimization
        interferenceAwareness = True
        useMultipleStreams = True
    else:
        assert params.method in ('1RateAdaptationOFF','2Random-MAS','3Blocked-MAS','4IA-Random-MAS','5IA-Blocked-MAS')
    
    ## Szenario size
    wpansize = 5 # Area is A x A
    wpanseparation = 1
    
    maxLinkDistance = params.maxLinkDistance
    
    sizeX = 3*wpansize + 2*wpanseparation
    sizeY = 3*wpansize + 2*wpanseparation
  
    ## Configure Probes
    settlingTimeGuard = 10.0
    createThroughputProbe = True
    createDelayProbe = True
    createChannelUsageProbe = True
    createMCSProbe = False
    createPERProbe = False

    createTimeseriesProbes = False
    createSNRProbes = False
    useDLRE = False
  
    commonLoggerLevel = 1
    dllLoggerLevel = 2

    useDRPchannelAccess = True
    usePCAchannelAccess = False
    
configuration = Configuration()

## scenario setup
scenario = rise.Scenario.Scenario()

objs = []
## e.g. single wall
objs.append(rise.scenario.Shadowing.LineSegment(openwns.geometry.Position(configuration.wpansize + configuration.wpanseparation / 2.0, 0.0, 0.0), 
                                            openwns.geometry.Position(configuration.wpansize + configuration.wpanseparation / 2.0, configuration.sizeY, 0.0), 
                                            attenuation = dB(params.wallAtt) ))
objs.append(rise.scenario.Shadowing.LineSegment(openwns.geometry.Position(configuration.wpansize*2 + configuration.wpanseparation *3.0 / 2.0, 0.0, 0.0), 
                                            openwns.geometry.Position(configuration.wpansize*2 + configuration.wpanseparation *3.0 / 2.0, configuration.sizeY, 0.0), 
                                            attenuation = dB(params.wallAtt) ))
                                            
objs.append(rise.scenario.Shadowing.LineSegment(openwns.geometry.Position(0.0, configuration.wpansize + configuration.wpanseparation / 2.0, 0.0), 
                                            openwns.geometry.Position(configuration.sizeX, configuration.wpansize + configuration.wpanseparation / 2.0, 0.0), 
                                            attenuation = dB(params.wallAtt) ))
objs.append(rise.scenario.Shadowing.LineSegment(openwns.geometry.Position(0.0, configuration.wpansize*2 + configuration.wpanseparation *3.0 / 2.0, 0.0), 
                                            openwns.geometry.Position(configuration.sizeX, configuration.wpansize*2 + configuration.wpanseparation *3.0 / 2.0, 0.0), 
                                            attenuation = dB(params.wallAtt) ))

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

###########################################################################################
## Configure Stations Positions & Links
###########################################################################################
class TrafficEstConfig:
    MaxCompoundSize = configuration.fixedPacketSize + 20
    CompoundspSF = math.ceil(configuration.throughputPerStation / (configuration.fixedPacketSize) * 0.065536)
    BitspSF = CompoundspSF * MaxCompoundSize
    overWriteEstimation = False

######################################
##Configure multi frequency devices
######################################
class ChannelUnits:
    Frequency = None
    BeaconSlot = None

ChannelManagerPerStation= []

for k in range(configuration.numberOfStations):
    ChannelManagers = []
    for i in range(1):
        channelunits = ChannelUnits()
        channelunits.Frequency = 3100
        channelunits.BeaconSlot = k+1
        ChannelManagers.append(channelunits)
    ChannelManagerPerStation.append(ChannelManagers)
    
    
wpanXorigins = [ (configuration.wpansize + configuration.wpanseparation), (0.0), (configuration.wpansize + configuration.wpanseparation)*2, (configuration.wpansize + configuration.wpanseparation), (configuration.wpansize + configuration.wpanseparation)]
wpanYorigins = [ (configuration.wpansize + configuration.wpanseparation), (configuration.wpansize + configuration.wpanseparation), (configuration.wpansize + configuration.wpanseparation), (configuration.wpansize + configuration.wpanseparation)*2, (0.0)]

transmitterPos = open("transmitterPos", "w")
receiverPos = open("receiverPos", "w")

## create Stations   
for wpan in (0,1,2,3,4):
    ## For each WPAN
    #wpanorigin = (configuration.wpansize + configuration.wpanseparation) * wpan
    wpanXorigin = wpanXorigins[wpan]
    wpanYorigin = wpanYorigins[wpan]

    for link in xrange (0, configuration.numberOfLinkspWPAN):
        ## For each link that is to be created
        
        ## Create Transmitter
        ## randomly choose a position
        transmitterXCoord = random.uniform(0, configuration.wpansize)
        transmitterXCoord = wpanXorigin + round(transmitterXCoord, 2)
        transmitterYCoord = random.uniform(0, configuration.wpansize)
        transmitterYCoord = wpanYorigin + round(transmitterYCoord, 2)

        
        staConfig = wimemac.support.NodeCreator.STAConfig(
                            initFrequency = configuration.initFrequency,
                            position = openwns.geometry.position.Position(transmitterXCoord, transmitterYCoord ,0),
                            channelModel = configuration.CM,
                            numberOfStations = configuration.numberOfStations,
                            useInterferenceAwareness = configuration.useInterferenceAwareness,
                            useLinkEstimation = configuration.useLinkEstimation,
                            channelManagers = ChannelManagerPerStation[len(WNS.simulationModel.nodes)-1],
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
                            isDroppingAfterRetr = configuration.isDroppingAfterRetr,
                            deleteQueues = configuration.deleteQueues,
                            overWriteEstimation = TrafficEstConfig.overWriteEstimation,
                            CompoundspSF = TrafficEstConfig.CompoundspSF,
                            BitspSF = TrafficEstConfig.BitspSF,
                            MaxCompoundSize = TrafficEstConfig.MaxCompoundSize)

        transmitter = nc.createSTA(idGen,
                               config = staConfig,
                               loggerLevel = configuration.commonLoggerLevel,
                               dllLoggerLevel = configuration.dllLoggerLevel)
        print "Created Transmitter with ID : " , (wpan*configuration.numberOfLinkspWPAN*2 + link*2 +1) ," at X: " , transmitterXCoord , " ,Y: " , transmitterYCoord
        transmitterPos.write('ID : ' + str(wpan*configuration.numberOfLinkspWPAN*2 + link*2 +1) 
            + ' at X: [' + str(transmitterXCoord) + '] , Y: [' + str(transmitterYCoord) + '] \n')
                               
        ## Create Receiver
        receiverfound = False
        while (receiverfound == False):
            ## randomly choose a position that is no farther away from the transmitter than maxLinkDistance
            distance = random.uniform(0.01, configuration.maxLinkDistance)
            distance = round(distance, 2)            
            radius = random.randrange(0, 360, 1)
            receiverXCoord = transmitterXCoord + distance * math.cos(math.radians(radius))
            receiverXCoord = round(receiverXCoord, 2)
            receiverYCoord = transmitterYCoord + distance * math.sin(math.radians(radius))
            receiverYCoord = round(receiverYCoord, 2)
           
            if ((wpanYorigin <= receiverYCoord) and (receiverYCoord <= (wpanYorigin + configuration.wpansize))):
                if ((wpanXorigin <= receiverXCoord) and (receiverXCoord <= (wpanXorigin + configuration.wpansize))):
                    ## The position needs to be within the scenario boundary
                    receiverfound = True
                else:
                    print "WPAN" , wpan+1, " : X Coordinate is out of boundaries! It is : " , receiverXCoord
            else:
                print "WPAN" , wpan+1, " : Y Coordinate is out of boundaries! It is : " , receiverYCoord
                    
        staConfig = wimemac.support.NodeCreator.STAConfig(
                            initFrequency = configuration.initFrequency,
                            position = openwns.geometry.position.Position(receiverXCoord, receiverYCoord ,0),
                            channelModel = configuration.CM,
                            numberOfStations = configuration.numberOfStations,
                            useInterferenceAwareness = configuration.useInterferenceAwareness,
                            useLinkEstimation = configuration.useLinkEstimation,
                            channelManagers = ChannelManagerPerStation[len(WNS.simulationModel.nodes)],
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
                            isDroppingAfterRetr = configuration.isDroppingAfterRetr,
                            deleteQueues = configuration.deleteQueues,
                            overWriteEstimation = TrafficEstConfig.overWriteEstimation,
                            CompoundspSF = TrafficEstConfig.CompoundspSF,
                            BitspSF = TrafficEstConfig.BitspSF,
                            MaxCompoundSize = TrafficEstConfig.MaxCompoundSize)

        receiver = nc.createSTA(idGen,
                               config = staConfig,
                               loggerLevel = configuration.commonLoggerLevel,
                               dllLoggerLevel = configuration.dllLoggerLevel)
           
        print "Created Receiver with ID : " , (wpan*configuration.numberOfLinkspWPAN*2 + (link+1)*2) ," at X: " , receiverXCoord , " ,Y: " , receiverYCoord   
        receiverPos.write('ID : ' + str(wpan*configuration.numberOfLinkspWPAN*2 + (link+1)*2) 
            + ' at X: [' + str(receiverXCoord) + '] , Y: [' + str(receiverYCoord) + '] \n')
        
        
        ## Create Bindings
        ipListenerBinding = constanze.Node.IPListenerBinding(transmitter.nl.domainName)
        listener = constanze.Node.Listener(transmitter.nl.domainName + ".listener")
        transmitter.load.addListener(ipListenerBinding, listener)
        WNS.simulationModel.nodes.append(transmitter)
        
        ipListenerBinding = constanze.Node.IPListenerBinding(receiver.nl.domainName)
        listener = constanze.Node.Listener(receiver.nl.domainName + ".listener")
        receiver.load.addListener(ipListenerBinding, listener)
        WNS.simulationModel.nodes.append(receiver)
        
        ## Create Link
        transmissionStart = random.randrange(10,4000, 10) ## Time at which the transmission starts in ms
        
        cbr = constanze.Constanze.CBR(transmissionStart/1000.0, configuration.throughputPerStation, configuration.fixedPacketSize)
        ipBinding = constanze.Node.IPBinding(transmitter.nl.domainName, receiver.nl.domainName)
        transmitter.load.addTraffic(ipBinding, cbr)


transmitterPos.close()
receiverPos.close()

###########################################################################################
## End Configure Stations
###########################################################################################

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

