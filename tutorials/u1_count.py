"""
An example of a model using retrieval and goal buffers. It corresponds to the simplest model in ACT-R tutorials, Unit 1, 'count'.
"""

from pyactr.model import ACTRModel

counting = ACTRModel()

#Each chunk type should be defined first.
counting.chunktype("countOrder", ("first", "second"))
#Chunk type is defined as (name, attributes)

#Attributes are written as an iterable (above) or as a string, separated by comma:
counting.chunktype("countOrder", "first, second")

dm = counting.DecMem()
#this creates declarative memory

for i in range(1, 6):
    dm.add(counting.Chunk("countOrder", first=i, second=i+1))
    #adding chunks to declarative memory

retrieval = counting.dmBuffer("retrieval", dm)
#creating buffer for dm
    
g = counting.goal("g")
#creating goal buffer

counting.chunktype("countFrom", ("start", "end", "count"))
g.add(counting.Chunk("countFrom", start=2, end=4))
#adding stuff to goal buffer

    
#production rules follow; they are generator functions: first yield yields buffer tests, the second yield yields buffer changes; in other words, the first yield corresponds to LHS, the second yield is RHS in ACT-R
def start():
    yield {"=g":counting.Chunk("countFrom", start="=x", count=None)}
    yield {"=g":counting.Chunk("countFrom", count="=x"),\
            "+retrieval": counting.Chunk("countOrder", first="=x")}

#this rule would look as follows in Lisp ACT-R:
#(p start
#=goal>
#  ISA         countFrom
#  start       =x
#  count       nil
#==>
#=goal>
#  ISA         countFrom
#  count       =x
#+retrieval>
#  ISA         countOrder
#  first       =x
#)

def increment():
    yield {"=g":counting.Chunk("countFrom", count="=x", end="~=x"),\
            "=retrieval": counting.Chunk("countOrder", first="=x", second="=y")}
    yield {"=g":counting.Chunk("countFrom", count="=y"),\
            "+retrieval": counting.Chunk("countOrder", first="=y")}

def stop():
    yield {"=g":counting.Chunk("countFrom", count=counting.Chunk("_variablesvalues", variables="x"), end="=x")}
    yield {"!g": ("clear", (0, counting.DecMem()))}

counting.productions(start, increment, stop)

if __name__ == "__main__":
    x = counting.simulation()
    x.run()

