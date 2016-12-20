"""
A simple model of lexical decision.
"""

import pyactr as actr

environment = actr.Environment(focus_position=(0,0))
model = actr.ACTRModel(environment=environment, automatic_visual_search=False)

actr.chunktype("goal", "state")
actr.chunktype("word", "form")
    
dm = model.decmem
for i in {"elephant", "dog", "crocodile"}:
    dm.add(actr.makechunk(typename="word", form=i))

model.goal.add(actr.makechunk(nameofchunk='start', typename="goal", state='start'))

model.productionstring(name="find_word", string="""
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
    screen_x closest""")

model.productionstring(name="attend_probe", string="""
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
    state   'recall'
    +visual>
    isa     _visual
    cmd     move_attention
    screen_pos =visual_location
    ~visual_location>""")

model.productionstring(name="prepare_retrieving", string="""
    =g>
    isa     goal
    state   'recall'
    =visual>
    isa     _visual
    value   =val
    ==>
    =g>
    isa     goal
    state   'retrieving'
    word    =val""")

model.productionstring(name="retrieving", string="""
    =g>
    isa     goal
    state   'retrieving'
    word    =val
    ==>
    =g>
    isa     goal
    state   'retrieval_done'
    +retrieval>
    isa     word
    form    =val""")

model.productionstring(name="can_recall", string="""
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
    key     'J'""")

model.productionstring(name="cannot_recall", string="""
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
    key     'F'""")

word = {1: {'text': 'elephant', 'position': (320, 180)}}

if __name__ == "__main__":
    sim = model.simulation(realtime=True, gui=True, environment_process=environment.environment_process, stimuli=word, triggers='', times=1)
    sim.run(2)

