"""
Recalling numbers. It corresponds to 'grouped' in Lisp ACT-R, unit 5.
"""

import warnings

import pyactr as actr

class Model(object):
    """
    Model 'grouped'.
    """

    def __init__(self, **kwargs):
        self.model = actr.ACTRModel(**kwargs)

        actr.chunktype("recall_list", "group element list group_position")
        
        actr.chunktype("group", "id parent position")
        
        actr.chunktype("item", "name group position")

        li = actr.makechunk(typename="chunk", value="list")

        self.dictchunks = {1: actr.makechunk(nameofchunk="p1", typename="chunk", value="first"), 2: actr.makechunk(nameofchunk="p2", typename="chunk", value="second"), 3: actr.makechunk(nameofchunk="p3", typename="chunk", value="third"), 4: actr.makechunk(nameofchunk="p4", typename="chunk", value="fourth")}
        group1 = actr.makechunk(nameofchunk="group1", typename="group", parent=li, position=self.dictchunks[1], id="group1")
        group2 = actr.makechunk(nameofchunk="group2", typename="group", parent=li, position=self.dictchunks[2], id="group2")
        group3 = actr.makechunk(nameofchunk="group3", typename="group", parent=li, position=self.dictchunks[3], id="group3")

        self.model.set_decmem(set(self.dictchunks.values()))
        self.dm = self.model.decmem
        self.dm.add(set([group1, group2, group3]))
        self.dm.add(li)

        self.model.set_similarities(self.dictchunks[1], self.dictchunks[2], -0.5)
        self.model.set_similarities(self.dictchunks[2], self.dictchunks[3], -0.5)

        for n in range(1,4):
            self.dm.add(actr.makechunk(typename="item", name=n, group=group1, position=self.dictchunks[n]))
        
        for n in range(4,7):
            self.dm.add(actr.makechunk(typename="item", name=n, group=group2, position=self.dictchunks[(n+1)%4]))
        
        for n in range(7,10):
            self.dm.add(actr.makechunk(typename="item", name=n, group=group3, position=self.dictchunks[(n+1)%7]))

        self.model.retrieval.finst = 15

        self.model.goal.add(actr.makechunk(typename="recall_list", list=li))

        self.model.productionstring(name="recall_first_group", string="""
        =g>
        isa     recall_list
        list    =l
        ?retrieval>
        buffer  empty
        state   free
        ==>
        =g>
        isa     recall_list
        group_position p1
        +retrieval>
        isa     group
        parent  =l
        position    p1""")

        self.model.productionstring(name="start_recall_of_group", string="""
        =g>
        isa     recall_list
        list    =l
        =retrieval>
        isa     group
        id      =sth
        ?retrieval>
        state   free
        ==>
        =g>
        isa     recall_list
        group   =retrieval
        element p1
        ?retrieval>
        recently_retrieved False
        +retrieval>
        isa     item
        group   =retrieval
        position p1""")

        self.model.productionstring(name="harvest_first_item", string="""
        =g>
        isa     recall_list
        element p1
        group   =group
        =retrieval>
        isa     item
        name    =name
        ?retrieval>
        state   free
        ==>
        =g>
        isa     recall_list
        element p2
        ?retrieval>
        recently_retrieved False
        +retrieval>
        isa     item
        group   =group
        position p2""")
        
        self.model.productionstring(name="harvest_second_item", string="""
        =g>
        isa     recall_list
        element p2
        group   =group
        =retrieval>
        isa     item
        name    =name
        ?retrieval>
        state   free
        ==>
        =g>
        isa     recall_list
        element p3
        ?retrieval>
        recently_retrieved False
        +retrieval>
        isa     item
        group   =group
        position p3""")

        self.model.productionstring(name="harvest_third_item", string="""
        =g>
        isa     recall_list
        element p3
        group   =group
        =retrieval>
        isa     item
        name    =name
        ?retrieval>
        state   free
        ==>
        =g>
        isa     recall_list
        element p4
        ?retrieval>
        recently_retrieved False
        +retrieval>
        isa     item
        group   =group
        position p4""")

        self.model.productionstring(name="recall_second_group", string="""
        =g>
        isa     recall_list
        group_position p1
        list    =l
        ?retrieval>
        state   error
        ==>
        =g>
        isa     recall_list
        group_position p2
        +retrieval>
        isa     group
        parent  =l
        position    p2""")

        self.model.productionstring(name="recall_third_group", string="""
        =g>
        isa     recall_list
        group_position p2
        list    =l
        ?retrieval>
        state   error
        ==>
        =g>
        isa     recall_list
        group_position p3
        +retrieval>
        isa     group
        parent  =l
        position    p3""")

if __name__ == "__main__":
    warnings.simplefilter("ignore")
    m = Model(subsymbolic=True, instantaneous_noise=0.15, retrieval_threshold=-10, partial_matching=True, activation_trace=True, strict_harvesting=True)
    sim = m.model.simulation(realtime=False)
    sim.run(3)

