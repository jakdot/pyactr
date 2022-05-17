"""
This example shows the workings of pyMC3 in pyactr. pyMC3 allows Bayesian inference on user-defined probabilistic models. Combining this with pyactr will allow you to get the posterior on free parameters assumed in pyactr.

You will need to install pymc3 and packages it depends on to make this work.
"""

import numpy as np
import simpy
import pyactr as actr
from pymc3 import Model, Normal, Gamma, Uniform, sample, summary, Metropolis, traceplot
import theano.tensor as T
from theano.compile.ops import as_op
import matplotlib.pyplot as pp


#Each chunk type should be defined first.
actr.chunktype("countOrder", ("first", "second"))

#creating goal buffer
actr.chunktype("countFrom", ("start", "end", "count"))

def counting_model(sub=True):
    """
    sub: is subsymbolic switched on?
    """
    counting = actr.ACTRModel(subsymbolic=sub)


    #production rules follow; using productionstring, they are similar to Lisp ACT-R

    counting.productionstring(name="start", string="""
    =g>
    isa countFrom
    start =x
    count None
    ==>
    =g>
    isa countFrom
    count =x
    +retrieval>
    isa countOrder
    first =x""")

    counting.productionstring(name="increment", string="""
    =g>
    isa     countFrom
    count       =x
    end         ~=x
    =retrieval>
    isa     countOrder
    first       =x
    second      =y
    ==>
    =g>
    isa     countFrom
    count       =y
    +retrieval>
    isa     countOrder
    first       =y""")

    counting.productionstring(name="stop", string="""
    =g>
    isa     countFrom
    count       =x
    end         =x
    ==>
    ~g>""")

    return counting

dd = {actr.chunkstring(string="\
    isa countOrder\
    first 1\
    second 2"): [0], actr.chunkstring(string="\
    isa countOrder\
    first 2\
    second 3"): [0],
    actr.chunkstring(string="\
    isa countOrder\
    first 3\
    second 4"): [0],
    actr.chunkstring(string="\
    isa countOrder\
    first 4\
    second 5"): [0]} #we have to store memory chunks separately, see below

# Simulating data

counting = counting_model(True)

counting.decmems = {}
counting.set_decmem(dd)

counting.goal.add(actr.chunkstring(string="isa countFrom start 2 end 4"))
#counting.model_parameters["latency_factor"] = 0.2
sim = counting.simulation(trace=True)
# an example of one run of the simulation
sim.run()

size=5000

Y = np.random.normal(loc=257.4, scale=10, size=size) #suppose these are data on counting, that is, how fast people are in counting from 2 to 4; we simulate them as normal distribution with mean 257.4 (milliseconds) and st.d. 10 (milliseconds)
print("Simulated data")
print(Y)
# We would get the mean of 257.4 milliseconds if the latency factor would be equal to 0.1.

# We now want to know what the posterior distribution of latency factor should be.
# We find this using pymc3 combining a Bayesian model and our ACT-R counting model.
# Ideally, we should get close to 0.1 for lf

# The part below runs the ACT-R model; this is not run on its own but called from inside the Bayesian model
@as_op(itypes=[T.dscalar], otypes=[T.dvector])
def model(lf):
    """
    We will create a model on two rules. We will let the pyMC find the best value for firing a rule.
    """
    #adding stuff to goal buffer
    counting.decmems = {} #we have to clean all the memories first, because each loop adds chunks into a memory and we want to ignore these
    counting.set_decmem(dd) #we then add only memory chunks that are present at the beginning
    counting.goal.add(actr.chunkstring(string="isa countFrom start 2 end 4")) # starting goal
    counting.model_parameters["latency_factor"] = lf
    sim = counting.simulation(trace=False)
    last_time = 0
    while True:
        if last_time > 10: #if the value is unreasonably high, which might happen with weird proposed estimates, break
            last_time = 10.0
            break
        try:
            sim.step() # run one step ahead in simulation
            last_time = sim.show_time()
        except simpy.core.EmptySchedule: #if you run out of actions, break
            last_time = 10.0 #some high value time so it is clear that this is not the right way to end
            break
        if not counting.goal: #if goal cleared (as should happen when you finish the task correctly and reach stop, break)
            break

    return np.repeat(np.array(1000*last_time), size) # we return time in ms

basic_model = Model()

with basic_model:

    # Priors for unknown model parameters
    lf = Gamma('lf', alpha=2, beta=4)

    sigma = Uniform('sigma', lower=0.1,upper=50)

    #you can print searched values from every draw
    #lf_print = T.printing.Print('lf')(lf)

    #Deterministic value (RT in ms) established by the ACT-R model
    mu = model(lf)
    
    # Likelihood (sampling distribution) of observations
    Normal('Y_obs', mu=mu, sd=sigma, observed=Y)

    #Metropolis algorithm for steps in simulation
    step = Metropolis(basic_model.vars)

    trace = sample(1000, tune=1000, step=step, init='auto') 

print(summary(trace))
traceplot(trace)
pp.savefig("plot_u8_estimating_using_pymc3.png")
print(trace['lf'], trace['sigma'])
print("Latency factor: mean ", np.mean( trace['lf'] ))
print("This value should be close to 0.1")
print("Sigma estimate: mean ",np.mean( trace['sigma'] ) )
print("This value should be close to 10")

# Of course, much more things can be explored this way:
# more parameters could be studied; different priors could be used etc.
