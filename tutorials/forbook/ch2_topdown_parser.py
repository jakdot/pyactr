"""
A simple top-down parser.
"""

import pyactr as actr

actr.chunktype("parsing", "task stack_top stack_bottom parsed_word ")
actr.chunktype("sentence", "word1 word2 word3")

parser = actr.ACTRModel()

dm = parser.decmem
dm.add(actr.chunkstring(string="isa word form 'Mary' cat 'ProperN'"))
dm.add(actr.chunkstring(string="isa word form 'Bill' cat 'ProperN'"))
dm.add(actr.chunkstring(string="isa word form 'likes' cat 'V'"))

parser.goal.add(actr.chunkstring(string="isa parsing  task parse stack_top 'S'"))
parser.goal = "g2"
parser.goals["g2"].delay = 0.2
parser.goals["g2"].add(actr.chunkstring(string="isa sentence word1 'Mary' word2 'likes' word3 'Bill'"))

parser.productionstring(name="expand: S->NP VP", string="""
        =g>
        isa         parsing
        task        parse
        stack_top   'S'
        ==>
        =g>
        isa         parsing
        stack_top   'NP'
        stack_bottom 'VP'
    """)

parser.productionstring(name="expand: NP->ProperN", string="""
        =g>
        isa         parsing
        task        parse
        stack_top   'NP'
        ==>
        =g>
        isa         parsing
        stack_top   'ProperN'
    """)

parser.productionstring(name="retrieve: ProperN", string="""
        =g>
        isa         parsing
        task        parse
        stack_top   'ProperN'
        =g2>
        isa         sentence
        word1       =w1
        ==>
        =g>
        isa         parsing
        task        retrieving
        =g2>
        isa         sentence
        +retrieval>
        isa         word
        form        =w1
    """)

parser.productionstring(name="retrieve: V", string="""
        =g>
        isa         parsing
        task        parse
        stack_top   'V'
        =g2>
        isa         sentence
        word1       =w1
        ==>
        =g>
        isa         parsing
        task        retrieving
        =g2>
        isa         sentence
        +retrieval>
        isa         word
        form        =w1
    """)

parser.productionstring(name="scan: string", string="""
        =g>
        isa         parsing
        task        retrieving
        stack_top   =y
        stack_bottom =x
        =retrieval>
        isa         word
        form        =w1
        cat         =y
        =g2>
        isa         sentence
        word1       =w1
        word2       =w2
        word3       =w3
        ==>
        =g>
        isa         parsing
        task        print
        stack_top   =x
        stack_bottom None
        parsed_word =w1
        =g2>
        isa         sentence
        word1       =w2
        word2       =w3
        word3       None
    """)

parser.productionstring(name="expand: VP -> V NP", string="""
        =g>
        isa         parsing
        task        parse
        stack_top   'VP'
        ==>
        =g>
        isa         parsing
        stack_top   'V'
        stack_bottom 'NP'
    """)

parser.productionstring(name="print parsed word", string="""
        =g>
        isa         parsing
        task        print
        =g2>
        isa         sentence
        word1      ~None
        ==>
        =g2>
        isa         sentence
        !g>
        show        parsed_word
        =g>
        isa         parsing
        task        parse
        parsed_word None""")

parser.productionstring(name="done", string="""
        =g>
        isa         parsing
        task        print
        =g2>
        isa         sentence
        word1       None
        ==>
        !g>
        show        parsed_word
        ~g2>
        ~g>""")

if __name__ == "__main__":
    x = parser.simulation()
    x.run()
    print(dm)
