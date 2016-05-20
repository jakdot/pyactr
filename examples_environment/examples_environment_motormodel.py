"""
A simple model on motor control. This does not correspond to any tutorial model in Lisp ACT-R, it just shows some basic workings of the motor module and environment examples.
"""

import pyactr.model as model
import timed_text as env
import triggered_text as env2
import triggered_timed_text as env3

class MotorModel(object):

    def __init__(self, environment):
        self.model = model.ACTRModel(environment)

        self.g = self.model.goal("g")

        self.model.chunktype("press", "key")
        self.g.add(self.model.Chunk("press", key="a"))

    def start(self):
        yield {"=g": self.model.Chunk("press", key="=k!a")}
        yield {"+manual": self.model.Chunk("_manual", cmd="presskey", key="=k"), "=g": self.model.Chunk("press", key="b")}

    def go_on(self):
        yield {"=g": self.model.Chunk("press", key="=k!b")}
        yield {"+manual": self.model.Chunk("_manual", cmd="presskey", key="=k"), "=g": self.model.Chunk("press", key="c")}
    
    def finish(self):
        yield {"=g": self.model.Chunk("press", key="=k!c"), "?manual": {"preparation": "free"}}
        yield {"+manual": self.model.Chunk("_manual", cmd="presskey", key="=k")}

if __name__ == "__main__":
    print("############Model with no production rules###############")
    timed_text = env.Environment()
    m = MotorModel(timed_text)
    sim = m.model.simulation(realtime=True, environment_process=timed_text.environment_process, start_time=0)
    sim.run(1.5)
    
    print("############Model with production rules, environment reacting to key presses#############")
    triggered_text = env2.Environment()
    m = MotorModel(triggered_text)
    m.model.productions(m.start, m.go_on, m.finish)
    sim = m.model.simulation(realtime=True, environment_process=triggered_text.environment_process, start_time=0)
    sim.run(1)

    print("############Model with production rules, environment reacting to key presses and time#############")
    triggered_timed_text = env3.Environment()
    m = MotorModel(triggered_timed_text)
    m.model.productions(m.start, m.go_on, m.finish)
    sim = m.model.simulation(realtime=True, environment_process=triggered_timed_text.environment_process, start_time=0)
    sim.run(2)
