"""
A simple model of lexical decision.
"""

import random

import pyactr as actr

environment = actr.Environment(focus_position=(320, 180))
model = actr.ACTRModel(environment=environment, subsymbolic=True, automatic_visual_search=True, activation_trace=False, retrieval_threshold=-5, latency_factor=0.13, latency_exponent=0.14, decay=0.5, eye_mvt_scaling_parameter=0.01, emma_noise=False)

actr.chunktype("goal", "state")
actr.chunktype("word", "form")

SEC_IN_YEAR = 365*24*3600
SEC_IN_TIME = 15*SEC_IN_YEAR

FREQ = {}
FREQ['nothing'] = 242*112.5
FREQ['section'] = 92*112.5
FREQ['crowd'] = 58*112.5
FREQ['bridge'] = 40.5*112.5
FREQ['knife'] = 30.6*112.5
FREQ['bunch'] = 23.4*112.5
FREQ['medium'] = 19*112.5
FREQ['subtle'] = 16*112.5
FREQ['punish'] = 13.4*112.5
FREQ['patent'] = 11.5*112.5
FREQ['denial'] = 10*112.5
FREQ['attain'] = 9*112.5
FREQ['drain'] = 7*112.5
FREQ['assault'] = 5*112.5
FREQ['disdain'] = 3*112.5
FREQ['amber'] = 1*112.5

model.productionstring(name="attend_probe", string="""
    =g>
    isa     goal
    state   'start'
    =visual_location>
    isa    _visuallocation
    ==>
    =g>
    isa     goal
    state   'recall'
    =visual_location>
    isa     _visuallocation
    +visual>
    isa     _visual
    cmd     move_attention
    screen_pos =visual_location""")

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
    ~g>
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
    ~g>
    +manual>
    isa     _manual
    cmd     press_key
    key     'F'""")

if __name__ == "__main__":
    activation_dict = {key: [] for key in FREQ}
    time_dict = {key: [] for key in FREQ}
    for lemma in FREQ:
        print(lemma)
        for _ in range(10):
            dm = model.DecMem()
            for _ in range(int(FREQ[lemma])):
                dm.add(actr.makechunk(typename="word", form=lemma), time=random.randint(-SEC_IN_TIME, 0))
            word = {1: {'text': lemma, 'position': (320, 180)}}
            retrieval = model.dmBuffer("retrieval", dm)
            g = model.goal("g", default_harvest=dm)
            g.add(actr.makechunk(nameofchunk='start', typename="goal", state='start'))
            environment.current_focus = [320,180]
            sim = model.simulation(realtime=False, gui=True, trace=False, environment_process=environment.environment_process, stimuli=word, triggers='', times=2)
            while True:
                sim.step()
                if sim.current_event.action == "START RETRIEVAL":
                    activation_dict[lemma].append(retrieval.activation)
                if sim.current_event.action == "KEY PRESSED: J":
                    time_dict[lemma].append(sim.show_time())
                    break
    for key in activation_dict.keys():
        print(key, sum(activation_dict[key])/10)
        print(key, sum(time_dict[key])/10)
