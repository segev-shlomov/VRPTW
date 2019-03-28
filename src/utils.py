import VRP
import readers
import time
from gurobiHandler import vrpSolver
import csv
import getopt
import sys
import os
import matplotlib.pyplot as plt
import networkx as nx

class vrpRunner:
    
    def __init__(self,readerType):
        if readerType == "solomon":
            self.reader = readers.solomonFileReader()
        else:
            raise Exception("illegal reader type: " + readerType)
    
    def generateAndSolveInstance(self,fileName,buildParam,runParam,maxConfSize,timeout,setNumTrucks,alphs, capacity = None):
        data = self.reader.readFile(fileName)
        if not capacity:
            capacity = data["capacity"]
        vrp = VRP.VRP(data["nTrucks"],capacity , data["targets"])
        t1 = time.time()
        confs = vrp.bfsConfBuilderWrapper(buildParam, runParam, maxConfSize,alphs)
        t2 = time.time()
        if setNumTrucks:
            for nConfs in range(1,vrp.nTargets):
                print "trying with nConfs",nConfs,"..."
                s = vrpSolver(confs, vrp,timeout)
                s.buildIP(nConfs)
                [nVehicles,totalDistance,exitOnTimeOut] = s.solve()
                if nVehicles > -1:
                    break
                if nVehicles == -2:
                    return {'nTrucks' : "n/a", 'totalDistance':"n/a",'confBuildTime': t2 - t1, 'solverTime': time.time() - t2,"fileName":fileName,\
                "buildParam":buildParam,"runParam":runParam,"maxConfSize":maxConfSize,"exitOnTimeOut":exitOnTimeOut}
        else:
            s = vrpSolver(confs, vrp,timeout)
            s.buildIP()
            [nVehicles,totalDistance,exitOnTimeOut] = s.solve()
        t3 = time.time()
        return {'nTrucks' : nVehicles, 'totalDistance':totalDistance,'confBuildTime': t2 - t1, 'solverTime': t3 - t2,"fileName":fileName,\
                "buildParam":buildParam,"runParam":runParam,"maxConfSize":maxConfSize,"exitOnTimeOut":exitOnTimeOut}

class filePrinter:
    
    def __init__(self):
        pass
    
    def printHeaderIfNewFile(self,filename,headers):
        if not os.path.isfile(filename):
            csvfile = open(filename, 'ab')
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            csvfile.close()

    def printSingleRes(self,res,filename,headers):
        csvfile = open(filename, 'ab')
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writerow(res)
        csvfile.close

    def printRes(self,allRes,filename,headers):
        writeHeader = True
        if os.path.isfile(filename):
            writeHeader = False
        csvfile = open(filename, 'ab')
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        if writeHeader:
            writer.writeheader()
        writer.writerows(allRes)
        csvfile.close

class graphPrinter:
    
    def __init__(self):
        pass
    
    def printGraph(self,vrp,chosenConfs,name):
        G=nx.Graph()
        
        # set positions
        pos = {}
        for target in range(len(vrp.targetLocations)):
            pos[target] = vrp.targetLocations[target]
            G.add_node(target)
        
        for c in chosenConfs:
            G.add_cycle([0] + c.targets)
        
        nx.draw_networkx_nodes(G,pos,node_size=5)
        nx.draw_networkx_edges(G,pos)
        plt.axis('off')
        plt.savefig(name) # save as png
        plt.show() # display
    
    def printGraphFromIlog(self,truck2Targets,targets,name):
        G=nx.Graph()
        
        # add nodes
        for target in targets:
            G.add_node(target)
        G.add_node(0)
        targets[0] = (35,35)
        
        for t in truck2Targets:
            G.add_cycle([0] + truck2Targets[t])
        
        nx.draw_networkx_nodes(G,targets,node_size=5)
        nx.draw_networkx_edges(G,targets)
        plt.axis('off')
        plt.savefig(name) # save as png
        plt.show() # display
        
class optionsHandler:
    
    def usage(self):
        print "-r <run param>"
        print "-b <build param>"
        print "-n [25|50|100] <solomon lib>"
        print "-t <gurobi timeout>"
        print "-i <instance name>"
        print "-s [t|f] <iteratively solve with a set num of trucks, default is f>"
        print "-a <alpha*trimParam best confs, the rest will be chosen to maximize variance>"
        
    def assertOptions(self,runParam,buildParam,solomonLib,timeout,instanceName = None):
        message = ""
        if runParam == 0:
            message += "must supply run param"
        if buildParam == 0:
            message += "must supply build param"
        if solomonLib == 0:
            message += "must supply solomonLib"
        if timeout == 0:
            message += "must supply timeout"
        if instanceName == "":
            message += "must supply instance name"

        if message != "":
            print "one or more errors in parsing input:"
            print message
            self.usage()
            sys.exit(2)
            
    
    def __init__(self,args):
        try:
            opts, _ = getopt.gnu_getopt(args[1:], "r:b:n:t:s:i:a:")
            self.opts = opts
        except getopt.GetoptError as err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            self.usage()
            sys.exit(2)
    
    def parseOptions(self,enforceInstanceName = False):
        runParam = 0
        buildParam = 0
        solomonLib = 0
        timeout = 0
        alpha = 1.0
        instanceName = ""
        setNumTrucks = False
        for o, a in self.opts:
            if o == "-h":
                self.usage()
                sys.exit(0)
            elif o == "-s":
                if a == "t":
                    setNumTrucks = True
                elif a != "f":
                    print "invalid value for -s", a
                    self.usage()
                    sys.exit(0)
            elif o == "-r":
                runParam = int(a)
                if runParam < 0:
                    print "invalid run param", a
                    sys.exit(0)
            elif o == "-t":
                timeout = int(a)
                if timeout < 0:
                    print "invalid timeout", a
                    sys.exit(0)
            elif o == "-b":
                buildParam = int(a)
                if buildParam < 0:
                    print "invalid build param", a
                    sys.exit(0)
            elif o == "-i":
                instanceName = a
            elif o == "-a":
                alpha = float(a)
                if alpha > 1.0 or alpha < 0.0:
                    print "invalid alpha value", a
                    sys.exit(0)
            elif o == "-n":
                solomonLib = int(a)
                if solomonLib not in [25,50,100]:
                    print "invalid solomonLib", a
                    sys.exit(0)
            else:
                assert False, "unhandled option : " + o
        if enforceInstanceName:
            self.assertOptions(runParam,buildParam,solomonLib,timeout,instanceName)
            return (runParam,buildParam,solomonLib,timeout,setNumTrucks,alpha,instanceName)
        else: 
            self.assertOptions(runParam,buildParam,solomonLib,timeout)
            return (runParam,buildParam,solomonLib,timeout,setNumTrucks,alpha)

class bestSols:
    def __init__(self):
        # data taken from http://www.bernabe.dorronsoro.es/vrp/
        self.all25Data = {"C101":[3,191.3],"C102":[3,190.3],"C103":[3,190.3],"C104":[3,186.9],"C105":[3,191.3],\
                          "C106":[3,191.3],"C107":[3,191.3],"C108":[3,191.3],"C109":[3,191.3],\
                          
                          "C201":[2,214.7],"C202":[2,214.7],"C203":[2,214.7],"C204":[1,213.1],\
                          "C205":[2,214.7],"C206":[2,214.7],"C207":[2,214.5],"C208":[2,214.5],\
                          
                          "R101":[8,617.1],"R102":[7,547.1],"R103":[5,454.6],"R104":[4,416.9],"R105":[6,530.5],"R106":[5,465.4],\
                          "R107":[4,424.3],"R108":[4,397.3],"R109":[5,441.3],"R110":[4,444.1],"R111":[4,428.8],"R112":[4,393.0],\
                          
                          "R201":[4,463.3],"R202":[4,410.5],"R203":[3,391.4],"R204":[2,355.0],"R205":[3,393.0],"R206":[3,374.4],\
                          "R207":[3,361.6],"R208":[1,328.2],"R209":[2,370.7],"R210":[3,404.6],"R211":[2,350.9],\
                          
                          "RC101":[4,461.1],"RC102":[3,351.8],"RC103":[3,332.8],"RC104":[3,306.6],\
                          "RC105":[4,411.3],"RC106":[3,345.5],"RC107":[3,298.3],"RC108":[3,294.5],\
                          
                          "RC201":[3,360.2],"RC202":[3,338.0],"RC203":[3,326.9],"RC204":[3,299.7],\
                          "RC205":[3,338.0],"RC206":[3,324.0],"RC207":[3,298.3],"RC208":[2,269.1]}
                    
        self.all50Data = {"C101":[5,362.4],"C102":[5,361.4],"C103":[4,361.4],"C104":[5,359.0],"C105":[5,362.4],\
                          "C106":[5,362.4],"C107":[5,362.4],"C108":[5,362.4],"C109":[5,362.4],\
                          
                          "C201":[3,360.2],"C202":[3,360.2],"C203":[3,359.8],"C204":[2,353.4],\
                          "C205":[3,359.8],"C206":[3,359.8],"C207":[3,359.6],"C208":[2,350.5],\
                          
                          "R101":[13,1047.0],"R102":[12,944.9],"R103":[9,772.9],"R104":[6,631.2],"R105":[10,906.6],"R106":[8,793.6],\
                          "R107":[7,720.4]  ,"R108":[6,618.2] ,"R109":[8,803.2],"R110":[8,724.9],"R111":[8,724.9],"R112":[6,651.1],\
                          
                          "R201":[6,800.7],"R202":[5,712.2],"R203":[5,606.4],"R204":[2,509.5],"R205":[5,703.3],"R206":[5,647.0],\
                          "R207":[4,584.6],"R208":[2,487.7],"R209":[4,600.6],"R210":[5,663.4],"R211":[3,551.3],\
                    
                          "RC101":[9,957.9],"RC102":[8,844.3],"RC103":[6,712.6],"RC104":[5,546.5],\
                          "RC105":[9,888.9],"RC106":[7,791.9],"RC107":[6,664.5],"RC108":[6,598.1],\
                          
                          "RC201":[5,684.8],"RC202":[5,613.6],"RC203":[4,555.3],"RC204":[3,444.2],\
                          "RC205":[5,631.0],"RC206":[5,610.0],"RC207":[4,558.6],"RC208":[100,10000]}
                        
                        
        self.all100Data = {"C101":[10,827.3],"C102":[10,827.3],"C103":[10,826.3],"C104":[10,822.9],"C105":[10,827.3],\
                           "C106":[10,827.3],"C107":[10,827.3],"C108":[10,827.3],"C109":[10,827.3],\
                           
                           "R101":[20,1637.7],"R102":[18,1466.6],"R103":[14,1208.7],"R104":[10,982.01],"R105":[15,1355.3],"R106":[13,1234.6],\
                           "R107":[11,1064.6],"R108":[9,960.88],"R109":[13,1146.9],"R110":[12,1068],"R111":[12,1048.7],"R112":[9,982.14],\
                           
                           "RC101":[15,1619.8],"RC102":[14,1457.4],"RC103":[11,1258],"RC104":[10,1135.48],\
                           "RC105":[15,1513.7],"RC106":[11,1424.73],"RC107":[11,1230.48],"RC108":[10,1139.82]}
        
        # data taken from http://w.cba.neu.edu/~msolomon/c1c2solu.htm
        dataToAdd_100 = {"C201":[3,589.1],"C202":[3,589.1],"C203":[3,588.7],"C204":[3,588.1],"C205":[3,586.4],\
                         "C206":[3,586.0],"C207":[3,585.8],"C208":[3,585.8]}
        self.all100Data.update(dataToAdd_100)
        
        # data taken from http://sun.aei.polsl.pl/~zjc/best-solutions-solomon.html
        dataToAdd_100 = {"R101":[19,1650.79],"R102":[17,1486.85],"R103":[13,1292.67],"R104":[9,1007.31],"R105":[14,1377.11],\
                         "R106":[12,1252.03],"R107":[10,1104.65],"R109":[11,1194.73],"R110":[10,1118.83],"R111":[10,1096.73],\
                         
                         "R201":[4,1252.37],"R202":[3,1191.70],"R203":[3,939.50],"R204":[2,825.52],"R205":[3,994.43],"R206":[3,906.14],\
                         "R207":[2,890.61],"R208":[2,726.82],"R209":[3,909.16],"R210":[3,939.37],"R211":[2,885.71],\
                         
                         "RC101":[14,1696.95],"RC102":[12,1554.75],"RC105":[13,1629.44],\
                         
                         "RC201":[4,1406.94],"RC202":[3,1365.64],"RC203":[3,1049.62],"RC204":[3,798.46],\
                         "RC205":[4,1297.65],"RC206":[3,1146.32],"RC207":[3,1061.14],"RC208":[3,828.14]}
        
        self.all100Data.update(dataToAdd_100)
        