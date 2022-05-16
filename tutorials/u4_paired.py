"""
Pairing a word to a number, can be run repeatedly. It corresponds to 'paired' in Lisp ACT-R, unit 4.
"""

import random

import pyactr as actr


class Model(object):
    """
    Model pressing the right key.
    """

    def __init__(self, env, **kwargs):
        self.m = actr.ACTRModel(environment=env, **kwargs)

        actr.chunktype("pair", "probe answer")
        
        actr.chunktype("goal", "state")

        self.dm = self.m.decmem

        start = actr.makechunk(nameofchunk="start", typename="chunk", value="start")
        actr.makechunk(nameofchunk="attending", typename="chunk", value="attending")
        actr.makechunk(nameofchunk="testing", typename="chunk", value="testing")
        actr.makechunk(nameofchunk="response", typename="chunk", value="response")
        actr.makechunk(nameofchunk="study", typename="chunk", value="study")
        actr.makechunk(nameofchunk="attending_target", typename="chunk", value="attending_target")
        actr.makechunk(nameofchunk="done", typename="chunk", value="done")
        self.m.goal.add(actr.makechunk(typename="read", state=start))
        self.m.set_goal("g2")
        self.m.goals["g2"].delay=0.2

        self.m.productionstring(name="find_probe", string="""
        =g>
        isa     goal
        state   start
        ?visual_location>
        buffer  empty
        ==>
        =g>
        isa     goal
        state   attend
        ?visual_location>
        attended False
        +visual_location>
        isa _visuallocation
        screen_x 320""")
        
        self.m.productionstring(name="attend_probe", string="""
        =g>
        isa     goal
        state   attend
        =visual_location>
        isa    _visuallocation
        ?visual>
        state   free
        ==>
        =g>
        isa     goal
        state   reading
        =visual_location>
        isa     _visuallocation
        +visual>
        cmd     move_attention
        screen_pos =visual_location""")

        self.m.productionstring(name="read_probe", string="""
        =g>
        isa     goal
        state   reading
        =visual>
        isa     _visual
        value  =word
        ==>
        =g>
        isa     goal
        state   testing
        +g2>
        isa     pair
        probe   =word
        =visual>
        isa     visual
        +retrieval>
        isa     pair
        probe   =word""")

        self.m.productionstring(name="recall", string="""
        =g>
        isa     goal
        state   testing
        =retrieval>
        isa     pair
        answer  =ans
        ?manual>
        state   free
        ?visual>
        state   free
        ==>
        +manual>
        isa     _manual
        cmd     'press_key'
        key     =ans
        =g>
        isa     goal
        state   study
        ~visual>""")

        self.m.productionstring(name="cannot_recall", string="""
        =g>
        isa     goal
        state   testing
        ?retrieval>
        state   error
        ?visual>
        state   free
        ==>
        =g>
        isa     goal
        state   attending_target
        ~visual>""")
        
        self.m.productionstring(name="associate", string="""
        =g>
        isa     goal
        state   attending_target
        =visual>
        isa     _visual
        value   =val
        =g2>
        isa     pair
        probe   =word
        ?visual>
        state   free
        ==>
        =g>
        isa     goal
        state   reading
        ~visual>
        =g2>
        isa     pair
        answer  =val
        ~g2>""")

if __name__ == "__main__":
    text = {"bank": "0", "card": "1", "dart": "2", "face": "3", "game": "4",
                "hand": "5", "jack": "6", "king": "7", "lamb": "8", "mask": "9",
                "neck": "0", "pipe": "1", "quip": "2", "rope": "3", "sock": "4",
                "tent": "5", "vent": "6", "wall": "7", "xray": "8", "zinc": "9"}

    used_stim = {key: text[key] for key in random.sample(list(text), 1)}
    text = []
    for x in zip(used_stim.keys(), used_stim.values()):
        text.append({1: {'text': x[0], 'position': (320, 180)}})
        text.append({1: {'text': x[1], 'position': (320, 180)}})
    print(text)
    trigger = list(used_stim.values())
    environ = actr.Environment( focus_position=(0, 0))
    m = Model(environ, subsymbolic=True, latency_factor=0.4, decay=0.5, retrieval_threshold=-2, instantaneous_noise=0, strict_harvesting=True, automatic_visual_search=False)
    sim = m.m.simulation(realtime=True, trace=True,  gui=True, environment_process=environ.environment_process, stimuli=2*text, triggers=4*trigger,times=5)
    sim.run(12)
    print(m.dm)

