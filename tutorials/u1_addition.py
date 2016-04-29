"""
Example 2, addition. Corresponds to addition in ACT-R tutorials, Unit 1.
"""

from pyactr.model import ACTRModel

addition = ACTRModel()

addition.chunktype("countOrder", ("first", "second"))

addition.chunktype("add", ("arg1", "arg2", "sum", "count"))

dm = addition.DecMem()

for i in range(0, 11):
    dm.add(addition.Chunk("countOrder", first=i, second=i+1))

retrieval = addition.dmBuffer("retrieval", dm)
    
g = addition.goal("g")

g.add(addition.Chunk("add", arg1=5, arg2=2))

def initAddition():
    yield {"=g":addition.Chunk("add", arg1="=num1", arg2="=num2", sum=None)}
    yield {"=g":addition.Chunk("add", sum="=num1", count=0), "+retrieval": addition.Chunk("countOrder", first="=num1")}

def terminateAddition():
    yield {"=g":addition.Chunk("add", count="=num", arg2="=num", sum="=answer")}
    yield {"!g": ("clear", (0, addition.DecMem()))}

def incrementCount():
    yield {"=g":addition.Chunk("add", count="=count", sum="=sum"), "=retrieval":addition.Chunk("countOrder", first="=count", second="=newcount")}
    yield {"=g":addition.Chunk("add", count="=newcount"), "+retrieval": addition.Chunk("countOrder", first="=sum")}

def incrementSum():
    yield {"=g":addition.Chunk("add", count="=count", arg2="~=count", sum="=sum"), "=retrieval":addition.Chunk("countOrder", first="=sum", second="=newsum")}
    yield {"=g":addition.Chunk("add", sum="=newsum"), "+retrieval": addition.Chunk("countOrder", first="=count")}

addition.productions(initAddition, terminateAddition, incrementCount, incrementSum)

if __name__ == "__main__":
    x = addition.simulation()
    x.run()
