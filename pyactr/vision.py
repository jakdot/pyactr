"""
Vision module. Just basic.
"""

import collections

import pyactr.chunks as chunks
import pyactr.utilities as utilities
from pyactr.utilities import ACTRError
import pyactr.buffers as buffers

#TODO
#setting ERROR/FREE should work even in buffers that can be interrupted -- check it does
#encoding visual info should proceed silently, but currently we need to go thru loop in production rules to wait for a change in environment

class VisualLocation(buffers.Buffer):
    """
    Visual buffer. Sees positions.
    """

    def __init__(self, environment, default_harvest=None, finst=4):
        buffers.Buffer.__init__(self, default_harvest, None)
        self.environment = environment
        self.recent = collections.deque()
        self.finst = finst

    def add(self, elem, found_stim, time=0, harvest=None):
        """
        Clears current buffer (into a memory) and adds a new chunk. Decl. memory is either specified as default_harvest, when Visual is initialized, or it can be specified as the argument of harvest.
        """
        self.clear(time, harvest)

        super().add(elem)
        
        if self.finst and found_stim:
            self.recent.append(found_stim)
            if self.finst < len(self.recent):
                self.recent.popleft()

    def modify(self, otherchunk, found_stim, actrvariables=None):
        """
        Modifies the chunk in VisualLocation buffer according to otherchunk. found_stim keeps information about the actual stimulus and it is used to update the queue of the recently visited chunks.
        """

        super().modify(otherchunk, actrvariables)
        
        if self.finst and found_stim:
            self.recent.append(found_stim)
            if self.finst < len(self.recent):
                self.recent.popleft()


    def clear(self, time=0, harvest=None):
        """
        Clears buffer, adds cleared chunk into decl. memory. Decl. memory is either specified as default_harvest, when Visual is initialized, or it can be specified here as harvest.
        """
        if harvest != None:
            if self._data:
                harvest.add(self._data.pop(), time)
        else:
            if self._data:
                self.dm.add(self._data.pop(), time)

    def find(self, otherchunk, actrvariables=None, extra_tests=None):
        """
        Sets a chunk in vision based on what is on the screen.
        """
        if extra_tests == None:
            extra_tests = {}
        if actrvariables == None:
            actrvariables = {}
        try:
            mod_attr_val = {x[0]: utilities.check_bound_vars(actrvariables, x[1]) for x in otherchunk.removeunused()}
        except utilities.ACTRError as arg:
            raise utilities.ACTRError("The chunk '%s' is not defined correctly; %s" % (otherchunk, arg))
        chunk_used_for_search = chunks.Chunk(utilities.VISUALLOCATION, **mod_attr_val)

        found = None
        found_stim = None
        closest = float("inf")
        current_x = None
        current_y = None
        for each in self.environment.stimulus:
            position = (int(self.environment.stimulus[each]['position'][0]), int(self.environment.stimulus[each]['position'][1]))
            try: #checks on x and y positions
                if chunk_used_for_search.screen_x[0] == utilities.VISIONSMALLER and int(chunk_used_for_search.screen_x[1:]) <= position[0]:
                    continue
                elif chunk_used_for_search.screen_x[0] == utilities.VISIONGREATER and int(chunk_used_for_search.screen_x[1:]) >= position[0]:
                    continue
                if chunk_used_for_search.screen_y[0] == utilities.VISIONSMALLER and int(chunk_used_for_search.screen_y[1:]) <= position[1]:
                    continue
                elif chunk_used_for_search.screen_y[0] == utilities.VISIONGREATER and int(chunk_used_for_search.screen_y[1:]) >= position[1]:
                    continue
            except (TypeError, IndexError):
                pass
            
            try: #checks on x and y positions
                if chunk_used_for_search.screen_x == utilities.VISIONLOWEST and current_x != None and position[0] > current_x:
                    continue
                elif chunk_used_for_search.screen_x == utilities.VISIONHIGHEST and current_x != None and position[0] < current_x:
                    continue
                if chunk_used_for_search.screen_y == utilities.VISIONLOWEST and current_y != None and position[1] > current_y:
                    continue
                elif chunk_used_for_search.screen_y == utilities.VISIONHIGHEST and current_y != None and position[1] < current_y:
                    continue
            except TypeError:
                pass
            
            try: #checks on closest
                if (chunk_used_for_search.screen_x == utilities.VISIONCLOSEST or  chunk_used_for_search.screen_y == utilities.VISIONCLOSEST) and utilities.calculate_pythagorian_distance(self.environment.current_focus, position) > closest:
                    continue
            except TypeError:
                pass

            try:
                if extra_tests["attended"] == False or extra_tests["attended"] == 'False':
                    if self.finst and self.environment.stimulus[each] in self.recent:
                        continue

                else:
                    if self.finst and self.environment.stimulus[each] not in self.recent:
                        continue
            except KeyError:
                pass
            found_stim = self.environment.stimulus[each]
            
            visible_chunk = chunks.makechunk(nameofchunk="vis1", typename="_visuallocation", **{key: each[key] for key in self.environment.stimulus[each] if key != 'position' and key != 'text'})
            if visible_chunk <= chunk_used_for_search:
                temp_dict = visible_chunk._asdict()
                temp_dict.update({"screen_x":position[0], "screen_y":position[1]})
                found = chunks.Chunk(utilities.VISUALLOCATION, **temp_dict)
                current_x = position[0]
                current_y = position[1]
                closest = utilities.calculate_pythagorian_distance(self.environment.current_focus, position)

        return found, found_stim

    def automatic_search(self, stim):
        """
        Automatically searches for a new stim in environment.
        """
        new_chunk = None
        found = None
        closest = float("inf")
        for st in stim:
            if st not in self.recent:
                position = st['position']
                try: #checks on closest
                    if utilities.calculate_pythagorian_distance(self.environment.current_focus, position) > closest:
                        continue
                except TypeError:
                    pass
                temp_dict = {key: st[key]  for key in st if key != 'position' and key != 'text'}
                temp_dict.update({'screen_x': st['position'][0], 'screen_y': st['position'][1]})
                closest = utilities.calculate_pythagorian_distance(self.environment.current_focus, position)
            new_chunk = chunks.Chunk(utilities.VISUALLOCATION, **temp_dict)
            found = st
        
        return new_chunk, found

    def test(self, state, inquiry):
        """
        Is current state busy/free/error?
        """
        return getattr(self, state) == inquiry

class Visual(buffers.Buffer):
    """
    Visual buffer. Sees objects.
    """

    _VISUAL = utilities.VISUAL

    def __init__(self, environment, default_harvest=None):
        self.environment = environment
        buffers.Buffer.__init__(self, default_harvest, None)
        self.current_focus = self.environment.current_focus
        self.state  = self._FREE
        self.preparation = self._FREE
        self.processor = self._FREE
        self.execution = self._FREE
        self.last_mvt = 0

    def add(self, elem, time=0, harvest=None):
        """
        Clears current buffer (into a memory) and adds a new chunk. Decl. memory is either specified as default_harvest, when Visual is initialized, or it can be specified as the argument of harvest.
        """
        self.clear(time, harvest)
        super().add(elem)

    def clear(self, time=0, harvest=None):
        """
        Clears buffer, adds cleared chunk into decl. memory. Decl. memory is either specified as default_harvest, when Visual is initialized, or it can be specified here as harvest.
        """
        if harvest != None:
            if self._data:
                harvest.add(self._data.pop(), time)
        else:
            if self._data:
                self.dm.add(self._data.pop(), time)

    def automatic_buffering(self, stim, model_parameters):
        """
        Automatically buffers.
        """
        temp_dict = {key: stim[key] for key in stim if key != 'position' and key != 'text'}
        temp_dict.update({'screen_pos': chunks.Chunk(utilities.VISUALLOCATION, **{'screen_x': stim['position'][0], 'screen_y': stim['position'][1]}), 'value': stim['text']})
        new_chunk = chunks.Chunk(utilities.VISUAL, **temp_dict)
        
        if new_chunk:
            angle_distance = 2*utilities.calculate_visual_angle(self.current_focus, (stim['position'][0], stim['position'][1]), self.environment.size, self.environment.simulated_screen_size, self.environment.viewing_distance) #the stimulus has to be within 2 degrees from the focus (foveal region)
            encoding_time = utilities.calculate_delay_visual_attention(angle_distance=angle_distance, K=model_parameters["eye_mvt_scaling_parameter"], k=model_parameters['eye_mvt_angle_parameter'], emma_noise=model_parameters['emma_noise'])
        return new_chunk, encoding_time

    def modify(self, otherchunk, actrvariables=None):
        """
        Modify the chunk in visual buffer according to the info in otherchunk.
        """
        super().modify(otherchunk, actrvariables)

    def shift(self, otherchunk, harvest=None, actrvariables=None, model_parameters=None):
        """
        Returns a chunk, time needed to attend and shift eye focus to the chunk, and the landing site of eye mvt.
        """
        if model_parameters == None:
            model_parameters = {}
        if actrvariables == None:
            actrvariables = {}
        try:
            mod_attr_val = {x[0]: utilities.check_bound_vars(actrvariables, x[1]) for x in otherchunk.removeunused()} #creates dict of attr-val pairs according to otherchunk
        except ACTRError as arg:
            raise ACTRError("The chunk '%s' is not defined correctly; %s" % (otherchunk, arg))

        for each in self.environment.stimulus:
            try:
                if self.environment.stimulus[each]['position'] == (float(mod_attr_val['screen_pos'].screen_x), float(mod_attr_val['screen_pos'].screen_y)):
                    mod_attr_val['value'] = self.environment.stimulus[each]['text']
            except (AttributeError, KeyError):
                raise ACTRError("The chunk in the visual buffer is not defined correctly. It is not possible to move attention.")

        new_chunk = chunks.Chunk(self._VISUAL, **mod_attr_val) #creates new chunk

        if new_chunk.cmd not in utilities.CMDVISUAL:
            raise ACTRError("Visual module received an invalid command: '%s'. The valid commands are: '%s'" % (new_chunk.cmd, utilities.CMDVISUAL))

        if new_chunk.cmd == utilities.CMDMOVEATTENTION and model_parameters['emma']:
            angle_distance = utilities.calculate_visual_angle(self.current_focus, [float(new_chunk.screen_pos.screen_x), float(new_chunk.screen_pos.screen_y)], self.environment.size, self.environment.simulated_screen_size, self.environment.viewing_distance)
            encoding_time = utilities.calculate_delay_visual_attention(angle_distance=angle_distance, K=model_parameters["eye_mvt_scaling_parameter"], k=model_parameters['eye_mvt_angle_parameter'], emma_noise=model_parameters['emma_noise'])
            preparation_time = utilities.calculate_preparation_time(emma_noise=model_parameters['emma_noise'])
            execution_time = utilities.calculate_execution_time(angle_distance, emma_noise=model_parameters['emma_noise'])
            landing_site = utilities.calculate_landing_site([float(new_chunk.screen_pos.screen_x), float(new_chunk.screen_pos.screen_y)], angle_distance, emma_noise=model_parameters['emma_noise'])
        elif new_chunk.cmd == utilities.CMDMOVEATTENTION and not model_parameters['emma']:
            encoding_time = 0.085
            preparation_time = 0
            execution_time = 0.085
            landing_site = (float(new_chunk.screen_pos.screen_x), float(new_chunk.screen_pos.screen_y))
        else:
            raise ACTRError("Visual module received an invalid command: '%s'. The only valid command currently is: %s" % (new_chunk.cmd, utilities.CMDMOVEATTENTION))
        return new_chunk, (encoding_time, preparation_time, execution_time), landing_site

    def move_eye(self, position):
        """
        Moves eye in environment to a new position.
        """
        self.current_focus[0] = int(position[0]) 
        self.current_focus[1] = int(position[1]) #current_focus is shared with environment

    def test(self, state, inquiry):
        """
        Is current state busy/free/error?
        """
        return getattr(self, state) == inquiry
