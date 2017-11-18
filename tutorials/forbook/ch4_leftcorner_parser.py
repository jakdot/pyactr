"""
A left-corner parser.
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

parser.productionstring(name="project: NP -> ProperN", string="""
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

parser.productionstring(name="project and complete: VP -> V NP", string="""
        =g>
        isa         read
        state       syntax
        goal_cat    'VP'
        =g2>
        isa         parsing
        top         'V'
        middle      =m
        bottom      =b
        ==>
        =g2>
        isa         parsing
        top         =m
        middle      =b
        bottom      None
        =g>
        isa         read
        state       done
        goal_cat    'NP'""")

parser.productionstring(name="project and complete: S->NP VP", string="""
        =g>
        isa         read
        state       syntax
        goal_cat    'S'
        =g2>
        isa         parsing
        top         'NP'
        middle      =m
        bottom      =b
        ==>
        =g2>
        isa         parsing
        top         =m
        middle      =b
        bottom      None
        =g>
        isa         read
        state       done
        goal_cat    'VP'
    """)

parser.productionstring(name="project and complete: NP", string="""
        =g>
        isa         read
        state       syntax
        goal_cat    =x
        =g2>
        isa         parsing
        top         =x
        middle      =m
        bottom      =b
        ==>
        =g2>
        isa         parsing
        top         =m
        middle      =b
        bottom      None
        =g>
        isa         read
        state       done
        goal_cat    None
    """)

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
        goal_cat    None
        ==>
        ~g>""")

if __name__ == "__main__":
    stimuli = [{1: {'text': 'Mary', 'position': (320, 180)}}, {1: {'text': 'likes', 'position': (320, 180)}}, {1: {'text': 'Bill', 'position': (320, 180)}}]
    sim = parser.simulation(realtime=True, environment_process=environment.environment_process, stimuli=stimuli, triggers='A', times=10)
    sim.run(2)
    for elem in parser.decmem.keys():
        if elem.typename == "parsing":
            print(elem)
