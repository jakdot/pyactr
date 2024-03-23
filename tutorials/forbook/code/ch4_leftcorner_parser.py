"""
A left-corner parser.
"""

import pyactr as actr
from ete3 import Tree

environment = actr.Environment(focus_position=(320, 180))

actr.chunktype("parsing_goal",
               "task stack_top stack_bottom parsed_word right_frontier")
actr.chunktype("parse_state",
               "node_cat mother daughter1 daughter2 lex_head")
actr.chunktype("word", "form cat")

parser = actr.ACTRModel(environment)
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
    form 'Bill'
    cat  'ProperN'
"""))
dm.add(actr.chunkstring(string="""
    isa  word
    form 'likes'
    cat  'V'
"""))
g.add(actr.chunkstring(string="""
    isa             parsing_goal
    task            read_word
    stack_top       'S'
    right_frontier  'S'
"""))


parser.productionstring(name="press spacebar", string="""
    =g>
    isa             parsing_goal
    task            read_word
    stack_top       ~None
    ?manual>
    state           free
    ==>
    +manual>
    isa             _manual
    cmd             'press_key'
    key             'space'
""")

parser.productionstring(name="encode word", string="""
    =g>
    isa             parsing_goal
    task            read_word
    =visual>
    isa             _visual
    value           =val
    ==>
    =g>
    isa             parsing_goal
    task            get_word_cat
    parsed_word    =val
    ~visual>
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
    stack_top       =t
    stack_bottom    None
    =retrieval>
    isa             word
    form            =w
    cat             =c
    ==>
    =g>
    isa             parsing_goal
    task            parsing
    stack_top       =c
    stack_bottom    =t
    +imaginal>
    isa             parse_state
    node_cat        =c
    daughter1       =w
    ~retrieval>
""")

parser.productionstring(name="project: NP ==> ProperN", string="""
    =g>
    isa             parsing_goal
    stack_top       'ProperN'
    stack_bottom    ~'NP'
    right_frontier  =rf
    parsed_word     =w
    ==>
    =g>
    isa             parsing_goal
    stack_top       'NP'
    +imaginal>
    isa             parse_state
    node_cat        'NP'
    daughter1       'ProperN'
    mother          =rf
    lex_head        =w
""")

parser.productionstring(name="project and complete: NP ==> ProperN", string="""
    =g>
    isa             parsing_goal
    stack_top       'ProperN'
    stack_bottom    'NP'
    right_frontier  =rf
    parsed_word     =w
    ==>
    =g>
    isa             parsing_goal
    task            read_word
    stack_top       None
    stack_bottom    None
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
    stack_top       'NP'
    stack_bottom    'S'
    ==>
    =g>
    isa             parsing_goal
    task            read_word
    stack_top       'VP'
    stack_bottom    None
    right_frontier  'VP'
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
    stack_top       'V'
    stack_bottom    'VP'
    ==>
    =g>
    isa             parsing_goal
    task            read_word
    stack_top       'NP'
    stack_bottom    None
    +imaginal>
    isa             parse_state
    node_cat        'VP'
    daughter1       'V'
    daughter2       'NP'
""")

parser.productionstring(name="finished", string="""
    =g>
    isa             parsing_goal
    task            read_word
    stack_top       None
    ==>
    ~g>
    ~imaginal>
""")

if __name__ == "__main__":
    stimuli = [{1: {'text': 'Mary', 'position': (320, 180)}},
               {1: {'text': 'likes', 'position': (320, 180)}},
               {1: {'text': 'Bill', 'position': (320, 180)}}]
    parser_sim = parser.simulation(
        realtime=True,
        gui=False,
        environment_process=environment.environment_process,
        stimuli=stimuli,
        triggers='space')
    parser_sim.run(1.1)

    sortedDM = sorted(([item[0], time] for item in dm.items()\
                                       for time in item[1]),\
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

    def final_tree(sortedDM):
        tree_list = []
        parse_states = [chunk for chunk in sortedDM\
                              if chunk[0].typename == "parse_state" and\
                                 chunk[0].daughter1 != None]
        words = set(str(chunk[0].form) for chunk in sortedDM\
                                       if chunk[0].typename == "word")
        nodes = [chunk for chunk in parse_states
                    if chunk[0].node_cat == "S"]
        while nodes:
            current_chunk = nodes.pop(0)
            current_node = str(current_chunk[0].node_cat) + " " +\
                        str(current_chunk[1])
            current_tree = Tree(name=current_node)
            if current_chunk[0].daughter2 != None:
                child_categs = [current_chunk[0].daughter1,\
                                current_chunk[0].daughter2]
            else:
                child_categs = [current_chunk[0].daughter1]
            children = []
            for cat in child_categs:
                if cat == 'NP':
                    chunkFromCat = [chunk for chunk in parse_states\
                                    if chunk[0].node_cat == cat and\
                                    chunk[0].mother ==\
                                        current_chunk[0].node_cat]
                    if chunkFromCat:
                        children += chunkFromCat
                        current_child = str(chunkFromCat[-1][0].node_cat)\
                                        + " " + str(chunkFromCat[-1][1])
                        current_tree.add_child(name=current_child)
                elif cat == 'ProperN':
                    chunkFromCat = [chunk for chunk in parse_states if\
                                    chunk[0].node_cat == cat and\
                                    chunk[0].daughter1 ==\
                                        current_chunk[0].lex_head]
                    if chunkFromCat:
                        children += chunkFromCat
                        current_child = str(chunkFromCat[-1][0].node_cat)\
                                        + " " + str(chunkFromCat[-1][1])
                        current_tree.add_child(name=current_child)
                elif cat in words:
                    last_act_time = [chunk[1][-1]
                                    for chunk in dm.items()\
                                    if chunk[0].typename == "word"\
                                    and str(chunk[0].form) == cat]
                    current_child = cat + " " + str(last_act_time[0])
                    current_tree.add_child(name=current_child)
                else:
                    chunkFromCat = [chunk for chunk in parse_states\
                                    if chunk[0].node_cat == cat]
                    if chunkFromCat:
                        children += chunkFromCat
                        current_child = str(chunkFromCat[-1][0].node_cat)\
                                        + " " + str(chunkFromCat[-1][1])
                        current_tree.add_child(name=current_child)
            tree_list.append(current_tree)
            nodes += children
        final_tree = tree_list[0]
        tree_list.remove(final_tree)
        while tree_list:
            leaves = final_tree.get_leaves()
            for leaf in leaves:
                subtree_list = [tree for tree in tree_list\
                                     if tree.name == leaf.name]
                if subtree_list:
                    subtree = subtree_list[0]
                    tree_list.remove(subtree)
                    leaf.add_sister(subtree)
                    leaf.detach()
        return final_tree
    print("\nFinal tree:")
    print(final_tree(sortedDM).get_ascii(compact=False))
