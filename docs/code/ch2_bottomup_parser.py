"""
A bottom-up parser.
"""

import pyactr as actr

environment = actr.Environment(focus_position=(320, 180))

actr.chunktype("read", "state word goal_cat")
actr.chunktype("parsing", "cat mother")
actr.chunktype("word", "form cat")

parser = actr.ACTRModel(environment)

dm = parser.decmem
dm.add(actr.chunkstring(string="isa word form 'Mary' cat 'ProperN'"))
dm.add(actr.chunkstring(string="isa word form 'Bill' cat 'ProperN'"))
dm.add(actr.chunkstring(string="isa word form 'likes' cat 'V'"))

parser.goal.add(actr.chunkstring(string="""
        isa     read
        state   start
        goal_cat 'S'"""))
parser.goal = "g2"
parser.goals["g2"].add(actr.chunkstring(string="""
        isa     parsing"""))


parser.productionstring(name="attend_word", string="""
        =g>
        isa     read
        state   start
        =visual_location>
        isa    _visuallocation
        ?visual>
        state   free
        buffer  empty
        ==>
        =g>
        isa     read
        state   start
        +visual>
        isa     _visual
        cmd     move_attention
        screen_pos =visual_location
        ~visual_location>""")

parser.productionstring(name="encode_word", string="""
        =g>
        isa     read
        state   start
        =visual>
        isa     _visual
        value   =val
        ==>
        =g>
        isa     read
        state   analyze
        word    =val
        ~visual>""")

parser.productionstring(name="retrieve category", string="""
        =g>
        isa         read
        state       analyze
        word        =w
        ==>
        =g>
        isa         read
        state       retrieving
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
        state       syntax
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
        cmd     'press_key'
        key     A""")

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
    stimuli = [{1: {'text': 'Mary', 'position': (320, 180)}}, {1: {'text': 'likes', 'position': (320, 180)}}, {1: {'text': 'Bill', 'position': (320, 180)}}]
    sim = parser.simulation(realtime=True, environment_process=environment.environment_process, stimuli=stimuli, triggers='A', times=10)
    sim.run()
    print(dm)

