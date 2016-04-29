"""
Testing utilities of production rules and changes in utilities.
"""

import pyactr.environment as env
import pyactr.model as model

class Model(object):
    """
    Model pressing the right key.
    """

    def __init__(self, **kwargs):
        self.m = model.ACTRModel(**kwargs)

        self.dm = self.m.DecMem()

        self.m.dmBuffer("retrieval", self.dm)

        g = self.m.goal("g")
        g.add(self.m.Chunk("start", state="start"))

    def one(self, utility=1):
        yield {"=g": self.m.Chunk("start", state="start")}
        yield {"=g": self.m.Chunk("change", state="change")}

    def two(self, utility=5):
        yield {"=g": self.m.Chunk("start", state="start")}
        yield {"=g": self.m.Chunk("dontchange", state="start")}
    
    def three(self, reward=10):
        yield {"=g": self.m.Chunk("change", state="change")}
        yield {"~g": None}

if __name__ == "__main__":
    m = Model(subsymbolic=True, utility_noise=10, utility_learning=True)
    m.m.productions(m.one, m.two, m.three)
    sim = m.m.simulation(realtime=True)
    print(m.m._ACTRModel__Productions)
    sim.run(1)
    print(m.m._ACTRModel__Productions)
    print(m.dm)

