"""
Fan experiment, unit5.
"""

import pyactr.model as model

class Model(object):
    """
    Model for fan experiment. We will abstract away from enviornment, key presses and visual module (the same is done in the abstract model of Lisp ACT-R).
    """

    def __init__(self, person, location, **kwargs):
        self.model = model.ACTRModel(environment=None, **kwargs)

        self.model.chunktype("comprehend", "relation arg1 arg2")
        self.model.chunktype("meaning", "word")

        dict_dm = {}
        words = "hippie bank fireman lawyer guard beach castle dungeon earl forest giant park church captain cave debutante store in".split()

        for word in words:
            dict_dm[word] = self.model.Chunk("meaning", word=word)

        for idx, word in enumerate("park church bank".split(), start=1):
            dict_dm[idx] = self.model.Chunk("comprehend", relation=dict_dm["in"], arg1=dict_dm["hippie"], arg2=dict_dm[word])
            print(idx, word)
        
        for idx, word in enumerate("park cave".split(), start=4):
            dict_dm[idx] = self.model.Chunk("comprehend", relation=dict_dm["in"], arg1=dict_dm["captain"], arg2=dict_dm[word])
        
        dict_dm[6] = self.model.Chunk("comprehend", relation=dict_dm["in"], arg1=dict_dm["debutante"], arg2=dict_dm["bank"])
        dict_dm[7] = self.model.Chunk("comprehend", relation=dict_dm["in"], arg1=dict_dm["fireman"], arg2=dict_dm["park"])

        for idx, word in enumerate("beach castle dungeon".split(), start=8):
            dict_dm[idx] = self.model.Chunk("comprehend", relation=dict_dm["in"], arg1=dict_dm["giant"], arg2=dict_dm[word])
        
        for idx, word in enumerate("castle forest".split(), start=11):
            dict_dm[idx] = self.model.Chunk("comprehend", relation=dict_dm["in"], arg1=dict_dm["earl"], arg2=dict_dm[word])
        dict_dm[13] = self.model.Chunk("comprehend", relation=dict_dm["in"], arg1=dict_dm["lawyer"], arg2=dict_dm["store"])

        self.dm = self.model.DecMem(set(dict_dm.values()))
        
        self.retrieval = self.model.dmBuffer("retrieval", self.dm)

        self.harvest_person = self.model.Chunk("chunk", value="harvest_person")
        self.harvest_location = self.model.Chunk("chunk", value="harvest_location")
        self.test = self.model.Chunk("chunk", value="test")
        self.get_retrieval = self.model.Chunk("chunk", value="get_retrieval")
        self.get_retrieval = self.model.Chunk("chunk", value="get_retrieval")

        self.model.chunktype("sentence_goal", "arg1 arg2 state")
        g = self.model.goal("g")
        g.add(self.model.Chunk("sentence_goal", arg1=person, arg2=location, state=self.test))

    def start(self):
        yield {"=g": self.model.Chunk("sentence_goal", arg1="=person", state=self.test)}
        yield {"=g": self.model.Chunk("sentence_goal", state=self.harvest_person), "+retrieval": self.model.Chunk("meaning", word="=person")}

    def harvesting_person(self):
        yield {"=g": self.model.Chunk("sentence_goal", arg2="=location", state=self.harvest_person), "=retrieval": self.model.Chunk("nonempty")}
        yield {"=g": self.model.Chunk("sentence_goal", state=self.harvest_location, arg1="=retrieval"), "+retrieval": self.model.Chunk("meaning", word="=location")}
        
    def harvesting_location(self):
        yield {"=g": self.model.Chunk("sentence_goal", state=self.harvest_location), "=retrieval": self.model.Chunk("nonempty"), "?retrieval": {"state": "free"}}
        yield {"=g": self.model.Chunk("sentence_goal", state=self.get_retrieval, arg2="=retrieval")}

    def retrieve_from_person(self):
        yield {"=g": self.model.Chunk("sentence_goal", state=self.get_retrieval, arg1="=person")}
        yield {"=g": self.model.Chunk("sentence_goal", state=None), "+retrieval": self.model.Chunk("comprehend", arg1="=person")}

    def retrieve_from_location(self):
        yield {"=g": self.model.Chunk("sentence_goal", state=self.get_retrieval, arg2="=location")}
        yield {"=g": self.model.Chunk("sentence_goal", state=None), "+retrieval": self.model.Chunk("comprehend", arg2="=location")}

    def respond_yes(self):
        yield {"=g": self.model.Chunk("sentence_goal", state=None, arg1="=person", arg2="=location"), "=retrieval": self.model.Chunk("comprehend", arg1="=person", arg2="=location")}
        yield {"=g": self.model.Chunk("sentence_goal", state="k")}

    def mismatch_person_no(self):
        yield {"=g": self.model.Chunk("sentence_goal", state=None, arg1="=person", arg2="=location"), "=retrieval": self.model.Chunk("comprehend", arg1="~=person")}
        yield {"=g": self.model.Chunk("sentence_goal", state="d")}

    def mismatch_location_no(self):
        yield {"=g": self.model.Chunk("sentence_goal", state=None, arg1="=person", arg2="=location"), "=retrieval": self.model.Chunk("comprehend", arg2="~=location")}
        yield {"=g": self.model.Chunk("sentence_goal", state="d")}

if __name__ == "__main__":
    m = Model("hippie", "bank", subsymbolic=True, latency_factor=0.63, strength_of_association=1.6, buffer_spreading_activation={"g":1}, activation_trace=True)
    m.model.productions(m.start, m.harvesting_person, m.harvesting_location, m.retrieve_from_person, m.retrieve_from_location, m.respond_yes, m.mismatch_person_no, m.mismatch_location_no)
    sim = m.model.simulation(realtime=True)
    sim.run(3)
