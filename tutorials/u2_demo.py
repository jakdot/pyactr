"""
Demo - pressing a key by ACT-R model. It corresponds to 'demo2' in Lisp ACT-R, unit 2.
"""

import string
import random
import warnings

import pyactr as actr


class Environment(actr.Environment): #subclass Environment
    """
    Environment, putting a random letter on screen.
    """

    def __init__(self):
        self.text = string.ascii_uppercase
        self.run_time = 2

    def environment_process(self, start_time):
        """
        Environment process. Random letter appears, model has to press the key corresponding to the letter.
        """
        time = start_time
        yield self.Event(time, self._ENV, "STARTING ENVIRONMENT") 
        letter = random.sample(self.text, 1)[0]
        self.output(letter, trigger=letter) #output on environment
        time = time + self.run_time
        yield self.Event(time, self._ENV, "PRINTED LETTER %s" % letter)


environ = Environment()

m = actr.ACTRModel(environment=environ)

g = m.goal("g")
g2 = m.goal("g2", set_delay=0.2)
actr.chunktype("chunk", "value")
actr.chunktype("read", "state")
actr.chunktype("image", "img")
actr.makechunk(nameofchunk="start", typename="chunk", value="start")
actr.makechunk(nameofchunk="start", typename="chunk", value="start")
actr.makechunk(nameofchunk="attend_let", typename="chunk", value="attend_let")
actr.makechunk(nameofchunk="response", typename="chunk", value="response")
actr.makechunk(nameofchunk="done", typename="chunk", value="done")
g.add(actr.chunkstring(name="reading", string="""
        isa     read
        state   start"""))

t1 = m.productionstring(name="find_unattended_letter", string="""
        =g>
        isa     read
        state   start
        ?visual>
        state   free
        ==>
        =g>
        isa     read
        state   attend_let
        +visual>""")

t2 = m.productionstring(name="encode_letter", string="""
        =g>
        isa     read
        state   attend_let
        =visual>
        isa     _visual
        object  =letter
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
        cmd     'presskey'
        key     =letter""")

if __name__ == "__main__":
    sim = m.simulation(realtime=True, environment_process=environ.environment_process, start_time=0)
    sim.run(4)

