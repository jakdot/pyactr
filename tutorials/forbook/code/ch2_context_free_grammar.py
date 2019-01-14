"""
CFG for the a^n b^n language.
"""

import pyactr as actr

cfg = actr.ACTRModel()

actr.chunktype("countOrder", "first, second")
actr.chunktype("countFrom", ("start", "end", "count", "terminal"))

dm = cfg.decmem
dm.add(actr.chunkstring(string="""
    isa         countOrder
    first       1
    second      2
"""))
dm.add(actr.chunkstring(string="""
    isa         countOrder
    first       2
    second      3
"""))
dm.add(actr.chunkstring(string="""
    isa         countOrder
    first       3
    second      4
"""))
dm.add(actr.chunkstring(string="""
    isa         countOrder
    first       4
    second      5
"""))

cfg.goal.add(actr.chunkstring(string="""
    isa         countFrom
    start       1
    end         3
    terminal    'a'
"""))

cfg.productionstring(name="start", string="""
    =g>
    isa         countFrom
    start       =x
    count       None
    ==>
    =g>
    isa         countFrom
    count       =x
    +retrieval>
    isa         countOrder
    first       =x
""")

cfg.productionstring(name="increment", string="""
    =g>
    isa         countFrom
    count       =x
    end         ~=x
    =retrieval>
    isa         countOrder
    first       =x
    second      =y
    ==>
    !g>
    show        terminal
    =g>
    isa         countFrom
    count       =y
    +retrieval>
    isa         countOrder
    first       =y
""")

cfg.productionstring(name="restart counting", string="""
    =g>
    isa         countFrom
    count       =x
    end         =x
    terminal    'a'
    ==>
    +g>
    isa         countFrom
    start       1
    end         =x
    terminal    'b'
""")

if __name__ == "__main__":
    cfg_sim = cfg.simulation(trace=False)
    cfg_sim.run()
