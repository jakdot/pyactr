"""
A bottom-up parser.
"""

import pyactr as actr

environment = actr.Environment(focus_position=(320, 180))

actr.chunktype("read", "state word goal_cat")
actr.chunktype("parsing", "top middle bottom")
actr.chunktype("word", "form cat")

parser = actr.ACTRModel(environment, motor_prepared=True, subsymbolic=True)

parser.decmem.add(actr.chunkstring(string="isa word form 'Mary' cat 'ProperN'"))
parser.decmem.add(actr.chunkstring(string="isa word form 'Bill' cat 'ProperN'"))
parser.decmem.add(actr.chunkstring(string="isa word form 'likes' cat 'V'"))

parser.goal.add(actr.chunkstring(string="""
        isa     read
        state   start
        goal_cat 'S'"""))
parser.goal = "g2"
parser.goals["g2"].add(actr.chunkstring(string="""
        isa     parsing"""))
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

parser.productionstring(name="retrieve category", string="""
        =g>
        isa         read
        state       parse
        word        =w
        ==>
        =g>
        isa         read
        state       retrieving
        +retrieval>
        isa         word
        form        =w""")
             
parser.productionstring(name="shift word and project it", string="""
        =g>
        isa         read
        state       retrieving
        =retrieval>
        isa         word
        cat         =y
        =g2>
        isa         parsing
        ==>
        =g>
        isa         read
        state       syntax
        =g2>
        isa         parsing
        top         =y
        ~retrieval>""")

parser.productionstring(name="reduce: NP -> ProperN", string="""
        =g>
        isa         read
        state       syntax
        =g2>
        isa         parsing
        top         'ProperN'
        ==>
        =g2>
        isa         parsing
        top         'NP'
        =g>
        isa         read
        state       syntax""")

parser.productionstring(name="reduce: VP -> V NP", string="""
        =g>
        isa         read
        state       syntax
        =g2>
        isa         parsing
        top         'NP'
        middle      'V'
        ==>
        =g2>
        isa         parsing
        top         'VP'
        =g>
        isa         read
        state       syntax""")

parser.productionstring(name="reduce: S->NP VP", string="""
        =g>
        isa         read
        state       syntax
        goal_cat    'S'
        =g2>
        isa         parsing
        top         'VP'
        bottom      'NP'
        ==>
        =g2>
        isa         parsing
        top         'S'
        =g>
        isa         read
        state       done
    """)

parser.productionstring(name="clean stack", string="""
        =g>
        isa         read
        state       syntax
        =g2>
        isa         parsing
        top         =t
        middle      =m
        bottom      =b
        ==>
        ~g2>
        =g>
        isa         read
        state       done
        +g2>
        isa         parsing
        middle      =t
        bottom      =m""", utility=-10)


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
        state       start
        goal_cat    =x
        =g2>
        isa         parsing
        top         =x
        ==>
        ~g2>
        ~g>""")

if __name__ == "__main__":
    stimuli = [{1: {'text': 'Mary', 'position': (320, 180)}}, {1: {'text': 'likes', 'position': (320, 180)}}, {1: {'text': 'Bill', 'position': (320, 180)}}]
    sim = parser.simulation(realtime=True, gui=False, environment_process=environment.environment_process, stimuli=stimuli, triggers='A', times=10)
    sim.run(2)
    print(parser.decmem)
