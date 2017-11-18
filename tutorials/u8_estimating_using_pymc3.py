"""
This example shows the workings of pyMC3 in pyactr. pyMC3 allows Bayesian inference on user-defined probabilistic models. Combining this with pyactr will allow you to get the posterior on free parameters assumed in pyactr.

You will need to install pymc3 and packages it depends on to make this work.
"""

import math

import numpy as np
import scipy
import simpy
import pyactr as actr
from pymc3 import Model, Normal, HalfNormal, Gamma, find_MAP, sample, summary, Metropolis, Slice, traceplot, gelman_rubin
import theano.tensor as T
from theano.compile.ops import as_op
import matplotlib.pyplot as pp

def counting_model(sub):
    counting = actr.ACTRModel(subsymbolic=sub)

    #Each chunk type should be defined first.
    actr.chunktype("countOrder", ("first", "second"))
    #Chunk type is defined as (name, attributes)

    #Attributes are written as an iterable (above) or as a string, separated by comma:
    actr.chunktype("countOrder", "first, second")

    #creating goal buffer
    actr.chunktype("countFrom", ("start", "end", "count"))

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

#Simulating data

size = 5000

Y = np.random.randn(size) + 0.5 #suppose these are data on the rule counting from u1, that is, how fast people are on counting from 2 to 4

#We now want to know what the speed of firing rule should be to fit these simulations.

counting = counting_model(True)

@as_op(itypes=[T.dscalar], otypes=[T.dvector]) #what should go in (itypes) and out (otpyes) into deterministic part
def model(rule_firing):
    """
    We will create a model on two rules. We will let the pyMC find the best value for firing a rule.
    """
    counting.decmems = {}
    counting.set_decmem(dd)
    #adding stuff to goal buffer
    counting.goal.add(actr.chunkstring(string="isa countFrom start 2 end 4"))
    counting.model_parameters["rule_firing"] = rule_firing
    sim = counting.simulation(trace=False)
    while True:
        last_time = sim.show_time()
        try:
            sim.step()
        except simpy.core.EmptySchedule:
            break
        if not counting.goal:
            break
    return np.repeat(np.array(last_time), size) #what is outputed -- nparray of simulated time points

basic_model = Model()

with basic_model:

    # Priors for unknown model parameters
    rule_firing = HalfNormal('rule_firing', sd=2)

    sigma = HalfNormal('sigma', sd=1)

    #Deterministic value, found in the model
    mu = model(rule_firing)

    # Likelihood (sampling distribution) of observations
    Normal('Y_obs', mu=mu, sd=sigma, observed=Y)

map_estimate = find_MAP(model=basic_model, fmin=scipy.optimize.fmin_powell)

print(map_estimate)

print("Estimated rule firing:", math.exp(map_estimate['rule_firing_log_']))

print("Let's see whether the estimate is reasonably close to the simulated data. The final rule 'stop' should fire close to 500 ms. The model tends to be off.")

counting.decmems = {}
counting.set_decmem(dd)

counting.goal.add(actr.chunkstring(string="isa countFrom start 2 end 4"))
counting.model_parameters["rule_firing"] = math.exp(map_estimate['rule_firing_log_'])
sim = counting.simulation(trace=True)
sim.run()

#We could consider other parameters. Let's check latency factor *and* rule firing.

counting = counting_model(True)

@as_op(itypes=[T.dscalar, T.dscalar], otypes=[T.dvector])
def model(rule_firing, lf):
    """
    We will create a model on two rules. We will let the pyMC find the best value for firing a rule.
    """
    #adding stuff to goal buffer
    counting.decmems = {} #we have to clean all the memories first, because each loop adds chunks into a memory and we want to ignore these
    counting.set_decmem(dd) #we then add only memory chunks that are present at the beginning
    counting.goal.add(actr.chunkstring(string="isa countFrom start 2 end 4"))
    counting.model_parameters["latency_factor"] = lf
    counting.model_parameters["rule_firing"] = rule_firing
    sim = counting.simulation(trace=False)
    while True:
        last_time = sim.show_time()
        if last_time > 10: #if the value is unreasonably high, break
            last_time = 10.0
            break
        try:
            sim.step()
        except simpy.core.EmptySchedule:
            last_time = 10.0 #some high value so it is clear that this is not the right way
            break
        if not counting.goal:
            break
    return np.repeat(np.array(last_time), size)

basic_model = Model()

with basic_model:

    # Priors for unknown model parameters
    rule_firing = HalfNormal('rule_firing', sd=2)
    lf = HalfNormal('lf', sd=2)

    sigma = HalfNormal('sigma', sd=1)

    #Deterministic value, found in the model
    mu = model(rule_firing, lf)

    # Likelihood (sampling distribution) of observations
    Normal('Y_obs', mu=mu, sd=sigma, observed=Y)
    
map_estimate = find_MAP(model=basic_model, fmin=scipy.optimize.fmin_powell)

print(map_estimate)

print("Estimated rule firing:", math.exp(map_estimate['rule_firing_log_']))
print("Estimated latency factor:", math.exp(map_estimate['lf_log_']))

print("Let's see whether the estimate is reasonably close to the simulated data. The final rule 'stop' should fire close to 500 ms. The model can still be somewhat off, even though usually it gets close within 10 percent of the value. It is often better than the model that only estimates the time it takes to fire a rule.")

counting.decmems = {}
counting.set_decmem(dd)

counting.goal.add(actr.chunkstring(string="isa countFrom start 2 end 4"))
counting.model_parameters["rule_firing"] = math.exp(map_estimate['rule_firing_log_'])
counting.model_parameters["latency_factor"] = math.exp(map_estimate['lf_log_'])
sim = counting.simulation(trace=True)
sim.run()

print("Search for parameters using Slice/Metropolis.")

basic_model = Model()

with basic_model:

    # Priors for unknown model parameters
    rule_firing = HalfNormal('rule_firing', sd=2, testval=abs(np.random.randn(1)[0]))
    lf = HalfNormal('lf', sd=2, testval=abs(np.random.randn(1)[0]))

    sigma = HalfNormal('sigma', sd=1)

    #you can print searched values after every iteration
    lf_print = T.printing.Print('lf')(lf)
    #Deterministic value, found in the model
    mu = model(rule_firing, lf_print)
    
    #Deterministic value, found in the model
    #mu = model(rule_firing, lf)

    # Likelihood (sampling distribution) of observations
    Normal('Y_obs', mu=mu, sd=sigma, observed=Y)

    #Slice should be used for continuous variables but it gets stuck sometimes - you can also use Metropolis
    step = Metropolis(basic_model.vars)

    #step = Slice(basic_model.vars)

    trace = sample(10, step, njobs=2, init='auto')

print(summary(trace))
traceplot(trace)
pp.savefig("plot_u8_estimating_using_pymc3.png")
print(trace['lf'], trace['rule_firing'])
print(gelman_rubin(trace))

print("Of course, much more things can be explored this way: more parameters could be studied; their priors could be better adjusted etc.")
