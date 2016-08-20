"""
Models testing symbolic system of ACT-R.
"""

import pyactr as actr

class Counting(object):

    def __init__(self):
        self.model = actr.ACTRModel()

        #Each chunk type should be defined first.
        self.model.chunktype("countOrder", ("first", "second"))
        #Chunk type is defined as (name, attributes)

        #Attributes are written as an iterable (above) or as a string, separated by comma:
        self.model.chunktype("countOrder", "first, second")

        self.dm = self.model.DecMem()
        #this creates declarative memory

        for i in range(1, 6):
            self.dm.add(self.model.Chunk("countOrder", first=i, second=i+1))
            #adding chunks to declarative memory

        self.retrieval = self.model.dmBuffer("retrieval", self.dm)
        #creating buffer for dm
    
        self.g = self.model.goal("g", default_harvest=self.dm)
        #creating goal buffer

        self.model.chunktype("countFrom", ("start", "end", "count"))
        self.g.add(self.model.Chunk("countFrom", start=2, end=4))
        #adding stuff to goal buffer

        #production rules follow; they are methods that create generators: first yield yields buffer tests, the second yield yields buffer changes;
    def start(self):
        yield {"=g":self.model.Chunk("countFrom", start="=x", count=None)}
        yield {"=g":self.model.Chunk("countFrom", count="=x"),
                "+retrieval": self.model.Chunk("countOrder", first="=x")}

    def increment(self):
        yield {"=g":self.model.Chunk("countFrom", count="=x", end="~=x"),
                "=retrieval": self.model.Chunk("countOrder", first="=x", second="=y")}
        yield {"=g":self.model.Chunk("countFrom", count="=y"),
                "+retrieval": self.model.Chunk("countOrder", first="=y")}

    def stop(self):
        yield {"=g":self.model.Chunk("countFrom", count="=x", end="=x")}
        yield {"!g": ("clear", (0, self.model.DecMem()))}

class Counting_stringversion(object):

    def __init__(self):
        self.model = actr.ACTRModel()

        self.model.chunktype("countOrder", "first, second")

        self.dm = self.model.DecMem()

        self.dm.add(self.model.chunkstring(string="\
                isa countOrder\
                first 1\
                second 2"))
        self.dm.add(self.model.chunkstring(string="\
                isa countOrder\
                first 2\
                second 3"))
        self.dm.add(self.model.chunkstring(string="\
                isa countOrder\
                first 3\
                second 4"))
        self.dm.add(self.model.chunkstring(string="\
                isa countOrder\
                first 4\
                second 5"))

        self.retrieval = self.model.dmBuffer("retrieval", self.dm)
        #creating buffer for dm
    
        self.g = self.model.goal("g", default_harvest=self.dm)
        #creating goal buffer

        self.model.chunktype("countFrom", ("start", "end", "count"))
        self.g.add(self.model.chunkstring(string="\
                isa countFrom\
                start   2\
                end 4"))

        self.model.productionstring(name="start", string="""
                =g>
                isa countFrom
                start =x
                count None
                ==>
                =g>
                isa countFrom
                count =x
                +retrieval>
                isa countOrder
                first =x""")

        self.model.productionstring(name="increment", string="""
        =g>
        isa     countFrom
        count       =x
        end         ~=x
        =retrieval>
        isa     countOrder
        first       =x
        second      =y
        ==>
        =g>
        isa     countFrom
        count       =y
        +retrieval>
        isa     countOrder
        first       =y""")

        self.model.productionstring(name="stop", string="""
        =g>
        isa     countFrom
        count       =x
        end         =x
        ==>
        ~g>""")

class Addition(object):

    def __init__(self):
        self.model = actr.ACTRModel()
        self.model.chunktype("countOrder", ("first", "second"))

        self.model.chunktype("add", ("arg1", "arg2", "sum", "count"))

        dm = self.model.DecMem()

        for i in range(0, 11):
            dm.add(self.model.Chunk("countOrder", first=i, second=i+1))

        retrieval = self.model.dmBuffer("retrieval", dm)
    
        g = self.model.goal("g")

        g.add(self.model.Chunk("add", arg1=5, arg2=2))

    def initAddition(self):
        yield {"=g":self.model.Chunk("add", arg1="=num1", arg2="=num2", sum=None)}
        yield {"=g":self.model.Chunk("add", sum="=num1", count=0), "+retrieval": self.model.Chunk("countOrder", first="=num1")}

    def terminateAddition(self):
        yield {"=g":self.model.Chunk("add", count="=num", arg2="=num", sum="=answer")}
        yield {"!g": ("clear", (0, self.model.DecMem()))}

    def incrementCount(self):
        yield {"=g":self.model.Chunk("add", count="=count", sum="=sum"), "=retrieval":self.model.Chunk("countOrder", first="=count", second="=newcount")}
        yield {"=g":self.model.Chunk("add", count="=newcount"), "+retrieval": self.model.Chunk("countOrder", first="=sum")}

    def incrementSum(self):
        yield {"=g":self.model.Chunk("add", count="=count", arg2="~=count", sum="=sum"), "=retrieval":self.model.Chunk("countOrder", first="=sum", second="=newsum")}
        yield {"=g":self.model.Chunk("add", sum="=newsum"), "+retrieval": self.model.Chunk("countOrder", first="=count")}

class Model1(object):

    def __init__(self):
        self.model = actr.ACTRModel()

        self.model.chunktype("countOrder", ("first", "second"))

        dm = self.model.DecMem()

        for i in range(1, 6):
            dm.add(self.model.Chunk("countOrder", first=i, second=i+1))
    
        retrieval = self.model.dmBuffer("retrieval", dm)
    
        g = self.model.goal("g")

        self.model.chunktype("countFrom", ("start", "end", "count"))
        g.add(self.model.Chunk("countFrom", start=2, end=4))

    def start(self):
        yield {"=g":self.model.Chunk("countFrom", start="=x", end=4), "?retrieval": {"state":"free"}}
        yield {"=g":self.model.Chunk("countFrom", end="=x"),
                "+retrieval": self.model.Chunk("countOrder", first="=x")}

    def increment(self):
        yield {"=g":self.model.Chunk("countFrom", start="=x", end="=x"), "?retrieval": {"state":"busy"}}
        yield {"=g":self.model.Chunk("countFrom", start="=x", end=3), "+retrieval": self.model.Chunk("countOrder", first=3)}

    def stop(self):
        yield {"=g":self.model.Chunk("countFrom", start="=x", end="~!4"), "?retrieval": {"state":"free"}}
        yield {"!g": ("clear", (0, self.model.DecMem()))}

class Model2(object):
    
    def __init__(self):
        self.model = actr.ACTRModel()

        self.model.chunktype("twoVars", ("x", "y"))

        self.dm = self.model.DecMem()

        self.dm.add(self.model.Chunk("twoVars", x=10, y=20))
    
        retrieval = self.model.dmBuffer("retrieval", self.dm)
    
        g = self.model.goal("g")

        self.model.chunktype("reverse", ("x", "y"))
        g.add(self.model.Chunk("reverse", x=10))

    def start(self):
        yield {"=g": self.model.Chunk("reverse", x="=num", y="~=num")}
        yield {"+retrieval": self.model.Chunk("twoVars", x="=num"), "=g": self.model.Chunk("reverse", x="=num", y="=num")}
    
    def switch(self):
        yield {"=retrieval": self.model.Chunk("twoVars", x="=num", y="=num2"), "=g": self.model.Chunk("reverse", y="=num")}
        yield {"=retrieval": self.model.Chunk("twoVars", x="=num2", y="=num")}

    def clear(self):
        yield {"?retrieval": {"buffer": "full"}, "?g": {"buffer": "empty"}}
        yield {"~retrieval": None}

class Model3(object):
    
    def __init__(self):
        self.model = actr.ACTRModel()

        self.model.chunktype("twoVars", ("x", "y"))

        self.dm = self.model.DecMem()

        self.dm.add(self.model.Chunk("twoVars", x=10, y=20))
    
        retrieval = self.model.dmBuffer("retrieval", self.dm)
    
        g = self.model.goal("g", None, self.dm) #default harvest is optional since only one harvest; but testing that it works

        self.model.chunktype("reverse", ("x", "y"))
        g.add(self.model.Chunk("reverse", x=10))

    def start(self):
        yield {"=g": self.model.Chunk("reverse", x="=num", y="~=num")}
        yield {"+retrieval": self.model.Chunk("twoVars", x="=num"), "=g": self.model.Chunk("reverse", x="=num", y="=num")}
    
    def switch(self):
        yield {"=retrieval": self.model.Chunk("twoVars", x="=num", y="=num2"), "=g": self.model.Chunk("reverse", y="=num")}
        yield {"=retrieval": self.model.Chunk("twoVars", x="=num2", y="=num")}

    def clear(self):
        yield {"?retrieval": {"buffer": "full"}, "?g": {"buffer": "empty"}}
        yield {"~retrieval": None}

class MotorModel(actr.ACTRModel):

    def __init__(self):
        self.model = actr.ACTRModel()

        g = self.model.goal("g")

        self.model.chunktype("press", "key")
        g.add(self.model.Chunk("press", key="a"))

    def start(self):
        yield {"=g": self.model.Chunk("press", key="=k!a")}
        yield {"+manual": self.model.Chunk("_manual", cmd="presskey", key="=k"), "=g": self.model.Chunk("press", key="b")}

    def go_on(self):
        yield {"=g": self.model.Chunk("press", key="=k!b")}
        yield {"+manual": self.model.Chunk("_manual", cmd="presskey", key="=k"), "=g": self.model.Chunk("press", key="c")}
    
    def finish(self):
        yield {"=g": self.model.Chunk("press", key="=k!c"), "?manual": {"preparation": "free"}}
        yield {"+manual": self.model.Chunk("_manual", cmd="presskey", key="=k"), "=g": self.model.Chunk("press", key="d")}

"""
Demo - pressing a key by ACT-R model. Tutorial 2 of Lisp ACT-R.
"""

import string
import random

import pyactr.environment as env

class Environment1(actr.Environment): #subclass Environment
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
        used_text = {key: self.text[key] for key in sorted(list(self.text))[0:number_pairs]}

        time = start_time
        yield self.Event(env.roundtime(time), self._ENV, "STARTING ENVIRONMENT")
        for _ in range(number_trials):
           for word in used_text: 
                self.output(word, trigger=used_text[word]) #output on environment
                time += self.run_time
                yield self.Event(env.roundtime(time), self._ENV, "PRINTED WORD %s" % word)
                self.output(used_text[word]) #output on environment
                time += self.run_time
                yield self.Event(env.roundtime(time), self._ENV, "PRINTED NUMBER %s" % used_text[word])

class Paired(object):
    """
    Model pressing the right key.
    """

    def __init__(self, env, **kwargs):
        self.m = actr.ACTRModel(environment=env, **kwargs)

        self.m.chunktype("pair", "probe answer")
        
        self.m.chunktype("goal", "state")

        self.dm = self.m.DecMem()

        self.m.dmBuffer("retrieval", self.dm)

        g = self.m.goal("g")
        self.m.goal("g2", set_delay=0.2)
        self.start = self.m.Chunk("somechunk", value="start")
        self.attending = self.m.Chunk("somechunk", value="attending")
        self.testing = self.m.Chunk("somechunk", value="testing")
        self.response = self.m.Chunk("somechunk", value="response")
        self.study = self.m.Chunk("somechunk", value="study")
        self.attending_target = self.m.Chunk("somechunk", value="attending_target")
        self.done = self.m.Chunk("somechunk", value="done")
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
        yield {"=g": self.m.Chunk("goal", state=self.start), "~visual": None, "=g2": self.m.Chunk("pair", answer="=val")}

    def clear_imaginal(self):
        yield {"=g": self.m.Chunk("goal", state=self.start), "=g2": self.m.Chunk("pair")}
        yield {"=g": self.m.Chunk("goal", state=self.start)}

class Utilities(object):
    """
    Model pressing the right key.
    """

    def __init__(self, **kwargs):
        self.m = actr.ACTRModel(**kwargs)

        self.dm = self.m.DecMem()

        self.m.dmBuffer("retrieval", self.dm)

        g = self.m.goal("g")
        g.add(self.m.Chunk("start", state="start"))

    def one(self, utility=1):
        yield {"=g": self.m.Chunk("start", state="start")}
        yield {"=g": self.m.Chunk("change", state="change")}

    def two(self, utility=5):
        yield {"=g": self.m.Chunk("start", state="start")}
        yield {"=g": self.m.Chunk("dontchange", state="start")}
    
    def three(self, reward=10):
        yield {"=g": self.m.Chunk("change", state="change")}
        yield {"~g": None}

