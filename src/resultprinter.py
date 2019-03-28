import VRP
import readers
from gurobiHandler import vrpSolver
import xlwt

def results(files):
    reader = readers.solomonFileReader()
    book = xlwt.Workbook()
    sh = book.add_sheet("sheet")
    n=1
    print(files)
    for f in files:
        print(f)
        data = reader.readFile(f)
        vrp = VRP.VRP(data["nTrucks"], data["capacity"], data["targets"])
        confs = vrp.bfsConfBuilderWrapper(20000,20000, 15) 
        s = vrpSolver(confs, vrp)
        s.buildIP()
        sol=s.solve()
        sh.write(n, 1, sol[0])
        sh.write(n, 2, sol[1])
        n=n+1
    book.save("our_results.xls")

files = ["../data/solomon_25/C101.txt","../data/solomon_25/C102.txt","../data/solomon_25/C103.txt","../data/solomon_25/C104.txt","../data/solomon_25/C105.txt","../data/solomon_25/C106.txt","../data/solomon_25/C107.txt","../data/solomon_25/C108.txt","../data/solomon_25/C109.txt"]
#files = ("../data/solomon_25/C101.txt","../data/solomon_25/C102.txt")
results(files)
