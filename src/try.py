import VRP
import readers
from gurobiHandler import vrpSolver
from VRP import conf
import itertools
 
reader = readers.solomonFileReader()
 
fileName = "../data/solomon_25/C101.txt"
data = reader.readFile(fileName)
vrp = VRP.VRP(data["nTrucks"], data["capacity"], data["targets"])
 
confs = vrp.bfsConfBuilderWrapper(20000,20000, 15)
  
s = vrpSolver(confs, vrp)
s.buildIP()
x=s.solve()
def iterClusters(confs):
    targets = [5, 3, 7, 8, 11, 9, 6, 4, 10]
    targets1 = [20, 24, 25, 23, 22, 21]
    targets2 = [13, 17, 18, 19, 15, 16, 14, 12]
     
     
    targets = [5, 3, 7, 8, 10, 11, 9, 6, 4, 2, 1]
    for i in range(len(targets) + 1):
        c = conf(targets[:i],vrp)
        c.printConfTimes()
        print "generated conf",c.targets,"=",len(filter(lambda con: con.targets == c.targets,confs))
     
    g = itertools.permutations(targets2)
    bestVal = 10000
    bestC = None
    for p in g:
    #     c = conf(list(p) + [2,1], vrp)
        c = conf(list(p), vrp)
    #     print c.val,";",c.finishTime,";",c.targets
        if c.val < bestVal:
            bestVal = c.val
            bestC = c
    print "best val is", bestVal,"best finish time",bestC.finishTime ,"best C is",bestC.targets
 
def printBestConfs():
    t1 = [5, 3, 7, 8, 10, 11, 9, 6, 4, 2, 1]
    t2 = [20, 24, 25, 23, 22, 21]
    t3 = [13, 17, 18, 19, 15, 16, 14, 12]
      
    c1 = conf(t1, vrp)
    c2 = conf(t2, vrp)
    c3 = conf(t3, vrp)
      
    c1.printConfTimes()
    print "c1 val is", c1.val
    c2.printConfTimes()
    print "c2 val is", c2.val
    c3.printConfTimes()
    print "c3 val is", c3.val
      
    print "\ntotal val is", c1.val + c2.val + c3.val


