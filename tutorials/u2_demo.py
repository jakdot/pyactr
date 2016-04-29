"""
Demo - pressing a key by ACT-R model. Tutorial 2 of Lisp ACT-R.
"""

import string
import random

import pyactr.environment as env
import pyactr.model as model

class Environment(env.Environment): #subclass Environment
    """
    Environment, putting a random letter on screen.
    """

    def __init__(self):
        self.text = string.ascii_uppercase
        self.run_time = 0.3

    def environment_process(self, start_time):
        """
        Environment process. Random letter appears, model has to press the key corresponding to the letter.
        """
        time = start_time
        yield env.Event(env.roundtime(time), env._ENV, "STARTING ENVIRONMENT") 
        letter = random.sample(self.text, 1)[0]
        self.output(letter, trigger=letter) #output on environment
        time = time + self.run_time
        yield env.Event(env.roundtime(time), env._ENV, "PRINTED LETTER %s" % letter)

class Model(object):
    """
    Model pressing the right key.
    """

    def __init__(self, env):
        self.m = model.ACTRModel(environment=env)

        g = self.m.goal("g")
        g2 = self.m.goal("g2", set_delay=0.2)
        self.start = self.m.Chunk("chunk", value="start")
        self.attend_let = self.m.Chunk("chunk", value="attend_let")
        self.response = self.m.Chunk("chunk", value="response")
        self.done = self.m.Chunk("chunk", value="done")
        g.add(self.m.Chunk("read", state=self.start))

    def find_unattended_letter(self):
        yield {"=g": self.m.Chunk("read", state=self.start), "?visual": {"state": "free"}}
        yield {"=g": self.m.Chunk("read", state=self.attend_let), "+visual": None}

    def encode_letter(self):
        yield {"=g": self.m.Chunk("read", state=self.attend_let), "=visual": self.m.Chunk("_visual", object="=letter")}
        yield {"=g": self.m.Chunk("read", state=self.response), "+g2": self.m.Chunk("image", img="=letter")}

    def respond(self):
        yield {"=g": self.m.Chunk("read", state=self.response), "=g2": self.m.Chunk("image", img="=letter"), "?manual": {"state": "free"}}
        yield {"=g": self.m.Chunk("read", state=self.done), "+manual": self.m.Chunk("_manual", cmd="presskey", key="=letter")}
    
if __name__ == "__main__":
    environ = Environment()
    m = Model(environ)
    m.m.productions(m.find_unattended_letter, m.encode_letter, m.respond)
    sim = m.m.simulation(realtime=True, environment_process=environ.environment_process, start_time=0)
    sim.run(4)

