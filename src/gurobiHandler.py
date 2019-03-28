import gurobipy
from gurobipy.gurobipy import gurobi
from gurobipy import gurobipy
import numpy as np
import csv

class vrpSolver:
    
    def __init__(self, confs, VRPobject,timeout):
        indices = {}
        for i in range(1,VRPobject.nTargets):
            indices[i] = []
        cId = 0
#         f = lambda t: indices[t].append[cId]
        for c in confs:
            map(lambda t: indices[t].append(cId), c.targets)
            cId += 1 
        
        self.confs = confs
        self.indices = indices
        self.VRPobj = VRPobject
        self.M      = 1000 
        self.timeout = timeout
            
    def buildIP(self, setNumTrucks = None):
        model = gurobipy.Model('VRPModel')
        model.setParam('OutputFlag',False)
        
        # variables
        x = {}
        for i in range(len(self.confs)):
            x[i] = model.addVar(vtype=gurobipy.GRB.BINARY, name=str(i))
        model.update()

        # constraints
        for targetId in self.indices:
            model.addConstr(gurobipy.quicksum(x[i] for i in self.indices[targetId]) >= 1,'target_%s' % (i))
        
        if setNumTrucks:    
            model.addConstr(gurobipy.quicksum(x[i] for i in range(len(self.confs))) <= setNumTrucks,'at_most_%i_confs' % (setNumTrucks))
        
        # objective
        if setNumTrucks:
            model.setObjective(gurobipy.quicksum( x[i]*(self.confs[i].val) for i in range(len(self.confs)) ) )
        else:
            model.setObjective(gurobipy.quicksum(x[i]*(self.confs[i].val + self.M) for i in range(len(self.confs))))
        model.setAttr("modelSense", gurobipy.GRB.MINIMIZE)
        model.setParam('TimeLimit', self.timeout)
        model.update()
        
        self.x = x
        self.model = model
    
    def solve(self):
        # Compute optimal solution
        self.model.optimize()
        chosenConfs = []
        exitOnTimeOut = False
        print "status =",self.model.status,"(",gurobipy.GRB.status.OPTIMAL,"=opt,",gurobipy.GRB.status.INFEASIBLE,"=inf,",gurobipy.GRB.status.TIME_LIMIT,"=timout)"
        if self.model.status == gurobipy.GRB.status.INFEASIBLE:
            return [-1,-1,-1]
        if self.model.status in [gurobipy.GRB.status.OPTIMAL,gurobipy.GRB.status.TIME_LIMIT]:
            if self.model.status == gurobipy.GRB.status.TIME_LIMIT:
                exitOnTimeOut = True
            if (self.model.SolCount == 0) and exitOnTimeOut:
                print "exit on timeout with no feasible solution!"
                return [-2,-1,exitOnTimeOut]
            for i in range(len(self.confs)):
                if self.x[i].x > 0:
                    print "conf", i, "was chosen"
                    chosenConfs.append(i)
            print "\nopt val is", self.model.getAttr("ObjVal")
        confsWithShortcuts = self.VRPobj.performShortcuts(map(lambda c: self.confs[c],chosenConfs))
        self.chosenConfs = confsWithShortcuts
        totalDist = 0.0
        for con in confsWithShortcuts:
            totalDist += con.val
            print con.targets
        print "\nnVehicels =",len(confsWithShortcuts), "total distance =",totalDist
        return [len(confsWithShortcuts),totalDist,exitOnTimeOut]


class confsTrimmer:
    
    def __init__(self,confs,nTargets,trimParam,chosenConfsIndices = []):
        self.confsTargets       = [c.targets for c in confs]
        self.nConfs             = len(self.confsTargets)
        self.nTargets           = nTargets
        self.trimParam          = trimParam
        self.chosenConfsIndices = chosenConfsIndices
        self.csvFileNAme        = "xs.csv"
        
    def buildLP(self):
        model = gurobipy.Model('trimModel')
        model.setParam('OutputFlag',False)
        
        x = {}
        for i in range(self.nConfs):
            x[i] = model.addVar(vtype=gurobipy.GRB.CONTINUOUS, name="x_%s" % (i), ub=1.0)
        s = {}
        for j in range(self.nTargets):
            s[j] = model.addVar(vtype=gurobipy.GRB.CONTINUOUS, name="s_%s" % (i))    
        model.update()
        
        model.addConstr(gurobipy.quicksum(x[i] for i in range(self.nConfs)    ) >= self.trimParam, '%s_confs' % (self.trimParam))
        for chosenConfIndex in self.chosenConfsIndices:
            model.addConstr(x[chosenConfIndex] >= 1.0, '%s_conf' % (chosenConfIndex))
        
        for j in range(self.nTargets):
            relevantConfs = [i for i in range(self.nConfs) if j in self.confsTargets[i]]
            model.addConstr(gurobipy.quicksum(x[i] for i in relevantConfs) <= s[j], 'col_%s' % (j))
        model.update()
        
        model.setObjective(gurobipy.quicksum(s[j] * s[j] for j in range(self.nTargets)))
        model.setAttr("modelSense", gurobipy.GRB.MINIMIZE)
        model.update()
        model.write('tmp.lp')
        self.x = x
        self.model = model

    def solve(self):
        # Compute optimal solution
        self.model.optimize()
        chosenConfs = []
        if self.model.status == gurobipy.GRB.status.OPTIMAL:
            for i in range(self.nConfs):
                if self.x[i].x > 0:
                    chosenConfs.append(i)
        #print [self.x[i].x for i in range(len(self.x))]
        csvfile = open(self.csvFileNAme, 'ab')
        writer = csv.writer(csvfile)
        xs = {i:self.x[i].x for i in range(len(self.x))}
        xs_keys_sorted = sorted(xs.keys(),key=lambda i: xs[i], reverse=True)
        top_k_xs = xs_keys_sorted[:self.trimParam]
        writer.writerow(top_k_xs)
        csvfile.close()

        self.chosenConfs = chosenConfs
        #return chosenConfs
#         return range(self.trimParam)
        return top_k_xs

        
        
        