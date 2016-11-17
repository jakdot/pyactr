"""
A bottom-up parser.
"""

import pyactr as actr

class Environment(actr.Environment): #subclass Environment
    """
    Environment, putting a random letter on screen.
    """

    def __init__(self):
        self.text = ['Bill', 'likes', 'Mary']
        self.run_time = 2

    def environment_process(self, start_time):
        """
        Environment process. Random letter appears, model has to press the key corresponding to the letter.
        """
        time = start_time
        yield self.Event(time, self._ENV, "STARTING ENVIRONMENT") 
        for idx in range(len(self.text)):
            word = self.text[idx]
            self.output(word, trigger='a') #output on environment
            time = time + self.run_time
            yield self.Event(time, self._ENV, "PRINTED WORD %s" % word)


environ = Environment()

actr.chunktype("read", "state word goal_cat")
actr.chunktype("parsing", "cat mother")

parser = actr.ACTRModel(environ)

dm = parser.DecMem()
dm.add(actr.chunkstring(string="isa word form 'Mary' cat 'ProperN'"))
dm.add(actr.chunkstring(string="isa word form 'Bill' cat 'ProperN'"))
dm.add(actr.chunkstring(string="isa word form 'likes' cat 'V'"))
retrieval = parser.dmBuffer(name="retrieval", declarative_memory=dm)

g = parser.goal(name="g")
g2 = parser.goal(name="g2", set_delay=0.2)
g.add(actr.chunkstring(string="""
        isa     read
        state   start
        goal_cat 'S'"""))
g2.add(actr.chunkstring(string="""
        isa     parsing"""))

parser.productionstring(name="find_unattended_word", string="""
        =g>
        isa     read
        state   start
        ?visual>
        state   auto_buffering
        ==>
        =g>
        isa     read
        state   attend_let
        +visual>""")

parser.productionstring(name="encode_word", string="""
        =g>
        isa     read
        state   attend_let
        =visual>
        isa     _visual
        object  =word
        ==>
        =g>
        isa     read
        state   analyze
        word    =word""")

parser.productionstring(name="retrieve category", string="""
        =g>
        isa         read
        state       analyze
        word        =w
        ==>
        =g>
        isa         read
        state        retrieving
        +retrieval>
        isa         word
        form        =w""")
            
parser.productionstring(name="project word", string="""
        =g>
        isa         read
        state       retrieving
        =retrieval>
        isa         word
        form        =w1
        cat         =y
        =g2>
        isa         parsing
        ==>
        =g>
        isa         read
        state        syntax
        =g2>
        isa         parsing
        cat         =y""")

parser.productionstring(name="project: NP -> ProperN", string="""
        =g>
        isa         read
        state       syntax
        =g2>
        isa         parsing
        cat         'ProperN'
        mother      None
        ==>
        =g2>
        isa         parsing
        cat         'ProperN'
        mother      'NP'
        =g>
        isa         read
        state       store""")

parser.productionstring(name="store parse and continue", string="""
        =g>
        isa         read
        state       store
        =g2>
        isa         parsing
        mother      =x
        ?retrieval>
        buffer      empty
        ==>
        ~g2>
        +g2>
        isa         parsing
        cat         =x
        =g>
        isa         read
        state       syntax""")


parser.productionstring(name="store V", string="""
        =g>
        isa         read
        state       syntax
        =g2>
        isa         parsing
        cat         'V'
        mother      None
        ?retrieval>
        buffer      empty
        ==>
        ~g2>
        +g2>
        isa         parsing
        =g>
        isa         read
        state       done""")

parser.productionstring(name="store parse and retrieval", string="""
        =g>
        isa         read
        state       store
        =g2>
        isa         parsing
        mother      =x
        ?retrieval>
        buffer      full
        ==>
        ~g2>
        ~retrieval>
        +g2>
        isa         parsing
        cat         =x
        =g>
        isa         read
        state       syntax""")


parser.productionstring(name="retrieve NP for: S -> NP VP", string="""
        =g>
        isa         read
        state       syntax
        =g2>
        isa         parsing
        cat         'VP'
        mother      None
        ?retrieval>
        buffer      empty
        state       free
        ==>
        =g2>
        isa         parsing
        +retrieval>
        isa         parsing
        cat         'NP'
        mother      None
        =g>
        isa         read""")


parser.productionstring(name="retrieve V for: VP -> V NP", string="""
        =g>
        isa         read
        state       syntax
        =g2>
        isa         parsing
        cat         'NP'
        mother      None
        ?retrieval>
        buffer      empty
        state       free
        ==>
        =g2>
        isa         parsing
        +retrieval>
        isa         parsing
        cat         'V'
        mother      None
        =g>
        isa         read""")

parser.productionstring(name="project: S -> NP VP", string="""
        =g>
        isa         read
        state       syntax
        =g2>
        isa         parsing
        cat         'VP'
        mother      None
        =retrieval>
        isa         parsing
        cat         'NP'
        mother      None
        ==>
        =g2>
        isa         parsing
        cat         'VP'
        mother      'S'
        =retrieval>
        isa         parsing
        cat         'NP'
        mother      'S'
        =g>
        isa         read
        state       syntax""")

parser.productionstring(name="project: VP -> V NP", string="""
        =g>
        isa         read
        state       syntax
        =g2>
        isa         parsing
        cat         'NP'
        mother      None
        =retrieval>
        isa         parsing
        cat         'V'
        mother      None
        ==>
        =g2>
        isa         parsing
        cat         'NP'
        mother      'VP'
        =retrieval>
        isa         parsing
        cat         'V'
        mother      'VP'
        =g>
        isa         read
        state       store""")


parser.productionstring(name="done", string="""
        =g>
        isa         read
        state       syntax
        =g2>
        isa         parsing
        ?retrieval>
        buffer      empty
        state       error
        ==>
        ~g2>
        +g2>
        isa         parsing
        =g>
        isa         read
        state       done""")


parser.productionstring(name="press a key", string="""
        =g>
        isa     read
        state   done
        ?manual>
        state   free
        ==>
        =g>
        isa     read
        state   start
        +manual>
        isa     _manual
        cmd     'presskey'
        key     'a'""")

parser.productionstring(name="finished", string="""
        =g>
        isa         read
        state       syntax
        goal_cat    =x
        =g2>
        isa         parsing
        mother      =x
        ?retrieval>
        buffer      full
        ==>
        ~g2>
        ~retrieval>
        ~g>""")

if __name__ == "__main__":
    sim = parser.simulation(realtime=True, environment_process=environ.environment_process, start_time=0)
    sim.run()
    print(dm)

