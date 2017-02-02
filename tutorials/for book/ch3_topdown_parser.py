"""
A simple top-down parser.
"""

import pyactr as actr

environment = actr.Environment(focus_position=(320, 180))

actr.chunktype("read", "state word goal_cat")
actr.chunktype("parsing", "top bottom")
actr.chunktype("word", "form cat")

parser = actr.ACTRModel(environment)

parser.decmem.add(actr.chunkstring(string="isa word form 'Mary' cat 'ProperN'"))
parser.decmem.add(actr.chunkstring(string="isa word form 'Bill' cat 'ProperN'"))
parser.decmem.add(actr.chunkstring(string="isa word form 'likes' cat 'V'"))

parser.goal.add(actr.chunkstring(string="""
        isa     read
        state   start
        goal_cat 'S'"""))
parser.goal = "g2"
parser.goals["g2"].add(actr.chunkstring(string="""
        isa     parsing
        top     'S'"""))
parser.goals["g2"].delay = 0.2

parser.productionstring(name="encode word", string="""
        =g>
        isa     read
        state   start
        =visual>
        isa     _visual
        value   =val
        ==>
        =g>
        isa     read
        state   parse
        word    =val
        ~visual>""")

parser.productionstring(name="expand: S->NP VP", string="""
        =g>
        isa         read
        state       parse
        goal_cat    'S'
        =g2>
        isa         parsing
        top         'S'
        ==>
        =g2>
        isa         parsing
        top         'NP'
        bottom      'VP'
        =g>
        isa         read
        state       parse
    """)

parser.productionstring(name="expand: VP->V NP", string="""
        =g>
        isa         read
        state       parse
        =g2>
        isa         parsing
        top         'VP'
        ==>
        =g2>
        isa         parsing
        top         'V'
        bottom      'NP'
        =g>
        isa         read
        state       match
    """)

parser.productionstring(name="expand: NP->ProperN", string="""
        =g>
        isa         read
        state       parse
        =g2>
        isa         parsing
        top         'NP'
        ==>
        =g2>
        isa         parsing
        top         'ProperN'
        =g>
        isa         read
        state       match
    """)

parser.productionstring(name="scan 1", string="""
        =g>
        isa         read
        state       match
        word        =w
        =g2>
        isa         parsing
        top         =t
        ?retrieval>
        state       free
        ==>
        =g>
        isa         read
        state       scan
        +retrieval>
        isa         word
        form        =w
        cat         =t""")

parser.productionstring(name="scan 2", string="""
        =g>
        isa         read
        state       scan
        ?retrieval>
        buffer      full
        =g2>
        isa         parsing
        top         =t
        bottom      =b
        ==>
        =g>
        isa         read
        state       done
        =g2>
        isa         parsing
        top         =b
        ~retrieval>""")

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

if __name__ == "__main__":
    stimuli = [{1: {'text': 'Mary', 'position': (320, 180)}}, {1: {'text': 'likes', 'position': (320, 180)}}, {1: {'text': 'Bill', 'position': (320, 180)}}]
    sim = parser.simulation(realtime=True, environment_process=environment.environment_process, stimuli=stimuli, triggers='A', times=10)
    sim.run(2)
    for elem in parser.decmem.keys():
        if elem.typename == "parsing":
            print(elem)
