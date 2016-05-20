"""
An example using goal and retrieval. It shows strict harvesting at work and how declarative memory is updated.
"""

from pyactr.model import ACTRModel

clearing = ACTRModel()

clearing.chunktype("twoVars", ("x", "y"))

dm = clearing.DecMem()

dm.add(clearing.Chunk("twoVars", x=10, y=20))
    
retrieval = clearing.dmBuffer("retrieval", dm)
    
g = clearing.goal("g")

clearing.chunktype("reverse", ("x", "y"))
g.add(clearing.Chunk("reverse", x=10))

def start():
    yield {"=g": clearing.Chunk("reverse", x="=num", y="~=num")}
    yield {"+retrieval": clearing.Chunk("twoVars", x="=num"), "=g": clearing.Chunk("reverse", x="=num", y="=num")}
    #retrieve chunk that has the same value as x has in g; in reverse, make x and y idential
    
def switch():
    yield {"=retrieval": clearing.Chunk("reverse", x="=num", y="=num2"), "=g": clearing.Chunk("reverse", x="=num")}
    yield {"=retrieval": clearing.Chunk("twoVars", x="=num2", y="=num")}
    #clear g buffer (strict harvesting), modify retrieval chunk

def clear():
    yield {"?retrieval": {"buffer": "full"}, "?g": {"buffer": "empty"}}
    yield {"~retrieval": None}
    #clear retrieval buffer

clearing.productions(start, switch, clear)


if __name__ == "__main__":
    x = clearing.simulation()
    x.run()
    print(dm)
