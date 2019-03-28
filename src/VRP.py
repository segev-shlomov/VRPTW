from math import sqrt, floor
import math
from gurobiHandler import confsTrimmer

class VRP:
    
    def __init__(self,nTrucks,capacity,targetsData, speed = 1, roundingMethod = None):
        self.nTrucks         = nTrucks
        self.capacity        = capacity
        self.speed           = speed
        self.roundingMethod  = roundingMethod 
        self.targetLocations = [(target['x'],target['y'])       for target in targetsData]
        self.targetsWindows  = [(target['start'],target['end']) for target in targetsData]
        self.targetDurations = [target['duration']              for target in targetsData]
        self.targetDemand    = [target['demand']                for target in targetsData]
        self.nTargets        = len(self.targetDemand)

    def bfsConfBuilderWrapper(self, buildParam, runParam,MaxSizeConf,alpha):
        confs=[]
        emptyconf=conf([], self, 0, 0, 0)
        lastLevelConfs = [emptyconf]
        for confSize in xrange(0,MaxSizeConf+1):
            if len(lastLevelConfs) == 0:
                break
            newConfs        = self.bfsConfBuilder(lastLevelConfs)
            # best confs for build, the rest will be chosen by solver
            nBestConfs      = int(floor(alpha * buildParam)) 
            lastLevelConfs  = self.trimConfs(newConfs, buildParam,True,nBestConfs)
            newConfsForRun  = self.trimConfs(lastLevelConfs, runParam)
            confs.extend(newConfsForRun)
            print "conf size =",confSize + 1, "built", len(newConfs), "chosen for build", len(lastLevelConfs), "chosen for run", len(newConfsForRun)
        return confs

        
    def checkFeasible(self,conf,targetId):
        
        finishTime  = conf.finishTime
        capacity    = conf.currentCapacity
        if len(conf.targets) == 0:
            lastTarget = 0
        else:
            lastTarget = conf.targets[-1]
        
        newFinish   = -1
        success     = False
        
        # capacity constraints
        newCapacity = capacity + self.targetDemand[targetId]
        if newCapacity > self.capacity:
            return (success,newFinish,newCapacity)
        
        # time window constraints
        arrivalTime = finishTime + self.getDistance(lastTarget, targetId)
        windowStart = self.targetsWindows[targetId][0]
        windowEnd   = self.targetsWindows[targetId][1]
        if arrivalTime > windowEnd:
            return (success,newFinish,newCapacity)
        waitingTime = max(0,windowStart - arrivalTime)
        newFinish   = arrivalTime + self.targetDurations[targetId] + waitingTime
        # chekc that we return to depot in time
        if newFinish + (self.getDistance(targetId,0) / self.speed) <= self.targetsWindows[0][1]:
            success     = True
        return (success,newFinish,newCapacity)
        
    def getDistance(self,t1,t2):
        (x1,y1) = self.targetLocations[t1]
        (x2,y2) = self.targetLocations[t2]
        if self.roundingMethod == "floor":
            # as done in http://pubsonline.informs.org/doi/pdf/10.1287/trsc.33.1.101
            output = floor(10 * sqrt( math.pow(x1 - x2,2) + math.pow(y1 - y2,2) ))/10
        else:
            output = sqrt( math.pow(x1 - x2,2) + math.pow(y1 - y2,2))
        return output
    
    def performShortcuts(self,optimalConfs):
        newTargetsSets = [c.targets[:] for c in optimalConfs]
        for target in range(1,self.nTargets):
            bestShortcut    = -1
            bestGain        = 10000
            foundConfs      = []
            for confId in range(len(optimalConfs)):
                currTargetSet = newTargetsSets[confId]
                try:
                    targetIndex = currTargetSet.index(target)
                except ValueError:
                    continue
                prevTarget = 0
                if targetIndex > 0:
                    prevTarget = currTargetSet[targetIndex - 1]
                nextTarget = 0
                if targetIndex < (len(currTargetSet) - 1):
                    nextTarget = currTargetSet[targetIndex + 1]
                gain = self.getDistance(prevTarget, target) + self.getDistance(target, nextTarget) - self.getDistance(prevTarget, nextTarget)
                # try to keep the conf with the minimal gain, and remove all the rest
                if (len(foundConfs) == 0) or (bestGain > gain): 
                    bestGain = gain
                    bestShortcut = confId                    
                foundConfs.append(confId)
#             print "targt =", target, "bestshortcut =",bestShortcut,foundConfs
            foundConfs.remove(bestShortcut)
            for confId in foundConfs:
                newTargetsSets[confId].remove(target)
        return map(lambda targetSet: conf(targetSet,self),newTargetsSets)
    
    def removeDups(self,confs,keyFn,valFn):
        uniqConfs = []
        targets2ConfId = {}
        nConfs = len(confs)
        for iteNum in range(nConfs):
            targetSet = confs[iteNum].targets
            currTargetSet = keyFn(targetSet)
            # if we encountered this set before
            if targets2ConfId.has_key(currTargetSet):
                foundConfVal = valFn(uniqConfs[targets2ConfId[currTargetSet]])
                # if current val is better than what we saw
                if foundConfVal > valFn(confs[iteNum]):
                    uniqConfs[targets2ConfId[currTargetSet]] = confs[iteNum]
            else:
                # this conf is not yet encountered:
                uniqConfs.append(confs[iteNum])
        return uniqConfs
           
    def trimConfs(self,confs,trimParam, forBuild = False,nBestConfs = 0):
        if forBuild:
            tuplize = lambda targetsSet: tuple([targetsSet[-1]] + sorted(targetsSet[:-1]))
            getVal  = lambda c: c.val - self.getDistance(0, c.targets[0]) - self.getDistance(c.targets[-1],0) 
        else:
            tuplize = lambda targetsSet: tuple(sorted(targetsSet))
            getVal  = lambda c: c.val
        
        uniqConfs = self.removeDups(confs, tuplize, getVal)
        nConfs = len(uniqConfs)
        if nConfs <= trimParam:
            return uniqConfs
        sortedConfs = sorted(confs, key=getVal)
        if forBuild:
            ct = confsTrimmer(sortedConfs, self.nTargets, trimParam, range(nBestConfs))
            ct.buildLP()
            confsIndices = ct.solve()
            return [sortedConfs[confsIndex] for confsIndex in confsIndices]
        else:
            return sortedConfs[0:trimParam]
    
    def bfsConfBuilder(self, lastLevelConfs):
        newConfs = []
        for currConf in lastLevelConfs: #need to check the first empty conf
            # hnadle 1st target 
            if len(currConf.targets) == 0:
                lastTarget = 0
            else:
                lastTarget = currConf.targets[-1]
            lastDistanceTravelled = self.getDistance(lastTarget,0)
            for targetId in range(1,self.nTargets):
                if targetId in currConf.targets:
                    continue
                (success, newFinishTime,newCapacity) = self.checkFeasible(currConf,targetId)
                if not success:
                    continue
                newConfTargets  = currConf.targets + [targetId]
                newConfVal      = currConf.val - lastDistanceTravelled + self.getDistance(targetId,0) + self.getDistance(lastTarget, targetId) 
                newConf         = conf(newConfTargets, self, newConfVal, newFinishTime, newCapacity)
                newConfs.append(newConf)
        return newConfs        
           
class conf:
    
    # target do not include "0" target at start and end
    # capacity is the total amount of capacity needed for the targets
    # val is the sum of all distances including from and to "0"
    def __init__(self, targets, VRPobject, val = -1, finishTime = -1, currentCapacity = -1):
        self.targets = targets
        self.VRPobject = VRPobject
        if (val == -1):
            (self.val,self.finishTime,self.currentCapacity) = self.calcParams()
        else: 
            self.val                = val
            self.finishTime         = finishTime 
            self.currentCapacity    = currentCapacity
    
    # calc val as the sum of distances between the confs
    # calc finish time as val
    def calcParams(self):
        val             = 0
        finishTime      = 0
        currentDemand   = 0
        prevTarget      = 0
        for target in self.targets:
            val             += (self.VRPobject.getDistance(prevTarget,target) / self.VRPobject.speed)
            currentDemand   += self.VRPobject.targetDemand[target]
            timeToTravel     = (self.VRPobject.getDistance(prevTarget,target) / self.VRPobject.speed)
            timeToService    = self.VRPobject.targetDurations[target]
            earlyArrival     = timeToTravel + finishTime 
            windowStart      = self.VRPobject.targetsWindows[target][0]
            waitingTime      = max(0,windowStart - earlyArrival)
            finishTime      += timeToTravel + waitingTime + timeToService 
            prevTarget       = target
            
        val         += (self.VRPobject.getDistance(prevTarget,0) / self.VRPobject.speed)
        return (val,finishTime,currentDemand)
    
    def printConfTimes(self):
        prevTarget = 0
        currTime   = 0
        distanceRounded = 0.0
        for target in self.targets:
            timeToTravel     = (self.VRPobject.getDistance(prevTarget,target) / self.VRPobject.speed)
            distanceRounded += self.VRPobject.getDistance(prevTarget,target)
            timeToService    = self.VRPobject.targetDurations[target]
            earlyArrival     = timeToTravel + currTime 
            windowStart      = self.VRPobject.targetsWindows[target][0]
            waitingTime      = max(0,windowStart - earlyArrival)
            feasibleAssignmentStr = '' 
            if currTime + timeToTravel + waitingTime > self.VRPobject.targetsWindows[target][1]:
                feasibleAssignmentStr = "**"
            print target, "starting at", currTime + timeToTravel + waitingTime, "window is", self.VRPobject.targetsWindows[target], \
                "capacity is", self.VRPobject.targetDemand[target], feasibleAssignmentStr
            currTime        += timeToTravel + waitingTime + timeToService 
            prevTarget       = target
        distanceRounded += self.VRPobject.getDistance(prevTarget,0)
        print "total distance is", distanceRounded
                  
        
    