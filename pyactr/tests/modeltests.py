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
        yield {"=g":self.model.Chunk("countFrom", start="=x", end="=x"), "?retrieval": {"buffer":"full"}}
        yield {"=g":self.model.Chunk("countFrom", start="=x", end=3), "+retrieval": self.model.Chunk("countOrder", first=3)}

    def stop(self):
        yield {"=g":self.model.Chunk("countFrom", start="=x", end="~!4"), "?retrieval": {"state":"free"}}
        yield {"!g": ("clear", (0, self.model.DecMem()))}

class Model2(object):
    
    def __init__(self, **kwargs):
        self.model = actr.ACTRModel(**kwargs)

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
    
    def __init__(self, **kwargs):
        self.model = actr.ACTRModel(**kwargs)

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
        self.model = actr.ACTRModel(motor_prepared=False)

        g = self.model.goal("g")

        self.model.chunktype("press", "key")
        g.add(self.model.Chunk("press", key="a"))

    def start(self):
        yield {"=g": self.model.Chunk("press", key="=k!a")}
        yield {"+manual": self.model.Chunk("_manual", cmd="press_key", key="=k"), "=g": self.model.Chunk("press", key="b")}

    def go_on(self):
        yield {"=g": self.model.Chunk("press", key="=k!b")}
        yield {"+manual": self.model.Chunk("_manual", cmd="press_key", key="=k"), "=g": self.model.Chunk("press", key="c")}
    
    def finish(self):
        yield {"=g": self.model.Chunk("press", key="=k!c"), "?manual": {"preparation": "free"}}
        yield {"+manual": self.model.Chunk("_manual", cmd="press_key", key="=k"), "=g": self.model.Chunk("press", key="d")}

"""
Demo - pressing a key by ACT-R model. Tutorial 2 of Lisp ACT-R.
"""

import string
import random

class Paired(object):
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
        screen_x >0""")
        
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

if __name__ == "__main__":
    mm = MotorModel()
    t = mm.model
    t.productions(mm.start, mm.go_on, mm.finish)
    sim = t.simulation(trace=True)
    sim.run()
