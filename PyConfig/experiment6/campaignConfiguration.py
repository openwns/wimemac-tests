#! /usr/bin/python
###############################################################################
# This file is part of openWNS (open Wireless Network Simulator)
# _____________________________________________________________________________
#
# Copyright (C) 2004-2007
# Chair of Communication Networks (ComNets)
# Kopernikusstr. 16, D-52074 Aachen, Germany
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

from wrowser.simdb.Parameters import AutoSimulationParameters, Parameters, Bool, Int, Float, String
import wrowser.Configuration as config
import wrowser.simdb.Database as db
import subprocess
import scipy

###################################
# Simple parameter generation HowTo
#
# First, you need to define your simulation parameters in a class derived from Parameters, e.g.
#
class Set(AutoSimulationParameters):
    # scenario parameter
    simTime = Float(parameterRange = [20.0])
    #wallAtt = Float(parameterRange = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 17.5, 20.0, 22.5, 25.0])
    #wallAtt = Float(parameterRange = [0.0, 2.0, 4.0, 6.0, 8.0, 8.5, 10.0, 12.0, 14.0, 17.5, 20.0, 25.0])
    wallAtt = Float(parameterRange = [8.5])
    method = String(parameterRange = ['2Random-MAS','4IA-Random-MAS'])
    #method = String(parameterRange = ['3Blocked-MAS','5IA-Blocked-MAS'])
    numberOfLinkspWPAN = Int(parameterRange = [5])
    maxLinkDistance = Float(parameterRange = [2.0])
    #Seed = Float(parameterRange = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0])
    Seed = Float(parameterRange = [7.0])
   
    # input parameter
    offeredLoadpLink = Int(default = 16E6)

## Search for receiver with the least incoming throughput
def getTotalThroughput(paramsString, inputName, cursor):
    
    #print paramsString
    parameterIndex = paramsString.index('numberOfLinkspWPAN =') + 21            # get Index of parameter numberOfLinkspWPAN
    str_numberOfLinkspWPAN = paramsString[parameterIndex:(parameterIndex + 3)]  # get substring of size 3 characters
    str_numberOfLinkspWPAN = str_numberOfLinkspWPAN.rstrip('AND ')              # strip substring into the number value only; size of value can vary
    
    numberOfStations = int(str_numberOfLinkspWPAN)*2*5                          # *2 stations per Link *5 WPANs
    ## all receiver stations have odd IDs
    resultsALL = []
    for STA in range(3, numberOfStations+2, 2):                                 # Station with ID==1 is the VPS, receiver stations start with ID 3  
        myQuery = " \
           SELECT idResults.scenario_id, idResults." + inputName + ", VAL.mean \
           FROM moments VAL, (SELECT scenario_id, " + inputName + " FROM parameter_sets \
                              WHERE " + paramsString + ") AS idResults \
           WHERE VAL.scenario_id = idResults.scenario_id AND \
           	     VAL.alt_name = 'traffic.endToEnd.window.incoming.bitThroughput_wns.node.Node.id" + str(STA) + "_Moments' \
           ORDER BY idResults." + inputName + ";"
        cursor.execute(myQuery)
        query = cursor.fetchall()
        resultsALL.append(query)

    ## initially fill results with the values of the first station
    results = []    
    for initialResults in (resultsALL[0]):
        results.append(initialResults)
    
    ## update results with minimum of the stations throughput
    for resultSTAIndex in range(len(resultsALL)):
        resultSTA = resultsALL[resultSTAIndex]
        for dbQueryIndex in range(len(resultSTA)):
            dbQuery = resultSTA[dbQueryIndex]

            assert (dbQuery[0] == results[dbQueryIndex][0]) ## scenarios IDs in queries should be the same
            if dbQuery[2] < results[dbQueryIndex][2]:       ## check and update if incoming throughput is smaller than the currently saved value
                #print "Updated Scenario: " + str(dbQuery[0]) + " with previous value " + str(results[dbQueryIndex][2]) + " to new value " + str(dbQuery[2])
                results[dbQueryIndex] = dbQuery
                
    return results




#################################
conf = config.Configuration()
conf.read("./.campaign.conf")
db.Database.connectConf(conf)
cursor = db.Database.getCursor()

params = Set('offeredLoadpLink', cursor, conf.parser.getint("Campaign", "id"), getTotalThroughput)
[status, results] = params.binarySearch(maxError = 0.05,
                                        exactness = 0.05,
                                        createSimulations=True,
                                        debug=True)


numberOfStations = params.numberOfLinkspWPAN*2*5                                    # *2 stations per Link *5 WPANs
#################################
## Write results to file
str_results = str(results)
f_out = open("results.m", "w")

cleanresults = []
while str_results.find("{") != -1:
    # Get limiters
    lLimit = str_results.find("{")
    rLimit = str_results.find("}") + 1
    
    newElement = str_results[lLimit:rLimit]
    str_results = str_results.replace(newElement, "")
    cleanresults.append(newElement)

for i in range(len(cleanresults)):
    f_out.write(cleanresults[i])
    f_out.write('\n')

f_out.close()

f_out = open("resultsSorted.m", "w")
#finalLoads_file = open("finalLoads.m", "w")

resultsIARandom = []
for i in range(len(cleanresults)):
    ## Get result value
    resultValIndex = cleanresults[i].index('result') + 9
    #resultVal = cleanresults[i][resultValIndex:(cleanresults[i].index('}'))]
    resultVal = cleanresults[i][resultValIndex:(cleanresults[i].index('scenarioId') -3)]
    ## Get scenario ID
    scenarioValIndex = cleanresults[i].index('scenarioId') + 13
    scenarioVal = cleanresults[i][scenarioValIndex:(scenarioValIndex + 5)]

    resultsIARandom.append(resultVal + " ")


#    finalLoads = []
#    myQuery = " \
#        SELECT offeredLoadpLink, Seed \
#        FROM parameter_sets \
#        WHERE scenario_id = " + scenarioVal + ";"
#
#
#    cursor.execute(myQuery)
#    query = cursor.fetchall()
#    finalLoads.append(query)
#    finalLoads_file.write(str(query))
#    finalLoads_file.write('\n')
#    print query

#finalLoads_file.close()

f_out.write("Results IA-Random-MAS")
f_out.write('\n')

for i in range(len(resultsIARandom)):
    f_out.write(resultsIARandom[i])
    
f_out.write('\n')

f_out.close()

## end file writing
######################################





print "%d new / %d waiting / %d finished simulations" %(status['new'],
                                                        status['waiting'],
                                                        status['finished'])
if(status['new'] > 0):
    subprocess.call(['./simcontrol.py --create-scenarios'],
                    shell = True)
    subprocess.call(['./simcontrol.py --queue-scenarios-with-state=NotQueued -t 10'],
                    shell = True)

