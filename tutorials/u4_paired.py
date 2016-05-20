"""
Pairing a word to a number, can be run repeatedly. It corresponds to 'paired' in Lisp ACT-R, unit 4.
"""

import string
import random
import warnings

import pyactr.environment as env
import pyactr.model as model

class Environment(env.Environment): #subclass Environment
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
        yield env.Event(env.roundtime(time), env._ENV, "STARTING ENVIRONMENT")
        for _ in range(number_trials):
           for word in used_text: 
                self.output(word, trigger=used_text[word]) #output on environment
                time += self.run_time
                yield env.Event(env.roundtime(time), env._ENV, "PRINTED WORD %s" % word)
                self.output(used_text[word]) #output on environment
                time += self.run_time
                yield env.Event(env.roundtime(time), env._ENV, "PRINTED NUMBER %s" % used_text[word])

class Model(object):
    """
    Model pressing the right key.
    """

    def __init__(self, env, **kwargs):
        self.m = model.ACTRModel(environment=env, **kwargs)

        self.m.chunktype("pair", "probe answer")
        
        self.m.chunktype("goal", "state")

        self.dm = self.m.DecMem()

        self.m.dmBuffer("retrieval", self.dm)

        g = self.m.goal("g")
        self.m.goal("g2", set_delay=0.2)
        self.start = self.m.Chunk("chunk", value="start")
        self.attending = self.m.Chunk("chunk", value="attending")
        self.testing = self.m.Chunk("chunk", value="testing")
        self.response = self.m.Chunk("chunk", value="response")
        self.study = self.m.Chunk("chunk", value="study")
        self.attending_target = self.m.Chunk("chunk", value="attending_target")
        self.done = self.m.Chunk("chunk", value="done")
        g.add(self.m.Chunk("read", state=self.start))

    def attend_probe(self):
        yield {"=g": self.m.Chunk("goal", state=self.start), "?visual": {"state": "auto_buffering"}}
        yield {"=g": self.m.Chunk("goal", state=self.attending), "+visual": None}

    def read_probe(self):
        yield {"=g": self.m.Chunk("goal", state=self.attending), "=visual": self.m.Chunk("_visual", object="=word")}
        yield {"=g": self.m.Chunk("goal", state=self.testing), "+g2": self.m.Chunk("pair", probe="=word"), "+retrieval": self.m.Chunk("pair", probe="=word")}

    def recall(self):
        yield {"=g": self.m.Chunk("goal", state=self.testing), "=retrieval": self.m.Chunk("pair", answer="=ans"), "?manual": {"state": "free"},  "?visual": {"state": "free"}}
        yield {"+manual": self.m.Chunk("_manual", cmd="presskey", key="=ans"), "=g": self.m.Chunk("goal", state=self.study), "~visual": None}

    def cannot_recall(self):
        yield {"=g": self.m.Chunk("goal", state=self.testing), "?retrieval": {"state": "error"}, "?visual": {"state": "free"}}
        yield {"=g": self.m.Chunk("goal", state=self.study), "~visual": None}

    def study_answer(self):
        yield {"=g": self.m.Chunk("goal", state=self.study), "?visual": {"state": "auto_buffering"}}
        yield {"=g": self.m.Chunk("goal", state=self.attending_target), "+visual": None}

    def associate(self):
        yield {"=g": self.m.Chunk("goal", state=self.attending_target), "=visual": self.m.Chunk("_visual", object="=val"), "=g2": self.m.Chunk("pair", probe="=word"), "?visual": {"state": "free"}}
        yield {"=g": self.m.Chunk("goal", state=self.start), "~visual": None, "=g2": self.m.Chunk("pair", answer="=val"), "~g2": None}

if __name__ == "__main__":
    warnings.simplefilter("ignore")
    environ = Environment()
    m = Model(environ, subsymbolic=True, latency_factor=0.4, decay=0.5, retrieval_threshold=-2, instantaneous_noise=0)
    m.m.productions(m.attend_probe, m.read_probe, m.recall, m.cannot_recall, m.study_answer, m.associate)
    sim = m.m.simulation(realtime=True, environment_process=environ.environment_process, number_pairs=1, number_trials=2, start_time=0)
    sim.run(12)
    print(m.dm)

