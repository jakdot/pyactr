"""
Demo - pressing a key by ACT-R model. It corresponds to 'demo2' in Lisp ACT-R, unit 2.
"""

import string
import random

import pyactr as actr

stimulus = random.sample(string.ascii_uppercase, 1)[0]
text = {1: {'text': stimulus, 'position': (100,100)}}
environ = actr.Environment(focus_position=(100,100))

m = actr.ACTRModel(environment=environ, motor_prepared=True)

actr.chunktype("chunk", "value")
actr.chunktype("read", "state")
actr.chunktype("image", "img")
actr.makechunk(nameofchunk="start", typename="chunk", value="start")
actr.makechunk(nameofchunk="start", typename="chunk", value="start")
actr.makechunk(nameofchunk="attend_let", typename="chunk", value="attend_let")
actr.makechunk(nameofchunk="response", typename="chunk", value="response")
actr.makechunk(nameofchunk="done", typename="chunk", value="done")
m.goal.add(actr.chunkstring(name="reading", string="""
        isa     read
        state   start"""))
g2 = m.set_goal("g2")
g2.delay = 0.2

t2 = m.productionstring(name="encode_letter", string="""
        =g>
        isa     read
        state   start
        =visual>
        isa     _visual
        value  =letter
        ==>
        =g>
        isa     read
        state   response
        +g2>
        isa     image
        img     =letter""")

m.productionstring(name="respond", string="""
        =g>
        isa     read
        state   response
        =g2>
        isa     image
        img     =letter
        ?manual>
        state   free
        ==>
        =g>
        isa     read
        state   done
        +manual>
        isa     _manual
        cmd     'press_key'
        key     =letter""")

if __name__ == "__main__":

    sim = m.simulation(realtime=True, environment_process=environ.environment_process, stimuli=text, triggers=stimulus, times=1)
    sim.run(1)
