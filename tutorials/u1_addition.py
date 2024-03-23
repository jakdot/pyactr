"""
An example of a model using goal and retrieval. It corresponds to 'addition' in ACT-R tutorials, Unit 1.
"""

import pyactr as actr

addition = actr.ACTRModel()

actr.chunktype("countOrder", ("first", "second"))

actr.chunktype("add", ("arg1", "arg2", "sum", "count"))

dm = addition.decmem

for i in range(0, 11):
    dm.add(actr.makechunk("chunk"+str(i), "countOrder", first=i, second=i+1))

addition.goal.add(actr.makechunk("", "add", arg1=5, arg2=2))

addition.productionstring(name="init_addition", string="""
        =g>
        isa     add
        arg1    =num1
        arg2    =num2
        sum     None
        ==>
        =g>
        isa     add
        sum     =num1
        count   0
        +retrieval>
        isa     countOrder
       first   =num1""")

addition.productionstring(name="terminate_addition", string="""
        =g>
        isa     add
        count   =num
        arg2    =num
        sum     =answer
        ==>
        ~g>""")

addition.productionstring(name="increment_count", string="""
        =g>
        isa     add
        count   =count
        sum     =sum
        =retrieval>
        isa     countOrder
        first   =count
        second  =newcount
        ==>
        =g>
        isa     add
        count   =newcount
        +retrieval>
        isa     countOrder
        first   =sum""")

addition.productionstring(name="increment_sum", string="""
        =g>
        isa     add
        count   =count
        arg2    ~=count
        sum     =sum
        =retrieval>
        isa     countOrder
        first   =sum
        second  =newsum
        ==>
        =g>
        isa     add
        sum     =newsum
        +retrieval>
        isa     countOrder
        first   =count""")

if __name__ == "__main__":
    x = addition.simulation()
    x.run()
