import utils
import os
import sys

dbg = False
if not dbg:
    optiosHnadler   = utils.optionsHandler(sys.argv)
    (runParam,buildParam,solomonLib,timeout,setNumTrucks,alpha) = optiosHnadler.parseOptions()
    dirName = "solomon_" + str(solomonLib)
else:
    dirName = "solomon_" + str(100)
    f = "C208.txt"
    runParam,buildParam,timeout,setNumTrucks,alpha = 10000,10000,18000,True,0.5
runner          = utils.vrpRunner('solomon')
filePrinter     = utils.filePrinter()
bestsol         = utils.bestSols()
headers         = ["fileName","buildParam","runParam","maxConfSize","confBuildTime","solverTime","opt_n_trucks","opt_distance","nTrucks","totalDistance","exitOnTimeOut"]
dirNames2sols   = {"solomon_25":bestsol.all25Data,"solomon_50":bestsol.all50Data,"solomon_100":bestsol.all100Data}
dirNames        = dirNames2sols.keys()
dataDir         = "../data/"
maxConfSize     = 100
capacity        = 80

if dbg:
    res = runner.generateAndSolveInstance(dataDir + dirName + "/" + f, buildParam, runParam, maxConfSize,timeout,setNumTrucks,alpha)
    sys.exit()
allFiles = []
for f in os.listdir(dataDir + dirName):
    if f.endswith(".txt"):
        allFiles.append(f)
outputFileName = "res_" + dirName + "_" + str(alpha) + ".csv"
filePrinter.printHeaderIfNewFile(outputFileName, headers)
fileIndex = 1
for f in allFiles:
    res = runner.generateAndSolveInstance(dataDir + dirName + "/" + f, buildParam, runParam, maxConfSize,timeout,setNumTrucks,alpha, capacity)
    solKey = f[:-4]
    if solKey in dirNames2sols[dirName]:
        res["opt_n_trucks"] = dirNames2sols[dirName][solKey][0]
        res["opt_distance"] = dirNames2sols[dirName][solKey][1]
    else:
        res["opt_n_trucks"] = "n/a"
        res["opt_distance"] = "n/a"
    filePrinter.printSingleRes(res, outputFileName, headers)
    print "\n\ndone file",fileIndex, "out of", len(allFiles),"\n"
    fileIndex += 1
