"""
A left-corner parser.
"""

import pyactr as actr
from ete3 import Tree
import simpy
import re

environment = actr.Environment(focus_position=(320, 180))

actr.chunktype("parsing_goal",
               "task stack1 stack2 stack3 stack4 parsed_word right_frontier found gapped")
actr.chunktype("parse_state",
               "node_cat mother daughter1 daughter2 lex_head")
actr.chunktype("word", "form cat")

parser = actr.ACTRModel(environment, subsymbolic=True, retrieval_threshold=-5, latency_factor=0.1, latency_exponent=0.13)
dm = parser.decmem
g = parser.goal
imaginal = parser.set_goal(name="imaginal", delay=0)

dm.add(actr.chunkstring(string="""
    isa  word
    form 'Mary'
    cat  'ProperN'
"""))

dm.add(actr.chunkstring(string="""
    isa  word
    form 'The'
    cat  'Det'
"""))

dm.add(actr.chunkstring(string="""
    isa  word
    form 'the'
    cat  'Det'
"""))
dm.add(actr.chunkstring(string="""
    isa  word
    form 'boy'
    cat  'N'
"""))
dm.add(actr.chunkstring(string="""
    isa  word
    form 'who'
    cat  'wh'
"""))
dm.add(actr.chunkstring(string="""
    isa  word
    form 'Bill'
    cat  'ProperN'
"""))
dm.add(actr.chunkstring(string="""
    isa  word
    form 'likes'
    cat  'V'
"""))
dm.add(actr.chunkstring(string="""
    isa  word
    form 'saw'
    cat  'V'
"""))
g.add(actr.chunkstring(string="""
    isa             parsing_goal
    task            reading_word
    stack1       'S'
    right_frontier  'S'
    gapped          False
"""))

parser.productionstring(name="encode word", string="""
    =g>
    isa             parsing_goal
    task            reading_word
    =visual>
    isa             _visual
    value           =val
    ==>
    =g>
    isa             parsing_goal
    task            get_word_cat
    parsed_word    =val
    ~visual>
    ~retrieval>
""")

parser.productionstring(name="retrieve category", string="""
    =g>
    isa             parsing_goal
    task            get_word_cat
    parsed_word     =w
    ==>
    +retrieval>
    isa             word
    form            =w
    =g>
    isa             parsing_goal
    task            retrieving_word
""")

parser.productionstring(name="shift and project word", string="""
    =g>
    isa             parsing_goal
    task            retrieving_word
    =retrieval>
    isa             word
    form            =w
    cat             =c
    ==>
    =g>
    isa             parsing_goal
    task            parsing
    found           =c
    +imaginal>
    isa             parse_state
    node_cat        =c
    daughter1       =w
    ~retrieval>
""")

parser.productionstring(name="reanalyse: subject wh", string="""
    =g>
    isa             parsing_goal
    task            parsing
    stack1          'VP'
    stack2          'VP'
    gapped          False
    found           ~'V'
    found           ~None
    ==>
    =g>
    isa             parsing_goal
    stack1          'S'
    stack2          'VP'
    stack3          'VP'
    right_frontier  'S'
    gapped          True
""")

parser.productionstring(name="project: NP ==> ProperN", string="""
    =g>
    isa             parsing_goal
    task            parsing
    stack1          'S'
    stack2          =s2
    stack3          =s3
    right_frontier  =rf
    parsed_word     =w
    found           'ProperN'
    ==>
    =g>
    isa             parsing_goal
    stack1          'NP'
    stack2          'S'
    stack3          =s2
    stack4          =s3
    found           None
    +imaginal>
    isa             parse_state
    node_cat        'NP'
    daughter1       'ProperN'
    mother          =rf
    lex_head        =w
""")

parser.productionstring(name="project: NP ==> Det N", string="""
    =g>
    isa             parsing_goal
    task            parsing
    stack1          'S'
    stack1          =s1
    stack2          =s2
    right_frontier  =rf
    parsed_word     =w
    found          'Det'
    ==>
    =g>
    isa             parsing_goal
    stack1          'N'
    stack2          'NP'
    stack3          =s1
    stack4          =s2
    found           None
    +imaginal>
    isa             parse_state
    node_cat        'NP'
    daughter1       'Det'
    mother          =rf
""")

parser.productionstring(name="project and complete: NP ==> Det N", string="""
    =g>
    isa             parsing_goal
    task            parsing
    stack1          'NP'
    right_frontier  =rf
    parsed_word     =w
    found          'Det'
    ==>
    =g>
    isa             parsing_goal
    stack1          'N'
    found           None
    +imaginal>
    isa             parse_state
    node_cat        'NP'
    daughter1       'Det'
    mother          =rf
""")

parser.productionstring(name="project and complete: N", string="""
    =g>
    isa             parsing_goal
    task            parsing
    stack1          'N'
    stack2          =s2
    stack3          =s3
    stack4          =s4
    right_frontier  =rf
    parsed_word     =w
    found           'N'
    ==>
    =g>
    isa             parsing_goal
    stack1          =s2
    stack2          =s3
    stack3          =s4
    stack4          None
    found           None
    +imaginal>
    isa             parse_state
    node_cat        'NP'
    daughter1       'Det'
    daughter2       'N'
    lex_head        =w
    mother          'NP'
""")

parser.productionstring(name="project and complete: wh", string="""
    =g>
    isa             parsing_goal
    task            parsing
    stack1          'VP'
    stack2          =s2
    stack3          =s3
    right_frontier  =rf
    parsed_word     =w
    found           'wh'
    gapped          ~filling
    ==>
    =g>
    isa             parsing_goal
    stack1          'VP'
    stack2          'VP'
    stack3          =s2
    stack4          =s3
    gapped          filling
    found           None
    +imaginal>
    isa             parse_state
    node_cat        'CP'
    daughter1       'wh-DP'
    daughter2       'S'
    lex_head        =w
    mother          'NP'
""")

parser.productionstring(name="project and complete: subj wh-gap", string="""
    =g>
    isa             parsing_goal
    task            parsing
    stack1          'VP'
    stack2          'VP'
    gapped          filling
    parsed_word     =w
    ==>
    =g>
    isa             parsing_goal
    gapped          False
    found           None
    +imaginal>
    isa             parse_state
    node_cat        'NP'
    daughter1       'gap'
    lex_head        =w
    mother          'S'
""")

parser.productionstring(name="project and complete: NP ==> ProperN", string="""
    =g>
    isa             parsing_goal
    task            parsing
    stack1          'NP'
    stack2          =s2
    stack3          =s3
    stack4          =s4
    right_frontier  =rf
    parsed_word     =w
    found           'ProperN'
    ==>
    =g>
    isa             parsing_goal
    stack1          =s2
    stack2          =s3
    stack3          =s4
    found           None
    +imaginal>
    isa             parse_state
    node_cat        'NP'
    daughter1       'ProperN'
    mother          =rf
    lex_head        =w
""")

parser.productionstring(name="project and complete: S ==> NP VP", string="""
    =g>
    isa             parsing_goal
    task            parsing
    stack1          'NP'
    stack2          'S'
    stack3          =s3
    stack4          =s4
    ==>
    =g>
    isa             parsing_goal
    stack1          'VP'
    stack2          =s3
    stack3          =s4
    right_frontier  'VP'
    found           None
    +imaginal>
    isa             parse_state
    node_cat        'S'
    daughter1       'NP'
    daughter2       'VP'
""")

parser.productionstring(name="project and complete: VP ==> V NP", string="""
    =g>
    isa             parsing_goal
    task            parsing
    stack1          'VP'
    found           'V'
    gapped          ~True
    ==>
    =g>
    isa             parsing_goal
    stack1       'NP'
    found           None
    +imaginal>
    isa             parse_state
    mother          'S'
    node_cat        'VP'
    daughter1       'V'
    daughter2       'NP'
""")

parser.productionstring(name="project and complete: VP ==> V NP gapped", string="""
    =g>
    isa             parsing_goal
    task            parsing
    stack1          'VP'
    stack2          =s2
    stack3          =s3
    stack4          =s4
    found           'V'
    gapped          True
    ==>
    +retrieval>
    isa             parse_state
    node_cat        'wh'
    =g>
    isa             parsing_goal
    stack1          =s2
    stack2          =s3
    stack3          =s4
    found           None
    gapped          False
    +imaginal>
    isa             parse_state
    mother          'S'
    node_cat        'VP'
    daughter1       'V'
    daughter2       'NP'
""")

parser.productionstring(name="press spacebar", string="""
    =g>
    isa             parsing_goal
    task            ~reading_word
    ?manual>
    state           free
    ?retrieval>
    state           free
    ==>
    =g>
    isa             parsing_goal
    task            reading_word
    +manual>
    isa             _manual
    cmd             'press_key'
    key             'space'
""", utility=-5)


parser.productionstring(name="finished", string="""
    =g>
    isa             parsing_goal
    task            reading_word
    stack1       None
    ==>
    ~g>
    ~imaginal>
""")

if __name__ == "__main__":

    sentence = "The boy who likes the boy saw Mary"
    sentence = sentence.split()

    stimuli = []
    for word in sentence:
        stimuli.append({1: {'text': word, 'position': (320, 180)}})
    parser_sim = parser.simulation(
        realtime=False,
        gui=False,
        environment_process=environment.environment_process,
        stimuli=stimuli,
        triggers='space')

    recorded = ["likes", "saw"]
    dict_recorded = {key: [0, 0] for key in recorded}
    recorded_word = None
    while True:
        try:
            parser_sim.step()
        except simpy.core.EmptySchedule:
            break
        if re.search("^RULE FIRED: press spacebar", str(parser_sim.current_event.action)):
                print(parser.goals["g"])
                input()

        if recorded_word in dict_recorded and not re.search(recorded_word, str(environment.stimulus)) and dict_recorded[recorded_word][0] and not dict_recorded[recorded_word][1]:
                dict_recorded[recorded_word][1] = parser_sim.show_time()
                #print(parser.goals["g"])
                #print(dict_recorded)
                #input()
        elif re.search("|".join(["(".join([x, ")"]) for x in recorded]), str(environment.stimulus)):
            recorded_word = str(environment.stimulus[1]['text'])
            if recorded_word in dict_recorded and not dict_recorded[recorded_word][0]:
                dict_recorded[recorded_word][0] = parser_sim.show_time()

    dict_recorded = {key: dict_recorded[key][1]-dict_recorded[key][0] for key in dict_recorded}
    print(dict_recorded)
    input()

    sortedDM = sorted(([item[0], time] for item in dm.items() for time in item[1]),
                      key=lambda item: item[1])
    print("\nParse states in declarative memory at the end of the simulation",
          "\nordered by time of (re)activation:")
    for chunk in sortedDM:
        if chunk[0].typename == "parse_state":
            print(chunk[1], "\t", chunk[0])
    print("\nWords in declarative memory at the end of the simulation",
          "\nordered by time of (re)activation:")
    for chunk in sortedDM:
        if chunk[0].typename == "word":
            print(chunk[1], "\t", chunk[0])

