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

#from wrowser.simdb.SimConfig import params

random.seed(3.0)
###################################
## Change basic configuration here:
###################################
class Configuration:
    maxSimTime = 5.0
    ## must be < 250 (otherwise IPAddress out of range)
    numberOfLinkspWPAN = 5
    numberOfStations = 5*2*5
    ## Throughput per station
    throughputPerStation = 1E6
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

    method = '5IA-Blocked-MAS'


    #########################
    ## Implementation methods
    print "Implementation method is : " , method
    #if method == '1RateAdaptationOFF':
    #    ## Is Rate Adaption Used
    #    useRateAdaption = False
    #    useRandomPattern = True
    #    ## Interference Optimization
    #    interferenceAwareness = False
    #    useMultipleStreams = False
    if method == '2Random-MAS':
        ## Is Rate Adaption Used
        useRateAdaption = True
        useRandomPattern = True
        ## Interference Optimization
        interferenceAwareness = False
        useMultipleStreams = False
    if method == '3Blocked-MAS':
        ## Is Rate Adaption Used
        useRateAdaption = True
        useRandomPattern = False
        ## Interference Optimization
        interferenceAwareness = False
        useMultipleStreams = False
    if method == '4IA-Random-MAS':
        ## Is Rate Adaption Used
        useRateAdaption = True
        useRandomPattern = True
        ## Interference Optimization
        interferenceAwareness = True
        useMultipleStreams = True
    if method == '5IA-Blocked-MAS':
        ## Is Rate Adaption Used
        useRateAdaption = True
        useRandomPattern = False
        ## Interference Optimization
        interferenceAwareness = True
        useMultipleStreams = True
    else:
        assert method in ('1RateAdaptationOFF','2Random-MAS','3Blocked-MAS','4IA-Random-MAS','5IA-Blocked-MAS')


    sendInterferenceMap = True
    
    ## Szenario size
    wpansize = 5 # Area is A x A
    wpanseparation = 1
    
    maxLinkDistance = 2.0
    
    sizeX = 3*wpansize + 2*wpanseparation
    sizeY = 3*wpansize + 2*wpanseparation
    wallAtt = 8.5
  
    ## TimeSettling for probes
    settlingTimeGuard = 10.0     # SettlingTime is only used for Constanze Probes
    ## Create Timeseries probes
    createTimeseriesProbes = False
    createSNRProbes = False
  
    commonLoggerLevel = 1
    dllLoggerLevel = 2

configuration = Configuration()

## scenario setup
scenario = rise.Scenario.Scenario(xmin=0,ymin=0,xmax= configuration.sizeX, ymax= configuration.sizeY)

objs = []
## e.g. single wall
objs.append(rise.scenario.Shadowing.Shape2D(pointA = [configuration.wpansize + configuration.wpanseparation / 2.0, 0.0, 0.0], 
                                            pointB = [configuration.wpansize + configuration.wpanseparation / 2.0, configuration.sizeY, 0.0], 
                                            attenuation = dB(configuration.wallAtt / 2.0) ))
objs.append(rise.scenario.Shadowing.Shape2D(pointA = [configuration.wpansize*2 + configuration.wpanseparation *3.0 / 2.0, 0.0, 0.0], 
                                            pointB = [configuration.wpansize*2 + configuration.wpanseparation *3.0 / 2.0, configuration.sizeY, 0.0], 
                                            attenuation = dB(configuration.wallAtt / 2.0) ))
                                            
objs.append(rise.scenario.Shadowing.Shape2D(pointA = [0.0, configuration.wpansize + configuration.wpanseparation / 2.0, 0.0], 
                                            pointB = [configuration.sizeX, configuration.wpansize + configuration.wpanseparation / 2.0, 0.0], 
                                            attenuation = dB(configuration.wallAtt / 2.0) ))
objs.append(rise.scenario.Shadowing.Shape2D(pointA = [0.0, configuration.wpansize*2 + configuration.wpanseparation *3.0 / 2.0, 0.0], 
                                            pointB = [configuration.sizeX, configuration.wpansize*2 + configuration.wpanseparation *3.0 / 2.0, 0.0], 
                                            attenuation = dB(configuration.wallAtt / 2.0) ))

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
myShadowing = rise.scenario.Shadowing.Objects(obstructionList = objs,
                                              xGridBlocks = 1,
                                              yGridBlocks = 1,
                                              scenario = scenario)
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
WNS.simulationModel.nodes.append(nc.createVPS(configuration.numberOfStations +1, 1))

###########################################################################################
## Configure Stations Positions & Links
###########################################################################################

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
                            position = openwns.geometry.position.Position(transmitterXCoord, transmitterYCoord, 0),
                            channelModel = configuration.CM,
                            numberOfStations = configuration.numberOfStations,
                            interferenceAwareness = configuration.interferenceAwareness,
                            useRandomPattern = configuration.useRandomPattern,
                            useRateAdaption = configuration.useRateAdaption,
                            useMultipleStreams = configuration.useMultipleStreams,
                            sendInterferenceMap = configuration.sendInterferenceMap,
                            isDroppingAfterRetr = configuration.isDroppingAfterRetr,
                            isForwarding = configuration.isForwarding,
                            postSINRFactor = configuration.postSINRFactor,
                            defPhyMode = configuration.defPhyMode,
                            maxPER = configuration.maxPER)
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
                            position = openwns.geometry.position.Position(receiverXCoord, receiverYCoord, 0),
                            channelModel = configuration.CM,
                            numberOfStations = configuration.numberOfStations,
                            interferenceAwareness = configuration.interferenceAwareness,
                            useRandomPattern = configuration.useRandomPattern,
                            useRateAdaption = configuration.useRateAdaption,
                            useMultipleStreams = configuration.useMultipleStreams,
                            sendInterferenceMap = configuration.sendInterferenceMap,
                            isDroppingAfterRetr = configuration.isDroppingAfterRetr,
                            isForwarding = configuration.isForwarding,
                            postSINRFactor = configuration.postSINRFactor,
                            defPhyMode = configuration.defPhyMode,
                            maxPER = configuration.maxPER)
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

wimemac.evaluation.wimemacProbes.installEvaluation(WNS, range(2, configuration.numberOfStations +2), configuration) # Begin with id2 because of the VPS
wimemac.evaluation.constanzeProbes.installEvaluation(WNS, range(2, configuration.numberOfStations +2), configuration)
#wimemac.evaluation.finalEvalProbes.installEvaluation(WNS, range(2, configuration.numberOfStations +2), configuration)

###################################
## Configure probes
###################################


openwns.setSimulator(WNS)

