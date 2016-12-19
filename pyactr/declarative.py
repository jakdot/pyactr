"""
Declarative memory. Consists of the actual declarative memory, and its associated buffer.
"""

import collections

import pyactr.chunks as chunks
import pyactr.utilities as utilities
import pyactr.buffers as buffers

class DecMem(collections.MutableMapping):
    """
    Declarative memory module.
    """

    def __init__(self, data=None):
        self._data = {}
        if data is not None:
            try:
                self.update(data)
            except ValueError:
                self.update({x:0 for x in data})

    def __contains__(self, elem):
        return elem in self._data
    
    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        for elem in self._data:
            yield elem

    def __getitem__(self, key):
        return self._data[key]

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return repr(self._data)

    def __setitem__(self, key, time):
        if isinstance(key, chunks.Chunk):
            try:
                self._data[key] = {round(float(time), 4)}
            except TypeError:
                self._data[key] = {round(float(x), 4) for x in time}
        else:
            raise utilities.ACTRError("Only chunks can be added as attributes to Declarative Memory; '%s' is not a chunk" % key)

    def add(self, key, time=0):
        """
        Add an element to decl. mem. If it exists, add time to the existing element.
        """
        try:
            self._data.setdefault(key, set()).add(round(float(time), 4))
        except TypeError:
            for x in key:
                self._data.setdefault(x, set()).add(round(float(time), 4))

    def copy(self):
        """
        Copy declarative memory.
        """
        dm = DecMem(self._data.copy())
        return dm


class DecMemBuffer(buffers.Buffer):
    """
    Declarative memory buffer.
    """

    def __init__(self, dm, data=None, finst=0):
        buffers.Buffer.__init__(self, dm, data)
        self.recent = collections.deque()
        self.finst = finst
        self.activation = None #activation of the last retrieved element

    def add(self, elem, time=0):
        """
        Clears current buffer and adds a new chunk.
        """
        self.clear(time)
        super().add(elem)

    def clear(self, time=0):
        """
        Clears buffer, adds cleared chunk into memory.
        """
        if self._data:
            self.dm.add(self._data.pop(), time)

    def copy(self, dm=None):
        """
        Copies buffer, along with its declarative memory, unless dm is specified. You need to specify new dm if 2 buffers share the same dm - only one of them should copy dm then.
        """
        if dm == None:
            dm = self.dm 
        copy_buffer = DecMemBuffer(dm, self._data.copy())
        return copy_buffer

    def test(self, state, inquiry):
        """
        Is current state busy/free/error?
        """
        return getattr(self, state) == inquiry

    def retrieve(self, time, otherchunk, actrvariables, buffers, extra_tests, model_parameters):
        """
        Retrieve a chunk from declarative memory that matches otherchunk.
        """
        if actrvariables == None:
            actrvariables = {}
        try:
            mod_attr_val = {x[0]: utilities.check_bound_vars(actrvariables, x[1]) for x in otherchunk.removeunused()}
        except utilities.ACTRError as arg:
            raise utilities.ACTRError("The chunk '%s' is not defined correctly; %s" % (otherchunk, arg))
        chunk_tobe_matched = chunks.Chunk(otherchunk.typename, **mod_attr_val)

        max_A = float("-inf")

        retrieved = None
        for chunk in self.dm:
            try:
                if extra_tests["recently_retrieved"] == False or extra_tests["recently_retrieved"] == 'False':
                    if self.finst and chunk in self.recent:
                        continue

                else:
                    if self.finst and chunk not in self.recent:
                        continue
            except KeyError:
                pass

            if model_parameters["subsymbolic"]: #if subsymbolic, check activation
                A_pm = 0
                if model_parameters["partial_matching"]:
                    A_pm = chunk_tobe_matched.match(chunk)
                else:
                    if not chunk_tobe_matched <= chunk:
                        continue

                A_bll = utilities.baselevel_learning(time, self.dm[chunk], model_parameters["baselevel_learning"], model_parameters["decay"]) #bll
                inst_noise = utilities.calculate_instantanoues_noise(model_parameters["instantaneous_noise"])
                A_sa = utilities.spreading_activation(chunk, buffers, self.dm, model_parameters["buffer_spreading_activation"], model_parameters["strength_of_association"])
                A = A_bll + A_sa + A_pm + inst_noise
                if utilities.retrieval_success(A, model_parameters["retrieval_threshold"]) and max_A < A:
                    max_A = A
                    retrieved = chunk
                    extra_time = utilities.retrieval_latency(A, model_parameters["latency_factor"],  model_parameters["latency_exponent"])

                    if model_parameters["activation_trace"]:
                        print("(Partially) matching chunk:", chunk)
                        print("Base level learning:", A_bll)
                        print("Spreading activation", A_sa)
                        print("Partial matching", A_pm)
                        print("Noise:", inst_noise)
                        print("Total activation", A)
                        print("Time to retrieve", extra_time)
                    self.activation = A
            else: #otherwise, just standard time for rule firing
                if chunk_tobe_matched <= chunk:
                    retrieved = chunk
                    extra_time = model_parameters["rule_firing"]

        if not retrieved:
            if model_parameters["subsymbolic"]:
                extra_time = utilities.retrieval_latency(model_parameters["retrieval_threshold"], model_parameters["latency_factor"],  model_parameters["latency_exponent"])
            else:
                extra_time = model_parameters["rule_firing"]
        if self.finst:
            self.recent.append(retrieved)
            if self.finst < len(self.recent):
                self.recent.popleft()
        return retrieved, extra_time
        
