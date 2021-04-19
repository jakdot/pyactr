"""
Testing a simple case of production compilation. The compilation also allows for utility learning, shown in the model below, as well.
"""

import warnings

import pyactr as actr

class Compilation1(object):
    """
    Model testing compilation -- basic cases.
    """

    def __init__(self, **kwargs):
        actr.chunktype("state", "starting ending")
        self.m = actr.ACTRModel(**kwargs)

        self.m.goal.add(actr.makechunk(nameofchunk="start", typename="state", starting=1))

        self.m.productionstring(name="one", string="""
            =g>
            isa     state
            starting =x
            ending ~=x
            ==>
            =g>
            isa     state
            ending =x""", utility=2)

        self.m.productionstring(name="two", string="""
            =g>
            isa     state
            starting =x
            ending  =x
            ==>
            =g>
            isa     state
            starting  =x
            ending 4""")
        
if __name__ == "__main__":
    warnings.simplefilter("ignore")
    mm = Compilation1(production_compilation=True, utility_learning=True)

    model = mm.m

    sim = model.simulation(realtime=True)
    sim.run(0.5)
    print(model.productions["one and two"])
