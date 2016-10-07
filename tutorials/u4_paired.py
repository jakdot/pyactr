"""
Pairing a word to a number, can be run repeatedly. It corresponds to 'paired' in Lisp ACT-R, unit 4.
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
        self.text = {"bank": "0", "card": "1", "dart": "2", "face": "3", "game": "4",
                "hand": "5", "jack": "6", "king": "7", "lamb": "8", "mask": "9",
                "neck": "0", "pipe": "1", "quip": "2", "rope": "3", "sock": "4",
                "tent": "5", "vent": "6", "wall": "7", "xray": "8", "zinc": "9"}
        self.run_time = 5

    def environment_process(self, number_pairs, number_trials, start_time=0):
        """
        Environment process. Random letter appears, model has to press the key corresponding to the letter.
        """
        used_text = {key: self.text[key] for key in random.sample(list(self.text), number_pairs)}

        time = start_time
        yield self.Event(time, self._ENV, "STARTING ENVIRONMENT")
        for _ in range(number_trials):
           for word in used_text: 
                self.output(word, trigger=used_text[word]) #output on environment
                time += self.run_time
                yield self.Event(time, self._ENV, "PRINTED WORD %s" % word)
                self.output(used_text[word]) #output on environment
                time += self.run_time
                yield self.Event(time, self._ENV, "PRINTED NUMBER %s" % used_text[word])

class Model(object):
    """
    Model pressing the right key.
    """

    def __init__(self, env, **kwargs):
        self.m = actr.ACTRModel(environment=env, **kwargs)

        actr.chunktype("pair", "probe answer")
        
        actr.chunktype("goal", "state")

        self.dm = self.m.DecMem()

        retrieval = self.m.dmBuffer("retrieval", self.dm)

        g = self.m.goal("g")
        self.m.goal("g2", set_delay=0.2)
        start = actr.makechunk(nameofchunk="start", typename="chunk", value="start")
        actr.makechunk(nameofchunk="attending", typename="chunk", value="attending")
        actr.makechunk(nameofchunk="testing", typename="chunk", value="testing")
        actr.makechunk(nameofchunk="response", typename="chunk", value="response")
        actr.makechunk(nameofchunk="study", typename="chunk", value="study")
        actr.makechunk(nameofchunk="attending_target", typename="chunk", value="attending_target")
        actr.makechunk(nameofchunk="done", typename="chunk", value="done")
        g.add(actr.makechunk(typename="read", state=start))

        self.m.productionstring(name="attend_probe", string="""
        =g>
        isa     goal
        state   start
        ?visual>
        state   auto_buffering
        ==>
        =g>
        isa     goal
        state   attending
        +visual>""")

        self.m.productionstring(name="read_probe", string="""
        =g>
        isa     goal
        state   attending
        =visual>
        isa     _visual
        object  =word
        ==>
        =g>
        isa     goal
        state   testing
        +g2>
        isa     pair
        probe   =word
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
        cmd     'presskey'
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
        state   study
        ~visual>""")

        self.m.productionstring(name="study_answer", string="""
        =g>
        isa     goal
        state   study
        ?visual>
        state   auto_buffering
        ==>
        =g>
        isa     goal
        state   attending_target
        +visual>""")

        self.m.productionstring(name="associate", string="""
        =g>
        isa     goal
        state   attending_target
        =visual>
        isa     _visual
        object  =val
        =g2>
        isa     pair
        probe   =word
        ?visual>
        state   free
        ==>
        =g>
        isa     goal
        state   start
        ~visual>
        =g2>
        isa     pair
        answer  =val
        ~g2>""")

if __name__ == "__main__":
    environ = Environment()
    m = Model(environ, subsymbolic=True, latency_factor=0.4, decay=0.5, retrieval_threshold=-2, instantaneous_noise=0, strict_harvesting=True)
    sim = m.m.simulation(realtime=True, environment_process=environ.environment_process, number_pairs=1, number_trials=2, start_time=0)
    sim.run(12)
    print(m.dm)

