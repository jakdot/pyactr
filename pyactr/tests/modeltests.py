"""
Models testing symbolic system of ACT-R.
"""

import pyactr as actr

class Counting(object):

    def __init__(self):
        self.model = actr.ACTRModel()

        #Each chunk type should be defined first.
        self.model.chunktype("countOrder", ("first", "second"))
        #makechunk type is defined as (name, attributes)

        #Attributes are written as an iterable (above) or as a string, separated by comma:
        self.model.chunktype("countOrder", "first, second")

        self.dm = self.model.decmem
        #this creates declarative memory

        for i in range(1, 6):
            self.dm.add(actr.chunks.makechunk("", "countOrder", first=i, second=i+1))
            #adding chunks to declarative memory

    

        self.model.chunktype("countFrom", ("start", "end", "count"))
        self.model.goal.add(actr.chunks.makechunk("01", "countFrom", start=2, end=4))
        #adding stuff to goal buffer

        #production rules follow; they are methods that create generators: first yield yields buffer tests, the second yield yields buffer changes;
    def start(self):
        yield {"=g":actr.chunks.makechunk("01", "countFrom", start="=x", count=None)}
        yield {"=g":actr.chunks.makechunk("01", "countFrom", count="=x"),
                "+retrieval": actr.chunks.makechunk("01", "countOrder", first="=x")}

    def increment(self):
        yield {"=g":actr.chunks.makechunk("01", "countFrom", count="=x", end="~=x"),
                "=retrieval": actr.chunks.makechunk("01", "countOrder", first="=x", second="=y")}
        yield {"=g":actr.chunks.makechunk("01", "countFrom", count="=y"),
                "+retrieval": actr.chunks.makechunk("01", "countOrder", first="=y")}

    def stop(self):
        yield {"=g":actr.chunks.makechunk("01", "countFrom", count="=x", end="=x")}
        yield {"!g": ("clear", (0, self.model.decmem))}

class Counting_stringversion(object):

    def __init__(self):
        self.model = actr.ACTRModel()

        self.model.chunktype("countOrder", "first, second")

        self.dm = self.model.decmem

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

        self.model.chunktype("countFrom", ("start", "end", "count"))
        self.model.goal.add(self.model.chunkstring(string="\
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

        dm = self.model.decmem

        for i in range(0, 11):
            dm.add(actr.makechunk("chunk"+str(i), "countOrder", first=i, second=i+1))

        self.model.goal.add(actr.makechunk("", "add", arg1=5, arg2=2))

        self.model.productionstring(name="initAddition", string="""
        =g>
        isa     add
        arg1    =num1
        arg2    =num2
        sum     None
        ==>
        =g>
        isa     add
        sum     =num1
        count   0
        +retrieval>
        isa     countOrder
       first   =num1""")

        self.model.productionstring(name="terminateAddition", string="""
        =g>
        isa     add
        count   =num
        arg2    =num
        sum     =answer
        ==>
        ~g>""")

        self.model.productionstring(name="incrementCount", string="""
        =g>
        isa     add
        count   =count
        sum     =sum
        =retrieval>
        isa     countOrder
        first   =count
        second  =newcount
        ==>
        =g>
        isa     add
        count   =newcount
        +retrieval>
        isa     countOrder
        first   =sum""")

        self.model.productionstring(name="incrementSum", string="""
        =g>
        isa     add
        count   =count
        arg2    ~=count
        sum     =sum
        =retrieval>
        isa     countOrder
        first   =sum
        second  =newsum
        ==>
        =g>
        isa     add
        sum     =newsum
        +retrieval>
        isa     countOrder
        first   =count""")

class Model1(object):

    def __init__(self):
        self.model = actr.ACTRModel()

        self.model.chunktype("countOrder", ("first", "second"))

        dm = self.model.decmem

        for i in range(1, 6):
            dm.add(actr.makechunk("", "countOrder", first=i, second=i+1))
    
        self.model.chunktype("countFrom", ("start", "end", "count"))
        self.model.goal.add(actr.makechunk("", "countFrom", start=2, end=4))

        self.model.productionstring(name="start", string="""
        =g>
        isa     countFrom
        start   =x
        count   None
        ?retrieval>
        state   free
        ==>
        =g>
        isa     countFrom
        count   =x
        +retrieval>
        isa     countOrder
        first   =x""")

        self.model.productionstring(name="increment", string="""
        =g>
        isa     countFrom
        count   =x
        end     ~=x
        =retrieval>
        isa     countOrder
        first   =x
        second  =y
        ==>
        =g>
        isa     countFrom
        count   =y
        +retrieval>
        isa     countOrder
        first   =y""")
        
        self.model.productionstring(name="stop", string="""
        =g>
        isa     countFrom
        count   =x
        end     =x
        ?retrieval>
        state   free
        ==>
        ~g>""")

class Model2(object):
    
    def __init__(self, **kwargs):
        self.model = actr.ACTRModel(**kwargs)

        actr.chunktype("twoVars", ("x", "y"))
        actr.chunktype("reverse", ("x", "y"))

        self.dm = self.model.decmem

        self.dm.add(actr.makechunk("", "twoVars", x=10, y=20))
    
        self.model.goal.add(actr.makechunk("", "reverse", x=10))

    def start(self):
        yield {"=g": actr.makechunk("", "reverse", x="=num", y="~=num")}
        yield {"+retrieval": actr.makechunk("", "twoVars", x="=num"), "=g": actr.makechunk("", "reverse", x="=num", y="=num")}
    
    def switch(self):
        yield {"=retrieval": actr.makechunk("", "twoVars", x="=num", y="=num2"), "=g": actr.makechunk("", "reverse", y="=num")}
        yield {"=retrieval": actr.makechunk("", "twoVars", x="=num2", y="=num")}

    def clear(self):
        yield {"?retrieval": {"buffer": "full"}, "?g": {"buffer": "empty"}}
        yield {"~retrieval": None}

class Model3(object):
    
    def __init__(self, **kwargs):
        self.model = actr.ACTRModel(**kwargs)

        actr.chunktype("twoVars", ("x", "y"))

        self.dm = self.model.decmem

        self.dm.add(actr.makechunk("","twoVars", x=10, y=20))
    
        self.model.goal.default_harvest = self.dm #default harvest is optional since only one harvest; but testing that it works

        actr.chunktype("reverse", ("x", "y"))
        self.model.goal.add(actr.makechunk("","reverse", x=10))

    def start(self):
        yield {"=g": actr.makechunk("","reverse", x="=num", y="~=num")}
        yield {"+retrieval": actr.makechunk("","twoVars", x="=num"), "=g": actr.makechunk("","reverse", x="=num", y="=num")}
    
    def switch(self):
        yield {"=retrieval": actr.makechunk("","twoVars", x="=num", y="=num2"), "=g": actr.makechunk("","reverse", y="=num")}
        yield {"=retrieval": actr.makechunk("","twoVars", x="=num2", y="=num")}

    def clear(self):
        yield {"?retrieval": {"buffer": "full"}, "?g": {"buffer": "empty"}}
        yield {"~retrieval": None}

class MotorModel(actr.ACTRModel):

    def __init__(self):
        self.model = actr.ACTRModel(motor_prepared=False)

        self.model.chunktype("press", "key")
        self.model.goal.add(actr.makechunk("","press", key="a"))

    def start(self):
        yield {"=g": actr.makechunk("","press", key="=k!a")}
        yield {"+manual": actr.makechunk("","_manual", cmd="press_key", key="=k"), "=g": actr.makechunk("","press", key="b")}

    def go_on(self):
        yield {"=g": actr.makechunk("","press", key="=k!b")}
        yield {"+manual": actr.makechunk("","_manual", cmd="press_key", key="=k"), "=g": actr.makechunk("","press", key="c")}
    
    def finish(self):
        yield {"=g": actr.makechunk("","press", key="=k!c"), "?manual": {"preparation": "free"}}
        yield {"+manual": actr.makechunk("","_manual", cmd="press_key", key="=k"), "=g": actr.makechunk("","press", key="d")}

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
        actr.chunktype("chunk", "value")
        actr.chunktype("goal", "state")

        self.dm = self.m.decmem

        start = actr.makechunk(nameofchunk="start", typename="chunk", value="start")
        actr.makechunk(nameofchunk="attending", typename="chunk", value="attending")
        actr.makechunk(nameofchunk="testing", typename="chunk", value="testing")
        actr.makechunk(nameofchunk="response", typename="chunk", value="response")
        actr.makechunk(nameofchunk="study", typename="chunk", value="study")
        actr.makechunk(nameofchunk="attending_target", typename="chunk", value="attending_target")
        actr.makechunk(nameofchunk="done", typename="chunk", value="done")
        self.m.goal.add(actr.makechunk("read", typename="goal", state=start))
        self.m.set_goal("g2", 0.2)

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
        isa     _visual
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
    Model testing utilities.
    """

    def __init__(self, **kwargs):
        self.m = actr.ACTRModel(**kwargs)

        self.dm = self.m.decmem

        actr.chunktype("phase", "state")

        self.m.goal.add(actr.makechunk("start", "phase", state="start"))

    def one(self, utility=1):
        yield {"=g": actr.makechunk("start", "phase", state="start")}
        yield {"=g": actr.makechunk("change", "phase", state="change")}

    def two(self, utility=5):
        yield {"=g": actr.makechunk("start", "phase", state="start")}
        yield {"=g": actr.makechunk("dontchange", "phase", state="start")}
    
    def three(self, reward=10):
        yield {"=g": actr.makechunk("change", "phase", state="change")}
        yield {"~g": None}

class Compilation1(object):
    """
    Model testing compilation -- basic cases. Modification.
    """

    def __init__(self, **kwargs):
        actr.chunktype("state", "starting ending")
        self.m = actr.ACTRModel(**kwargs)


        self.dm = self.m.decmem

        self.m.goal.add(actr.makechunk(nameofchunk="start", typename="state", starting=1))

        self.m.productionstring(name="one", string="""
            =g>
            isa     state
            starting =x
            ending ~=x
            ==>
            =g>
            isa     state
            ending =x""")

        self.m.productionstring(name="two", string="""
            =g>
            isa     state
            starting =x
            ending  =x
            ==>
            =g>
            isa     state
            starting 4""")
        
class Compilation2(object):
    """
    Model testing compilation -- basic cases. Modification.
    """

    def __init__(self, **kwargs):
        actr.chunktype("state", "starting ending")
        self.m = actr.ACTRModel(**kwargs)

        self.dm = self.m.decmem

        self.m.goal.add(actr.makechunk(nameofchunk="start", typename="state", starting=1, ending=1))

        self.m.productionstring(name="one", string="""
            =g>
            isa     state
            starting =x
            ending  =x
            ==>
            =g>
            isa     state
            ending  =x
            starting 4""")
        
        self.m.productionstring(name="two", string="""
            =g>
            isa     state
            starting =x
            ending ~=x
            ==>
            =g>
            isa     state
            ending =x""")

class Compilation3(object):
    """
    Model testing compilation -- basic cases. Modification.
    """

    def __init__(self, **kwargs):
        actr.chunktype("goal", "arg1 arg2 arg3 arg4")
        self.m = actr.ACTRModel(**kwargs)


        self.dm = self.m.decmem

        self.m.goal.add(actr.makechunk(nameofchunk="start", typename="goal", arg1=3))

        self.m.productionstring(name="one", string="""
            =g>
            isa     goal
            arg1    =v1
            arg2    =v2
            arg3    =v2
            arg4    =v3
            ==>
            =g>
            isa     goal
            arg1    =v2
            arg2    =v3
            arg3    =v1""")
        
        self.m.productionstring(name="two", string="""
            =g>
            isa     goal
            arg1    =v0
            arg2    =v1
            arg3    3
            ==>
            =g>
            isa     goal
            arg3    =v1
            arg4    =v0""")

class Compilation4(object):
    """
    Model testing compilation -- basic cases. Query.
    """

    def __init__(self, **kwargs):
        actr.chunktype("goal", "arg1 arg2 arg3 arg4")
        self.m = actr.ACTRModel(**kwargs)


        self.dm = self.m.decmem

        self.m.goal.add(actr.makechunk(nameofchunk="start", typename="goal", arg1=1, arg2=None, arg4=10))
        self.m.goal.default_harvest = self.dm

        self.m.productionstring(name="one", string="""
            ?g>
            state   free
            =g>
            isa     goal
            arg1    1
            ==>
            =g>
            isa     goal
            arg1    2""")
        
        self.m.productionstring(name="two", string="""
            ?g>
            buffer  full
            =g>
            isa     goal
            arg1    2
            arg2    None
            arg3    None
            ==>
            =g>
            isa     goal
            arg1    3""")

class Compilation5(object):
    """
    Model testing compilation -- basic cases. Setting a chunk.
    """

    def __init__(self, **kwargs):
        actr.chunktype("state", "starting ending position")
        self.m = actr.ACTRModel(**kwargs)


        self.dm = self.m.decmem

        self.m.goal.add(actr.makechunk(nameofchunk="start", typename="state", starting=1, ending=3, position='start'))
        self.m.goal.default_harvest = self.dm

        self.m.productionstring(name="one", string="""
            =g>
            isa     state
            starting =x
            ending ~=x
            position 'start'
            ==>
            +g>
            isa     state
            position 'end'
            ending =x""")

        self.m.productionstring(name="two", string="""
            =g>
            isa     state
            starting None
            position 'end'
            ==>
            =g>
            isa     state
            starting 4""")
        
class Compilation6(object):
    """
    Model testing compilation. Modification and retrieval.
    """

    def __init__(self, **kwargs):
        actr.chunktype("goal", "arg1 arg2 arg3 arg4")
        actr.chunktype("fact", "arg1 arg2 arg3 arg4")
        self.m = actr.ACTRModel(**kwargs)


        self.dm = self.m.decmem

        self.dm.add(actr.makechunk("", "fact",  arg1=3, arg2=3, arg3=5, arg4=1) )

        self.m.goal.add(actr.makechunk(nameofchunk="start", typename="goal", arg1=3))

        self.m.productionstring(name="one", string="""
            =g>
            isa     goal
            arg1    =v1
            arg2    =v2
            arg3    =v2
            arg4    =v3
            ==>
            +retrieval>
            isa     fact
            arg1    3
            arg2    =v1
            =g>
            isa     goal
            arg1    =v2
            arg2    =v3
            arg3    =v1""")
        
        self.m.productionstring(name="two", string="""
            =g>
            isa     goal
            arg1    =v0
            arg2    =v1
            arg3    3
            =retrieval>
            isa     fact
            arg3    =v2
            ==>
            =g>
            isa     goal
            arg2    =v2
            arg3    =v1
            arg4    =v0""")

class Compilation7(object):
    """
    Model testing compilation. Modification and retrieval.
    """

    def __init__(self, **kwargs):
        actr.chunktype("goal", "arg1 arg2 arg3 arg4")
        actr.chunktype("fact", "arg1 arg2 arg3 arg4")
        self.m = actr.ACTRModel(**kwargs)


        self.dm = self.m.decmem

        self.dm.add(actr.makechunk("", "fact",  arg1=3, arg2=3, arg3=5, arg4=1) )

        self.m.goal.add(actr.makechunk(nameofchunk="start", typename="goal", arg1=3))

        self.m.productionstring(name="one", string="""
            =g>
            isa     goal
            arg1    =v1
            arg2    =v2
            arg2    ~5
            arg3    =v2
            arg4    =v3
            ==>
            +retrieval>
            isa     fact
            arg1    3
            arg2    =v1
            =g>
            isa     goal
            arg1    =v2
            arg2    =v3
            arg3    =v1""")
        
        self.m.productionstring(name="two", string="""
            =g>
            isa     goal
            arg1    =v0
            arg2    =v1
            arg3    3
            =retrieval>
            isa     fact
            arg3    =v2
            ==>
            ~retrieval>
            =g>
            isa     goal
            arg2    =v2
            arg3    =v1
            arg4    =v0""")
        
        self.m.productionstring(name="three", string="""
            =g>
            isa     goal
            arg2    5
            ?retrieval>
            buffer  empty
            ==>
            =g>
            isa     goal""")

class Compilation8(actr.ACTRModel):
    """
    Motor model for production compilation.
    """

    def __init__(self, **kwargs):
        self.m = actr.ACTRModel(**kwargs)

        self.m.chunktype("press", "key")
        self.m.goal.add(actr.makechunk("","press", key="a"))

    def start(self):
        yield {"=g": actr.makechunk("","press", key="=k!a")}
        yield {"+manual": actr.makechunk("","_manual", cmd="press_key", key="=k"), "=g": actr.makechunk("","press", key="b")}

    def go_on(self):
        yield {"=g": actr.makechunk("","press", key="=k!b")}
        yield {"+manual": actr.makechunk("","_manual", cmd="press_key", key="=k"), "=g": actr.makechunk("","press", key="c")}
    
    def still_go_on(self):
        yield {"=g": actr.makechunk("","press", key="=k!c"), "?manual": {"state": "busy"}}
        yield {"=g": actr.makechunk("","press", key="d")}
    
    def finish(self):
        yield {"=g": actr.makechunk("","press", key="=k!d"), "?manual": {"state": "free"}}
        yield {"=g": actr.makechunk("","press", key="e")}

class Compilation9(object):
    """
    Model testing compilation. Modification and retrieval.
    """

    def __init__(self, **kwargs):
        actr.chunktype("goal", "arg1 arg2 arg3 arg4")
        actr.chunktype("fact", "arg1 arg2 arg3 arg4")
        self.m = actr.ACTRModel(**kwargs)


        self.dm = self.m.decmem

        self.dm.add(actr.makechunk("", "fact",  arg1=3, arg2=3, arg3=5, arg4=1) )

        self.m.goal.add(actr.makechunk(nameofchunk="start", typename="goal", arg1=3))

        self.m.productionstring(name="one", string="""
            =g>
            isa     goal
            arg1    =v1
            arg2    =v2
            arg3    =v2
            arg4    =v3
            ==>
            +retrieval>
            isa     fact
            arg1    3
            arg2    =v1
            +g>
            isa     goal
            arg1    =v2
            arg2    =v3
            arg3    =v1""")
        
        self.m.productionstring(name="two", string="""
            =g>
            isa     goal
            arg1    =v0
            arg2    =v1
            arg3    3
            =retrieval>
            isa     fact
            arg3    =v2
            ==>
            ~retrieval>
            +g>
            isa     goal
            arg2    =v2
            arg3    =v1
            arg4    =v0""")

class Compilation10(object):
    """
    Model testing compilation. Modification and retrieval.
    """

    def __init__(self, **kwargs):
        actr.chunktype("goal", "arg1 arg2 arg3 arg4")
        actr.chunktype("fact", "arg1 arg2 arg3 arg4")
        self.m = actr.ACTRModel(**kwargs)


        self.dm = self.m.decmem

        self.dm.add(actr.makechunk("", "fact",  arg1=3, arg2=3, arg3=5, arg4=1) )

        self.m.goal.add(actr.makechunk(nameofchunk="start", typename="goal", arg1=3))

        self.m.productionstring(name="one", string="""
            =g>
            isa     goal
            arg1    =v1
            arg2    =v2
            arg3    =v2
            arg4    =v3
            ==>
            +retrieval>
            isa     fact
            arg1    3
            arg2    =v1
            +g>
            isa     goal
            arg1    =v2
            arg2    =v3
            arg3    =v1""")
        
        self.m.productionstring(name="two", string="""
            =g>
            isa     goal
            arg1    =v0
            arg2    =v1
            arg3    3
            =retrieval>
            isa     fact
            arg3    =v2
            ==>
            =g>
            isa     goal
            arg2    =v2
            arg3    =v1
            arg4    =v0""")

class Compilation11(object):
    """
    Model testing compilation -- compilation + utilities.
    """

    def __init__(self, **kwargs):
        actr.chunktype("state", "starting ending")
        self.m = actr.ACTRModel(**kwargs)

        self.dm = self.m.decmem

        self.m.goal.add(actr.makechunk(nameofchunk="start", typename="state", starting=1, ending=2))

        self.m.productionstring(name="one", string="""
            =g>
            isa     state
            starting 1
            ending 2
            ==>
            =g>
            isa     state
            ending 1""", utility=10)

        self.m.productionstring(name="two", string="""
            =g>
            isa     state
            starting 1
            ending 1
            ==>
            =g>
            isa   state
            ending 2""")

class Compilation12(object):
    """
    Model testing compilation -- basic cases. Setting a chunk with an empty value.
    """

    def __init__(self, **kwargs):
        actr.chunktype("state", "starting ending position")
        self.m = actr.ACTRModel(**kwargs)


        self.dm = self.m.decmem

        self.m.goal.add(actr.makechunk(nameofchunk="start", typename="state", starting=1, ending=3, position='start'))
        self.m.goal.default_harvest = self.dm

        self.m.productionstring(name="one", string="""
            =g>
            isa     state
            starting =x
            ending ~=x
            position 'start'
            ==>
            +g>
            isa     state
            starting    None
            position 'end'
            ending =x""")

        self.m.productionstring(name="two", string="""
            =g>
            isa     state
            starting None
            position 'end'
            ==>
            =g>
            isa     state
            position 'completeend'""")
