"""
Recalling numbers. It corresponds to 'grouped' in Lisp ACT-R, unit 5.
"""

import warnings

import pyactr.environment as env
import pyactr.model as model

class Model(object):
    """
    Model 'grouped'.
    """

    def __init__(self, **kwargs):
        self.model = model.ACTRModel(**kwargs)

        self.model.chunktype("recall_list", "group element list group_position")
        
        self.model.chunktype("group", "id parent position")
        
        self.model.chunktype("item", "name group position")

        l = self.model.Chunk("chunk", value="list")

        self.dictchunks = {1: self.model.Chunk("chunk", value="first"), 2: self.model.Chunk("chunk", value="second"),3: self.model.Chunk("chunk", value="third"), 4: self.model.Chunk("chunk", value="fourth")}
        group1 = self.model.Chunk("group", parent=l, position=self.dictchunks[1], id="group1")
        group2 = self.model.Chunk("group", parent=l, position=self.dictchunks[2], id="group2")
        group3 = self.model.Chunk("group", parent=l, position=self.dictchunks[3], id="group3")

        self.dm = self.model.DecMem(set(self.dictchunks.values()))
        self.dm.add(set([group1, group2, group3]))
        self.dm.add(l)

        self.model.set_similarities(self.dictchunks[1], self.dictchunks[2], -0.5)
        self.model.set_similarities(self.dictchunks[2], self.dictchunks[3], -0.5)

        for n in range(1,4):
            self.dm.add(self.model.Chunk("item", name=n, group=group1, position=self.dictchunks[n]))
        
        for n in range(4,7):
            self.dm.add(self.model.Chunk("item", name=n, group=group2, position=self.dictchunks[(n+1)%4]))
        
        for n in range(7,10):
            self.dm.add(self.model.Chunk("item", name=n, group=group3, position=self.dictchunks[(n+1)%7]))

        self.retrieval = self.model.dmBuffer("retrieval", self.dm, finst=15)

        g = self.model.goal("g")
        g.add(self.model.Chunk("recall_list", list=l))

        self.recalled = []

    def recall_first_group(self):
        yield {"=g": self.model.Chunk("recall_list", list="=l"), "?retrieval": {"buffer": "empty", "state": "free"}} #lack of error not encoded
        yield {"=g": self.model.Chunk("recall_list", group_position=self.dictchunks[1]), "+retrieval": self.model.Chunk("group", parent="=l", position=self.dictchunks[1])}

    def start_recall_of_group(self):
        yield {"=g": self.model.Chunk("recall_list", list="=l"), "=retrieval": self.model.Chunk("group", id="=sth"), "?retrieval": {"state": "free"}}
        yield {"=g": self.model.Chunk("recall_list", group="=retrieval", element=self.dictchunks[1]), "?retrieval": {"recently_retrieved": False}, "+retrieval": self.model.Chunk("item", group="=retrieval", position=self.dictchunks[1])}

    def harvest_first_item(self):
        yield {"=g": self.model.Chunk("recall_list", element=self.dictchunks[1], group="=group"), "=retrieval": self.model.Chunk("item", name="=name"), "?retrieval": {"state": "free"}}
        self.recalled.append(self.retrieval.copy())
        yield {"=g": self.model.Chunk("recall_list", element=self.dictchunks[2]), "?retrieval": {"recently_retrieved": False}, "+retrieval": self.model.Chunk("item", group="=group", position=self.dictchunks[2])}

    def harvest_second_item(self):
        yield {"=g": self.model.Chunk("recall_list", element=self.dictchunks[2], group="=group"), "=retrieval": self.model.Chunk("item", name="=name"), "?retrieval": {"state": "free"}}
        self.recalled.append(self.retrieval.copy())
        yield {"=g": self.model.Chunk("recall_list", element=self.dictchunks[3]), "?retrieval": {"recently_retrieved": False}, "+retrieval": self.model.Chunk("item", group="=group", position=self.dictchunks[3])}
    
    def harvest_third_item(self):
        yield {"=g": self.model.Chunk("recall_list", element=self.dictchunks[3], group="=group"), "=retrieval": self.model.Chunk("item", name="=name"), "?retrieval": {"state": "free"}}
        self.recalled.append(self.retrieval.copy())
        yield {"=g": self.model.Chunk("recall_list", element=self.dictchunks[4]), "?retrieval": {"recently_retrieved": False}, "+retrieval": self.model.Chunk("item", group="=group", position=self.dictchunks[4])}

    def recall_second_group(self):
        yield {"=g": self.model.Chunk("recall_list", group_position=self.dictchunks[1], list="=l"), "?retrieval": {"state": "error"}}
        yield {"=g": self.model.Chunk("recall_list", group_position=self.dictchunks[2]), "+retrieval": self.model.Chunk("group", parent="=l", position=self.dictchunks[2])}

    def recall_third_group(self):
        yield {"=g": self.model.Chunk("recall_list", group_position=self.dictchunks[2], list="=l"), "?retrieval": {"state": "error"}}
        yield {"=g": self.model.Chunk("recall_list", group_position=self.dictchunks[3]), "+retrieval": self.model.Chunk("group", parent="=l", position=self.dictchunks[3])}

if __name__ == "__main__":
    warnings.simplefilter("ignore")
    m = Model(subsymbolic=True, instantaneous_noise=0.15, retrieval_threshold=-0.5, partial_matching=True, activation_trace=True)
    m.model.productions(m.recall_first_group, m.start_recall_of_group, m.harvest_first_item, m.harvest_second_item, m.harvest_third_item, m.recall_second_group, m.recall_third_group)
    sim = m.model.simulation(realtime=False)
    sim.run(20)
    for x in m.recalled:
        print(x.pop().name)

