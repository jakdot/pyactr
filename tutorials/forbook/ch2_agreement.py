"""
An example of a very simple model that simulates subject-verb agreement. We abstract away from syntactic parsing.
"""

import pyactr as actr

import random

car = actr.makechunk(nameofchunk="car",\
                      typename="word", phonology="/ka:/", meaning="[[car]]", category="noun", number="sg", syncat="subject")

agreement = actr.ACTRModel()

dm = agreement.decmem
dm.add(car)

agreement.goal.add(actr.chunkstring(string="isa word task agree category 'verb'"))

agreement.productionstring(name="agree", string="""
    =g>
    isa  word
    task trigger_agreement
    category 'verb'
    =retrieval>
    isa  word
    category 'noun'
    syncat 'subject'
    number =x
    ==>
    =g>
    isa  word
    task done
    category 'verb'
    number =x
    """)

agreement.productionstring(name="retrieve", string="""
    =g>
    isa  word
    task agree
    category 'verb'
    ?retrieval>
    buffer empty
    ==>
    =g>
    isa  word
    task trigger_agreement
    category 'verb'
    +retrieval>
    isa  word
    category 'noun'
    syncat 'subject'
    """)

agreement.productionstring(name="done", string="""
    =g>
    isa  word
    task done
    category 'verb'
    number =x
    ==>
    ~g>""")

if __name__ == "__main__":
    x = agreement.simulation()
    x.run()
