"""
A simple model of lexical decision.
"""

import pyactr as actr

environment = actr.Environment(focus_position=(0,0))
lex_decision = actr.ACTRModel(environment=environment,
                              automatic_visual_search=False)

actr.chunktype("goal", "state")
actr.chunktype("word", "form")

dm = lex_decision.decmem
for string in {"elephant", "dog", "crocodile"}:
    dm.add(actr.makechunk(typename="word", form=string))

g = lex_decision.goal
g.add(actr.makechunk(nameofchunk="start",
                     typename="goal",
                     state="start"))

lex_decision.productionstring(name="find word", string="""
    =g>
    isa     goal
    state   'start'
    ?visual_location>
    buffer  empty
    ==>
    =g>
    isa     goal
    state   'attend'
    +visual_location>
    isa _visuallocation
    screen_x closest
""")

lex_decision.productionstring(name="attend word", string="""
    =g>
    isa     goal
    state   'attend'
    =visual_location>
    isa    _visuallocation
    ?visual>
    state   free
    ==>
    =g>
    isa     goal
    state   'retrieving'
    +visual>
    isa     _visual
    cmd     move_attention
    screen_pos =visual_location
    ~visual_location>
""")

lex_decision.productionstring(name="retrieving", string="""
    =g>
    isa     goal
    state   'retrieving'
    =visual>
    isa     _visual
    value   =val
    ==>
    =g>
    isa     goal
    state   'retrieval_done'
    +retrieval>
    isa     word
    form    =val
""")

lex_decision.productionstring(name="lexeme retrieved", string="""
    =g>
    isa     goal
    state   'retrieval_done'
    ?retrieval>
    buffer  full
    state   free
    ==>
    =g>
    isa     goal
    state   'done'
    +manual>
    isa     _manual
    cmd     press_key
    key     'J'
""")

lex_decision.productionstring(name="no lexeme found", string="""
    =g>
    isa     goal
    state   'retrieval_done'
    ?retrieval>
    buffer  empty
    state   error
    ==>
    =g>
    isa     goal
    state   'done'
    +manual>
    isa     _manual
    cmd     press_key
    key     'F'
""")

word = {1: {'text': 'elephant', 'position': (320, 180)}}

if __name__ == "__main__":
    lex_dec_sim = lex_decision.simulation(realtime=True, gui=False,
                      environment_process=environment.environment_process,
                      stimuli=word, triggers='', times=1)
    lex_dec_sim.run()
