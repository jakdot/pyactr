"""
A basic model of grammar.
"""

import pyactr as actr

regular_grammar = actr.ACTRModel()

actr.chunktype("goal_chunk", "mother daughter1 daughter2 state")

dm = regular_grammar.decmem

regular_grammar.goal.add(actr.chunkstring(string="""
    isa         goal_chunk
    mother      'NP'
    state       rule
"""))

regular_grammar.productionstring(name="NP ==> N NP", string="""
    =g>
    isa         goal_chunk
    mother      'NP'
    daughter1   None
    daughter2   None
    state       rule
    ==>
    =g>
    isa         goal_chunk
    daughter1   'N'
    daughter2   'NP'
    state       show
""")

regular_grammar.productionstring(name="print N", string="""
    =g>
    isa         goal_chunk
    state       show
    ==>
    !g>
    show        daughter1
    =g>
    isa         goal_chunk
    state       rule
""")

regular_grammar.productionstring(name="get new mother", string="""
    =g>
    isa         goal_chunk
    daughter2   =x
    daughter2   ~None
    state       rule
    ==>
    =g>
    isa         goal_chunk
    mother      =x
    daughter1   None
    daughter2   None
""")

regular_grammar_sim = regular_grammar.simulation(trace=False)
regular_grammar_sim.run(2)
