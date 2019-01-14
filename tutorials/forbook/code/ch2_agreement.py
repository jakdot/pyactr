"""
A basic model that simulates subject-verb agreement.
We abstract away from syntactic parsing, among other things.
"""

import pyactr as actr

actr.chunktype("word", "phonology, meaning, category, number, synfunction")
actr.chunktype("goal_lexeme", "task, category, number")

carLexeme = actr.makechunk(
    nameofchunk="car",
    typename="word",
    phonology="/kar/",
    meaning="[[car]]",
    category="noun",
    number="sg",
    synfunction="subject")

agreement = actr.ACTRModel()

dm = agreement.decmem
dm.add(carLexeme)

agreement.goal.add(actr.chunkstring(string="""
    isa goal_lexeme
    task agree
    category 'verb'"""))

agreement.productionstring(name="retrieve", string="""
    =g>
    isa goal_lexeme
    category 'verb'
    task agree
    ?retrieval>
    buffer empty
    ==>
    =g>
    isa goal_lexeme
    task trigger_agreement
    category 'verb'
    +retrieval>
    isa word
    category 'noun'
    synfunction 'subject'
    """)

agreement.productionstring(name="agree", string="""
    =g>
    isa goal_lexeme
    task trigger_agreement
    category 'verb'
    =retrieval>
    isa word
    category 'noun'
    synfunction 'subject'
    number =x
    ==>
    =g>
    isa goal_lexeme
    category 'verb'
    number =x
    task done
    """)

agreement.productionstring(name="done", string="""
    =g>
    isa goal_lexeme
    task done
    ==>
    ~g>""")

if __name__ == "__main__":
    agreement_sim = agreement.simulation()
    agreement_sim.run()
    print("\nDeclarative memory at the end of the simulation:")
    print(dm)
