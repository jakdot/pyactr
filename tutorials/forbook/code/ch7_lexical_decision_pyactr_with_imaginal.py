"""
A model of lexical decision: Bayes+ACT-R, with imaginal buffer;
default delay for the imaginal buffer (200 ms)
"""

import warnings
import sys

import matplotlib as mpl
mpl.use("pgf")
pgf_with_pdflatex = {"text.usetex": True, "pgf.texsystem": "pdflatex",
                     "pgf.preamble": [r"\usepackage{mathpazo}",
                                      r"\usepackage[utf8x]{inputenc}",
                                      r"\usepackage[T1]{fontenc}",
                                      r"\usepackage{amsmath}"],
                     "axes.labelsize": 8,
                     "font.family": "serif",
                     "font.serif":["Palatino"],
                     "font.size": 8,
                     "legend.fontsize": 8,
                     "xtick.labelsize": 8,
                     "ytick.labelsize": 8}
mpl.rcParams.update(pgf_with_pdflatex)
import matplotlib.pyplot as plt
plt.style.use('seaborn')
import seaborn as sns
sns.set_style({"font.family":"serif", "font.serif":["Palatino"]})

import pandas as pd
import pyactr as actr
import math
from simpy.core import EmptySchedule
import numpy as np
import re
import scipy.stats as stats
import scipy

import pymc3 as pm
from pymc3 import Gamma, Normal, HalfNormal, Deterministic, Uniform, find_MAP,\
                  Slice, sample, summary, Metropolis, traceplot, gelman_rubin
from pymc3.backends.base import merge_traces
from pymc3.backends import SQLite
from pymc3.backends.sqlite import load
import theano
import theano.tensor as tt
from theano.compile.ops import as_op

warnings.filterwarnings("ignore")

FREQ = np.array([242, 92.8, 57.7, 40.5, 30.6, 23.4, 19,\
                 16, 13.4, 11.5, 10, 9, 7, 5, 3, 1])
RT = np.array([542, 555, 566, 562, 570, 569, 577, 587,\
               592, 605, 603, 575, 620, 607, 622, 674])
ACCURACY = np.array([97.22, 95.56, 95.56, 96.3, 96.11, 94.26,\
                     95, 92.41, 91.67, 93.52, 91.85, 93.52,\
                     91.48, 90.93, 84.44, 74.63])/100

environment = actr.Environment(focus_position=(320, 180))
lex_decision = actr.ACTRModel(environment=environment,\
                       subsymbolic=True,\
                       automatic_visual_search=True,\
                       activation_trace=False,\
                       retrieval_threshold=-80,\
                       motor_prepared=True,
                       eye_mvt_scaling_parameter=0.18,\
                       emma_noise=False)

actr.chunktype("goal", "state")
actr.chunktype("word", "form")

# on average, 15 years of exposure is 112.5 million words

SEC_IN_YEAR = 365*24*3600
SEC_IN_TIME = 15*SEC_IN_YEAR

FREQ_DICT = {}
FREQ_DICT['guy'] = 242*112.5
FREQ_DICT['somebody'] = 92*112.5
FREQ_DICT['extend'] = 58*112.5
FREQ_DICT['dance'] = 40.5*112.5
FREQ_DICT['shape'] = 30.6*112.5
FREQ_DICT['besides'] = 23.4*112.5
FREQ_DICT['fit'] = 19*112.5
FREQ_DICT['dedicate'] = 16*112.5
FREQ_DICT['robot'] = 13.4*112.5
FREQ_DICT['tile'] = 11.5*112.5
FREQ_DICT['between'] = 10*112.5
FREQ_DICT['precedent'] = 9*112.5
FREQ_DICT['wrestle'] = 7*112.5
FREQ_DICT['resonate'] = 5*112.5
FREQ_DICT['seated'] = 3*112.5
FREQ_DICT['habitually'] = 1*112.5

ORDERED_FREQ = sorted(list(FREQ_DICT), key=lambda x:FREQ_DICT[x], reverse=True)

def time_freq(freq):
    rehearsals = np.zeros((np.int(np.max(freq) * 113), len(freq)))
    for i in np.arange(len(freq)):
        temp = np.arange(np.int((freq[i]*112.5)))
        temp = temp * np.int(SEC_IN_TIME/(freq[i]*112.5))
        rehearsals[:len(temp),i] = temp
    return(rehearsals.T)

time = theano.shared(time_freq(FREQ), 'time')

LEMMA_CHUNKS = [(actr.makechunk("", typename="word", form=word))
                for word in ORDERED_FREQ]
lex_decision.set_decmem({x: np.array([]) for x in LEMMA_CHUNKS})

lex_decision.goals = {}
lex_decision.set_goal("g")
lex_decision.set_goal("imaginal")

lex_decision.productionstring(name="attend word", string="""
    =g>
    isa     goal
    state   'attend'
    =visual_location>
    isa    _visuallocation
    ?visual>
    state   free
    ==>
    =g>
    isa     goal
    state   'encoding'
    +visual>
    isa     _visual
    cmd     move_attention
    screen_pos =visual_location
    ~visual_location>
""")

lex_decision.productionstring(name="encoding word", string="""
    =g>
    isa     goal
    state   'encoding'
    =visual>
    isa     _visual
    value   =val
    ==>
    =g>
    isa     goal
    state   'retrieving'
    +imaginal>
    isa     word
    form    =val
""")

lex_decision.productionstring(name="retrieving", string="""
    =g>
    isa     goal
    state   'retrieving'
    =imaginal>
    isa     word
    form    =val
    ==>
    =g>
    isa     goal
    state   'retrieval_done'
    +retrieval>
    isa     word
    form    =val
""")

lex_decision.productionstring(name="lexeme retrieved", string="""
    =g>
    isa     goal
    state   'retrieval_done'
    ?retrieval>
    buffer  full
    state   free
    ==>
    =g>
    isa     goal
    state   'done'
    +manual>
    isa     _manual
    cmd     press_key
    key     'J'
""")

lex_decision.productionstring(name="no lexeme found", string="""
    =g>
    isa     goal
    state   'retrieval_done'
    ?retrieval>
    buffer  empty
    state   error
    ==>
    =g>
    isa     goal
    state   'done'
    +manual>
    isa     _manual
    cmd     press_key
    key     'F'
""")

def run_stimulus(word):
    """
    Function running one instance of lexical decision for a word.
    """
    # reset model state to initial state for a new simulation
    # (flush buffers without moving their contents to dec mem)
    try:
        lex_decision.retrieval.pop()
    except KeyError:
        pass
    try:
        lex_decision.goals["g"].pop()
    except KeyError:
        pass
    try:
        lex_decision.goals["imaginal"].pop()
    except KeyError:
        pass

    # reinitialize model
    stim = {1: {'text': word, 'position': (320, 180)}}
    lex_decision.goals["g"].add(actr.makechunk(nameofchunk='start',
                                               typename="goal",
                                               state='attend'))
    lex_decision.goals["imaginal"].add(actr.makechunk(nameofchunk='start',
                                                      typename="word"))
    lex_decision.goals["imaginal"].delay = 0.2
    environment.current_focus = [320,180]
    lex_decision.model_parameters['motor_prepared'] = True

    # run new simulation
    lex_dec_sim = lex_decision.simulation(realtime=False, gui=False, trace=False,
              environment_process=environment.environment_process,
              stimuli=stim, triggers='', times=10)
    while True:
        lex_dec_sim.step()
        if lex_dec_sim.current_event.action == "KEY PRESSED: J":
            estimated_time = lex_dec_sim.show_time()
            break
        if lex_dec_sim.current_event.action == "KEY PRESSED: F":
            estimated_time = -1
            break
    return estimated_time

def run_lex_decision_task():
    """
    Function running a full lexical decision task:
    it calls run_stimulus(word) for words from all 16 freq bands.
    """
    sample = []
    for word in ORDERED_FREQ:
        sample.append(1000*run_stimulus(word))
    return sample

@as_op(itypes=[tt.dscalar, tt.dscalar, tt.dscalar, tt.dvector],
       otypes=[tt.dvector])
def actrmodel_latency(lf, le, decay, activation_from_time):
    """
    Function running the entire lexical decision task for specific
    values of the latency factor, latency exponent and decay parameters.
    The activation computed with the specific value of the decay
    parameter is also inherited as a separate argument to save expensive
    computation time.
    The function is wrapped inside the theano @as_op decorator so that
    pymc3 / theano can use it as part of the RT likelihood function in the
    Bayesian model below.
    """
    lex_decision.model_parameters["latency_factor"] = lf
    lex_decision.model_parameters["latency_exponent"] = le
    lex_decision.model_parameters["decay"] = decay
    activation_dict = {x[0]: x[1]
                       for x in zip(LEMMA_CHUNKS, activation_from_time)}
    lex_decision.decmem.activations.update(activation_dict)
    sample = run_lex_decision_task()
    return np.array(sample)

lex_decision_with_bayes = pm.Model()
with lex_decision_with_bayes:
    # prior for activation
    decay = Uniform('decay', lower=0, upper=1)
    # priors for accuracy
    noise = Uniform('noise', lower=0, upper=5)
    threshold = Normal('threshold', mu=0, sd=10)
    # priors for latency
    lf = HalfNormal('lf', sd=1)
    le = HalfNormal('le', sd=1)
    # compute activation
    scaled_time = time ** (-decay)
    def compute_activation(scaled_time_vector):
        compare = tt.isinf(scaled_time_vector)
        subvector = scaled_time_vector[(1-compare).nonzero()]
        activation_from_time = tt.log(subvector.sum())
        return activation_from_time
    activation_from_time, _ = theano.scan(fn=compute_activation,\
                                          sequences=scaled_time)
    # latency likelihood -- this is where pyactr is used
    pyactr_rt = actrmodel_latency(lf, le, decay, activation_from_time)
    mu_rt = Deterministic('mu_rt', pyactr_rt)
    rt_observed = Normal('rt_observed', mu=mu_rt, sd=0.01, observed=RT)
    # accuracy likelihood
    odds_reciprocal = tt.exp(-(activation_from_time - threshold)/noise)
    mu_prob = Deterministic('mu_prob', 1/(1 + odds_reciprocal))
    prob_observed = Normal('prob_observed', mu=mu_prob, sd=0.01,\
                           observed=ACCURACY)
    # we start the sampling
    #step = Metropolis()
    #db = SQLite('lex_dec_pyactr_chain_with_imaginal.sqlite')
    #trace = sample(draws=60000, trace=db, njobs=1, step=step, init='auto')

with lex_decision_with_bayes:
    trace = load('./data/lex_dec_pyactr_chain_with_imaginal.sqlite')
    trace = trace[10500:]

mu_rt = pd.DataFrame(trace['mu_rt'])
yerr_rt = [(mu_rt.mean()-mu_rt.quantile(0.025)),\
           (mu_rt.quantile(0.975)-mu_rt.mean())]

mu_prob = pd.DataFrame(trace['mu_prob'])
yerr_prob = [(mu_prob.mean()-mu_prob.quantile(0.025)),\
             (mu_prob.quantile(0.975)-mu_prob.mean())]

def generate_lex_dec_pyactr_with_imaginal_figure():
    fig, (ax1, ax2) = plt.subplots(ncols=1, nrows=2)
    fig.set_size_inches(6.0, 8.5)
    # plot 1: RTs
    ax1.errorbar(RT, mu_rt.mean(), yerr=yerr_rt, marker='o', linestyle='')
    ax1.plot(np.linspace(500, 800, 10), np.linspace(500, 800, 10),\
             color='red', linestyle=':')
    ax1.set_title('Lex. dec. model (pyactr, with imaginal, delay 200): RTs')
    ax1.set_xlabel('Observed RTs (ms)')
    ax1.set_ylabel('Predicted RTs (ms)')
    ax1.grid(b=True, which='minor', color='w', linewidth=1.0)
    # plot 2: probabilities
    ax2.errorbar(ACCURACY, mu_prob.mean(), yerr=yerr_prob, marker='o',\
                 linestyle='')
    ax2.plot(np.linspace(50, 100, 10)/100,\
             np.linspace(50, 100, 10)/100,\
             color='red', linestyle=':')
    ax2.set_title('Lex. dec. model (pyactr, with imaginal, delay 200): Prob.s')
    ax2.set_xlabel('Observed probabilities')
    ax2.set_ylabel('Predicted probabilities')
    ax2.grid(b=True, which='minor', color='w', linewidth=1.0)
    # clean up and save
    plt.tight_layout(pad=0.5, w_pad=0.2, h_pad=0.7)
    plt.savefig('./figures/lex_dec_model_pyactr_with_imaginal.pgf')
    plt.savefig('./figures/lex_dec_model_pyactr_with_imaginal.pdf')

generate_lex_dec_pyactr_with_imaginal_figure()
