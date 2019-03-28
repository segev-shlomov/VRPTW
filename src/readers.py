class solomonFileReader:
    
    def __init__(self):
        pass
    
    def readFile(self,fileName):
        data = {}
        f = open(fileName)
        
        # problem name
        data['name'] = f.next().strip()
        # 3 blank lines
        for _ in range(3):
            f.next()
        # nTrucks and capacity
        line = f.next()
        lineData = line.strip().split()
        data["nTrucks"] = int(lineData[0])
        data["capacity"] = float(lineData[1])
        # skip 4
        for _ in range(4):
            f.next()
        # targets data
        data['targets'] = []
        for line in f:
            l = line.strip()
            if l == "":
                continue 
            lineData            = l.split()
            target = {}
            target["id"]          = int(lineData[0])
            target["x"]           = float(lineData[1])
            target["y"]           = float(lineData[2])
            target["demand"]      = float(lineData[3])
            target["start"]       = float(lineData[4])
            target["end"]         = float(lineData[5])
            target["duration"]    = float(lineData[6])
            data['targets'].append(target)
        
        f.close()
        return data