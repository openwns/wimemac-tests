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
import ip
import ip.evaluation.default

import wimemac.support.Configuration
import wimemac.evaluation.acknowledgedModeShortCut
import wimemac.evaluation.probetest

from openwns import dBm, dB

import rise.Scenario

import rise.scenario.FastFading
import rise.scenario.Propagation
import rise.scenario.Shadowing
import rise.scenario.Pathloss

import ofdmaphy.OFDMAPhy


#throughputPerStation = configuration.speed * configuration.load / configuration.numberOfStations
throughputPerStation = 120E6

class Configuration:
    maxSimTime = 5.0
    # must be < 250 (otherwise IPAddress out of range)
    numberOfStations = 2
    # 100 MBit/s
    speed = 53.3E6
    # 1500 byte
    fixedPacketSize = 1480 * 8
    # traffic generator will offer traffic with speed*load
    load = 7.2E-3 #0.5
    # fixed Bit Error Rate
    fixedBER = 1E-5
    # resendTimeout of StopAndWait-ARQ (be careful with this one!)
    resendTimeout = 0.01 
    commonLoggerLevel = 1
    dllLoggerLevel = 2


configuration = Configuration()


# create an instance of the WNS configuration
# The variable must be called WNS!!!!
WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE
WNS.maxSimTime = configuration.maxSimTime


sizeX, sizeY = 8, 10 # -> two stations distance = sizeX/2
scenario = rise.Scenario.Scenario(xmin=0,ymin=0,xmax=sizeX, ymax=sizeY)                                              

######################################
# Radio channel propagation parameters
myPathloss = rise.scenario.Pathloss.PyFunction(
    validFrequencies = Interval(3100, 10600),
    validDistances = Interval(1, 100), #[m]
    offset = dB(-27.5522),
    freqFactor = 20,
    distFactor = 20,
    distanceUnit = "m", # only for the formula, not for validDistances
    minPathloss = dB(42), # pathloss at 1m distance
    outOfMinRange = rise.scenario.Pathloss.Constant("42 dB"),
    outOfMaxRange = rise.scenario.Pathloss.Deny(),
    scenarioWrap = False,
    sizeX = sizeX,
    sizeY = sizeY)
myShadowing = rise.scenario.Shadowing.No()
myFastFading = rise.scenario.FastFading.No()
propagationConfig = rise.scenario.Propagation.Configuration(
    pathloss = myPathloss,
    shadowing = myShadowing,
    fastFading = myFastFading)
# End radio channel propagation parameters
##########################################


# create an instance of the NodeCreatorls 
nc = wimemac.support.NodeCreator.NodeCreator(propagationConfig)

idGen = wimemac.support.idGenerator()

ofdmaPhyConfig = WNS.modules.ofdmaPhy

#from ChannelManagerPool.py for 1 MeshChannel
managers = []
sys = ofdmaphy.OFDMAPhy.OFDMASystem('ofdma')
sys.Scenario = scenario
managers.append(sys)

ofdmaPhyConfig.systems.extend(managers)
###


class MySTAConfig(object):
    frequency = None
    bandwidth = 528
    txPower = None
    postSINRFactor = None
    position = None
    defPhyMode = None
    channelModel = None
    interferenceAwareness = None
    maxPER = None
    interferenceThreshold = None
    def __init__(self, initFrequency, position, channelModel, interferenceAwareness = True, interferenceThreshold = dBm(-92), maxPER = 0.08, txPower = dBm(-14), postSINRFactor = dB(0.0), defPhyMode = 7):
        self.frequency = initFrequency
        self.position = position
        self.txPower = txPower
        self.postSINRFactor = postSINRFactor
        self.defPhyMode = defPhyMode
        self.channelModel = channelModel
        self.interferenceAwareness = interferenceAwareness
        self.interferenceThreshold = interferenceThreshold
        self.maxPER = maxPER
                                          
# create Stations
# if distance <= 4 use different channel model
if sizeX/2 <= 4:
    CM = 2
else:
    CM = 3
    
for i in xrange(configuration.numberOfStations):
    staConfig = MySTAConfig(initFrequency = 5016,
                            position = openwns.geometry.position.Position(
                                            (sizeX / configuration.numberOfStations /2) + (sizeX / configuration.numberOfStations * i), sizeY / 2 ,0),
                            channelModel = CM,
                            interferenceAwareness = False,
                            postSINRFactor = dB(0.0),
                            defPhyMode = 3)
    station = nc.createSTA(idGen,
                           config = staConfig,
                           loggerLevel = configuration.commonLoggerLevel,
                           dllLoggerLevel = configuration.dllLoggerLevel)
    WNS.simulationModel.nodes.append(station)
    


###
for i in xrange(configuration.numberOfStations):
    cbr = constanze.Constanze.CBR(0.01, throughputPerStation, configuration.fixedPacketSize)
    ipBinding = constanze.Node.IPBinding(WNS.simulationModel.nodes[i-1].nl.domainName, WNS.simulationModel.nodes[i].nl.domainName)
#    #WNS.simulationModel.nodes[i-1].load.addTraffic(ipBinding, cbr)
    ipListenerBinding = constanze.Node.IPListenerBinding(WNS.simulationModel.nodes[i-1].nl.domainName)
    listener = constanze.Node.Listener(WNS.simulationModel.nodes[i-1].nl.domainName + ".listener")
    WNS.simulationModel.nodes[i-1].load.addListener(ipListenerBinding, listener)
    
WNS.simulationModel.nodes[0].load.addTraffic(ipBinding, cbr)



# one Virtual ARP Zone
varp = VirtualARPServer("vARP", "theOnlySubnet")
WNS.simulationModel.nodes = [varp] + WNS.simulationModel.nodes

vdhcp = VirtualDHCPServer("vDHCP@",
                          "theOnlySubnet",
                          "192.168.0.2", "192.168.254.253",
                          "255.255.0.0")

vdns = VirtualDNSServer("vDNS", "ip.DEFAULT.GLOBAL")
WNS.simulationModel.nodes.append(vdns)

WNS.simulationModel.nodes.append(vdhcp)

# modify probes afterwards
#wimemac.evaluation.acknowledgedModeShortCut.installEvaluation(WNS, range(1, configuration.numberOfStations + 1))


wimemac.evaluation.probetest.installEvaluation(WNS, range(1, configuration.numberOfStations +1))

#ip.evaluation.default.installEvaluation(sim = WNS,
#                                        maxPacketDelay = 0.5,     # s
#                                        maxPacketSize = 2000*8,   # Bit
#                                        maxBitThroughput = 10E6,  # Bit/s
#                                        maxPacketThroughput = 1E6 # Packets/s
#                                        )

#########################

#constanze.evaluation.default.installEvaluation(sim = WNS,
#                                               maxPacketDelay = 1.0,
#                                               maxPacketSize = 16000,
#                                               maxBitThroughput = 100e6,
#                                               maxPacketThroughput = 10e6,
#                                               delayResolution = 1000,
#                                               sizeResolution = 2000,
#                                               throughputResolution = 10000)

from openwns.evaluation import *
sourceName = 'traffic.endToEnd.window.incoming.bitThroughput'
node = openwns.evaluation.createSourceNode(WNS, sourceName)
node.appendChildren(SettlingTimeGuard(2.0))
node.getLeafs().appendChildren(Separate(by = 'wns.node.Node.id', forAll = range(1, configuration.numberOfStations +1), format="wns.node.Node.id%d"))
node.getLeafs().appendChildren(PDF(name = sourceName,
                        description = 'average bit rate [Bit/s]',
                        minXValue = 0.0,
                        maxXValue = 500e6,
                        resolution = 10000))









#########################

openwns.setSimulator(WNS)
#openwns.evaluation.default.installEvaluation(sim = WNS)

#Enable Warp2Gui output
node = openwns.evaluation.createSourceNode(WNS, "wimemac.guiProbe")
node.appendChildren(openwns.evaluation.generators.TextTrace("wimemac.guiText", ""))


