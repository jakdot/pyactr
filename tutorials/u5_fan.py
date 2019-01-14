"""
The fan experiment from unit 5 of Lisp ACT-R.
"""

import warnings

import pyactr as actr

class Model(object):
    """
    Model for fan experiment. We will abstract away from enviornment, key presses and visual module (the same is done in the abstract model of Lisp ACT-R).
    """

    def __init__(self, person, location, **kwargs):
        self.model = actr.ACTRModel(environment=None, **kwargs)

        actr.chunktype("comprehend", "relation arg1 arg2")
        actr.chunktype("meaning", "word")

        dict_dm = {}
        words = "hippie bank fireman lawyer guard beach castle dungeon earl forest giant park church captain cave debutante store in".split()

        for word in words:
            dict_dm[word] = actr.makechunk(nameofchunk=word, typename="meaning", word=word)

        for idx, word in enumerate("park church bank".split(), start=1):
            dict_dm[idx] = actr.makechunk(nameofchunk=idx, typename="comprehend", relation=dict_dm["in"], arg1=dict_dm["hippie"], arg2=dict_dm[word])
            print(idx, word)
        
        for idx, word in enumerate("park cave".split(), start=4):
            dict_dm[idx] = actr.makechunk(nameofchunk=idx, typename="comprehend", relation=dict_dm["in"], arg1=dict_dm["captain"], arg2=dict_dm[word])
        
        dict_dm[6] = actr.makechunk(nameofchunk=6, typename="comprehend", relation=dict_dm["in"], arg1=dict_dm["debutante"], arg2=dict_dm["bank"])
        dict_dm[7] = actr.makechunk(nameofchunk=7, typename="comprehend", relation=dict_dm["in"], arg1=dict_dm["fireman"], arg2=dict_dm["park"])

        for idx, word in enumerate("beach castle dungeon".split(), start=8):
            dict_dm[idx] = actr.makechunk(nameofchunk=idx, typename="comprehend", relation=dict_dm["in"], arg1=dict_dm["giant"], arg2=dict_dm[word])
        
        for idx, word in enumerate("castle forest".split(), start=11):
            dict_dm[idx] = actr.makechunk(nameofchunk=idx, typename="comprehend", relation=dict_dm["in"], arg1=dict_dm["earl"], arg2=dict_dm[word])
        dict_dm[13] = actr.makechunk(nameofchunk=idx, typename="comprehend", relation=dict_dm["in"], arg1=dict_dm["lawyer"], arg2=dict_dm["store"])

        self.model.set_decmem(set(dict_dm.values()))
        self.dm = self.model.decmem
        
        self.harvest_person = actr.makechunk(nameofchunk="harvest_person", typename="chunk", value="harvest_person")
        self.harvest_location = actr.makechunk(nameofchunk="harvest_location", typename="chunk", value="harvest_location")
        self.test = actr.makechunk(nameofchunk="test", typename="chunk", value="test")
        self.get_retrieval = actr.makechunk(nameofchunk="get_retrieval", typename="chunk", value="get_retrieval")

        actr.chunktype("sentence_goal", "arg1 arg2 state")
        self.model.goal.add(actr.makechunk(typename="sentence_goal", arg1=person, arg2=location, state=self.test))

        self.model.productionstring(name="start", string="""
        =g>
        isa     sentence_goal
        arg1    =person
        state   test
        ==>
        =g>
        isa     sentence_goal
        state   harvest_person
        +retrieval>
        isa     meaning
        word    =person""")

        self.model.productionstring(name="harvesting_person", string="""
        =g>
        isa     sentence_goal
        arg2    =location
        state   harvest_person
        =retrieval>
        isa     nonempty
        ==>
        =g>
        isa     sentence_goal
        state   harvest_location
        arg1    =retrieval
        +retrieval>
        isa     meaning
        word    =location""")

        self.model.productionstring(name="harvesting_location", string="""
        =g>
        isa     sentence_goal
        state   harvest_location
        =retrieval>
        isa     nonempty
        ?retrieval>
        state   free
        ==>
        =g>
        isa     sentence_goal
        state   get_retrieval
        arg2    =retrieval""")

        self.model.productionstring(name="retrieve_from_person", string="""
        =g>
        isa     sentence_goal
        state   get_retrieval
        arg1    =person
        ==>
        =g>
        isa     sentence_goal
        state   None
        +retrieval>
        isa     comprehend
        arg1    =person""")

        self.model.productionstring(name="retrieve_from_location", string="""
        =g>
        isa     sentence_goal
        state   get_retrieval
        arg2    =location
        ==>
        =g>
        isa     sentence_goal
        state   None
        +retrieval>
        isa     comprehend
        arg2    =location""")

        self.model.productionstring(name="respond_yes", string="""
        =g>
        isa     sentence_goal
        state   None
        arg1    =person
        arg2    =location
        =retrieval>
        isa     comprehend
        arg1    =person
        arg2    =location
        ==>
        =g>
        isa     sentence_goal
        state   'k'""")

        self.model.productionstring(name="mismatch_person_no", string="""
        =g>
        isa     sentence_goal
        state   None
        arg1    =person
        arg2    =location
        =retrieval>
        isa     comprehend
        arg1    ~=person
        ==>
        =g>
        isa     sentence_goal
        state   'd'""")

        t3= self.model.productionstring(name="mismatch_location_no", string="""
        =g>
        isa     sentence_goal
        state   None
        arg1    =person
        arg2    =location
        =retrieval>
        isa     comprehend
        arg2    ~=location
        ==>
        =g>
        isa     sentence_goal
        state   'd'""")

if __name__ == "__main__":
    warnings.simplefilter("ignore")
    m = Model("hippie", "bank", subsymbolic=True, latency_factor=0.63, strength_of_association=1.6, buffer_spreading_activation={"g":1}, activation_trace=True, strict_harvesting=True)
    sim = m.model.simulation(realtime=True)
    sim.run(2)
