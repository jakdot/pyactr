"""
A simple top-down parser.
"""

import pyactr as actr

actr.chunktype("parsing_goal", "stack_top stack_bottom parsed_word task")
actr.chunktype("sentence", "word1 word2 word3")
actr.chunktype("word", "form, cat")

parser = actr.ACTRModel()
dm = parser.decmem
g = parser.goal
imaginal = parser.set_goal(name="imaginal", delay=0.2)

dm.add(actr.chunkstring(string="""
    isa word
    form 'Mary'
    cat 'ProperN'
"""))
dm.add(actr.chunkstring(string="""
    isa word
    form 'Bill'
    cat 'ProperN'
"""))
dm.add(actr.chunkstring(string="""
    isa word
    form 'likes'
    cat 'V'
"""))

g.add(actr.chunkstring(string="""
    isa parsing_goal
    task parsing
    stack_top 'S'
"""))
imaginal.add(actr.chunkstring(string="""
    isa sentence
    word1 'Mary'
    word2 'likes'
    word3 'Bill'
"""))

parser.productionstring(name="expand: S ==> NP VP", string="""
    =g>
    isa parsing_goal
    task parsing
    stack_top 'S'
    ==>
    =g>
    isa parsing_goal
    stack_top 'NP'
    stack_bottom 'VP'
""")

parser.productionstring(name="expand: NP ==> ProperN", string="""
    =g>
    isa parsing_goal
    task parsing
    stack_top 'NP'
    ==>
    =g>
    isa parsing_goal
    stack_top 'ProperN'
""")

parser.productionstring(name="expand: VP ==> V NP", string="""
    =g>
    isa parsing_goal
    task parsing
    stack_top 'VP'
    ==>
    =g>
    isa parsing_goal
    stack_top 'V'
    stack_bottom 'NP'
""")

parser.productionstring(name="retrieve: ProperN", string="""
    =g>
    isa parsing_goal
    task parsing
    stack_top 'ProperN'
    =imaginal>
    isa sentence
    word1 =w1
    ==>
    =g>
    isa parsing_goal
    task retrieving
    +retrieval>
    isa word
    form =w1
""")

parser.productionstring(name="retrieve: V", string="""
    =g>
    isa parsing_goal
    task parsing
    stack_top 'V'
    =imaginal>
    isa sentence
    word1 =w1
    ==>
    =g>
    isa parsing_goal
    task retrieving
    +retrieval>
    isa word
    form =w1
""")

parser.productionstring(name="scan: word", string="""
    =g>
    isa parsing_goal
    task retrieving
    stack_top =y
    stack_bottom =x
    =retrieval>
    isa word
    form =w1
    cat =y
    =imaginal>
    isa sentence
    word1 =w1
    word2 =w2
    word3 =w3
    ==>
    =g>
    isa parsing_goal
    task printing
    stack_top =x
    stack_bottom empty
    parsed_word =w1
    =imaginal>
    isa sentence
    word1 =w2
    word2 =w3
    word3 empty
    ~retrieval>
""")

parser.productionstring(name="print parsed word", string="""
    =g>
    isa parsing_goal
    task printing
    =imaginal>
    isa sentence
    word1 ~empty
    ==>
    !g>
    show parsed_word
    =g>
    isa parsing_goal
    task parsing
    parsed_word None
""")

parser.productionstring(name="done", string="""
    =g>
    isa parsing_goal
    task printing
    =imaginal>
    isa sentence
    word1 empty
    ==>
    =g>
    isa parsing_goal
    task done
    !g>
    show parsed_word
    ~imaginal>
    ~g>
""")


if __name__ == "__main__":
    parser_sim = parser.simulation()
    parser_sim.run()
    print("\nDeclarative memory at the end of the simulation:")
    print(dm)
