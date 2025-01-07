"""
Vision module. Just basic.
"""

import collections

from pyactr import buffers, chunks, utilities
from pyactr.utilities import ACTRError

#TODO
#setting ERROR/FREE should work even in buffers that can be interrupted -- check it does
#encoding visual info should proceed silently, but currently we need to go thru loop in production rules to wait for a change in environment

class VisualLocation(buffers.Buffer):
    """
    Visual buffer. This buffer sees positions of objects in the environment.
    """

    def __init__(self, environment, default_harvest=None, finst=4):
        buffers.Buffer.__init__(self, default_harvest, None)
        self.environment = environment
        self.recent = collections.deque()
        self.finst = finst

    @property
    def finst(self):
        """
        Finst - how many chunks are 'remembered' in declarative memory buffer.
        """
        return self.__finst

    @finst.setter
    def finst(self, value):
        if value >= 0:
            self.__finst = value
        else:
            raise ValueError('Finst in the dm buffer must be >= 0')

    @property
    def default_harvest(self):
        """
        Default harvest of visuallocation buffer.
        """
        return self.dm

    @default_harvest.setter
    def default_harvest(self, value):
        try:
            self.dm = value
        except ValueError:
            raise ACTRError('The default harvest set in the visuallocation buffer is not a possible declarative memory')

    def add(self, elem, found_stim, time=0, harvest=None):
        """
        Clear current buffer (into a memory) and adds a new chunk. Decl. memory is either specified as default_harvest, when Visual is initialized, or it can be specified as the argument of harvest.
        """
        self.clear(time, harvest)

        super().add(elem)
        
        if self.finst and found_stim:
            self.recent.append(found_stim)
            if self.finst < len(self.recent):
                self.recent.popleft()

    def modify(self, otherchunk, found_stim, actrvariables=None):
        """
        Modify the chunk in VisualLocation buffer according to otherchunk. found_stim keeps information about the actual stimulus and it is used to update the queue of the recently visited chunks.
        """

        super().modify(otherchunk, actrvariables)
        
        if self.finst and found_stim:
            self.recent.append(found_stim)
            if self.finst < len(self.recent):
                self.recent.popleft()


    def clear(self, time=0, harvest=None):
        """
        Clear buffer, adds cleared chunk into decl. memory. Decl. memory is either specified as default_harvest, when Visual is initialized, or it can be specified here as harvest.
        """
        if harvest != None:
            if self._data:
                harvest.add(self._data.pop(), time)
        else:
            if self._data:
                self.dm.add(self._data.pop(), time)

    def find(self, otherchunk, actrvariables=None, extra_tests=None):
        """
        Set a chunk in vision based on what is on the screen.
        """
        if extra_tests == None:
            extra_tests = {}
        if actrvariables == None:
            actrvariables = {}
        try:
            mod_attr_val = {x[0]: utilities.check_bound_vars(actrvariables, x[1], negative_impossible=False) for x in otherchunk.removeunused()}
        except utilities.ACTRError as arg:
            raise utilities.ACTRError(f"The chunk '{otherchunk}' is not defined correctly; {arg}")
        chunk_used_for_search = chunks.Chunk(utilities.VISUALLOCATION, **mod_attr_val)
            
        found = None
        found_stim = None
        closest = float("inf")
        x_closest = float("inf")
        y_closest = float("inf")
        current_x = None
        current_y = None
        for each in self.environment.stimulus:

            #extra test applied first
            try:
                if extra_tests["attended"] == False or extra_tests["attended"] == 'False':
                    if self.finst and self.environment.stimulus[each] in self.recent:
                        continue

                else:
                    if self.finst and self.environment.stimulus[each] not in self.recent:
                        continue
            except KeyError:
                pass

            #check value in text; in principle, you can search based on any value, so this is more powerful than actual visual search
            if chunk_used_for_search.value != chunk_used_for_search.EmptyValue() and chunk_used_for_search.value.values != self.environment.stimulus[each]["text"]:
                continue

            position = (int(self.environment.stimulus[each]['position'][0]), int(self.environment.stimulus[each]['position'][1]))

            #check absolute position; exception on AttributeError is to avoid the case in which the slot has empty value (in that case, the attribute "values" is undefined)
            try: 
                if chunk_used_for_search.screen_x.values and int(chunk_used_for_search.screen_x.values) != position[0]:
                    continue
            except (TypeError, ValueError, AttributeError):
                pass
            try:
                if chunk_used_for_search.screen_y.values and int(chunk_used_for_search.screen_y.values) != position[1]:
                    continue
            except (TypeError, ValueError, AttributeError):
                pass

            #check on x and y relative positions
            try: 
                if chunk_used_for_search.screen_x.values[0] == utilities.VISIONSMALLER and int(chunk_used_for_search.screen_x.values[1:]) <= position[0]:
                    continue
                elif chunk_used_for_search.screen_x.values[0] == utilities.VISIONGREATER and int(chunk_used_for_search.screen_x.values[1:]) >= position[0]:
                    continue
            except (TypeError, IndexError, AttributeError):
                pass

            try: 
                if chunk_used_for_search.screen_y.values[0] == utilities.VISIONSMALLER and int(chunk_used_for_search.screen_y.values[1:]) <= position[1]:
                    continue
                elif chunk_used_for_search.screen_y.values[0] == utilities.VISIONGREATER and int(chunk_used_for_search.screen_y.values[1:]) >= position[1]:
                    continue
            except (TypeError, IndexError, AttributeError):
                pass

            #check on x and y absolute positions 
            try: 
                if chunk_used_for_search.screen_x.values == utilities.VISIONLOWEST and current_x != None and position[0] > current_x:
                    continue
                elif chunk_used_for_search.screen_x.values == utilities.VISIONHIGHEST and current_x != None and position[0] < current_x:
                    continue
            except (TypeError, AttributeError):
                pass

            try: 
                if chunk_used_for_search.screen_y.values == utilities.VISIONLOWEST and current_y != None and position[1] > current_y:
                    continue
                elif chunk_used_for_search.screen_y.values == utilities.VISIONHIGHEST and current_y != None and position[1] < current_y:
                    continue
            except (TypeError, AttributeError):
                pass

            #check on closest
            try: 
                if (chunk_used_for_search.screen_x.values == utilities.VISIONCLOSEST or chunk_used_for_search.screen_y.values == utilities.VISIONCLOSEST) and utilities.calculate_pythagorean_distance(self.environment.current_focus, position) > closest:
                    continue
            except (TypeError, AttributeError):
                pass

            #check on onewayclosest
            try: 
                if (chunk_used_for_search.screen_x.values == utilities.VISIONONEWAYCLOSEST) and utilities.calculate_onedimensional_distance(self.environment.current_focus, position, horizontal=True) > x_closest:
                    continue
            except (TypeError, AttributeError):
                pass

            try:
                if (chunk_used_for_search.screen_y.values == utilities.VISIONONEWAYCLOSEST) and utilities.calculate_onedimensional_distance(self.environment.current_focus, position, horizontal=False) > y_closest:
                    continue
            except (TypeError, AttributeError):
                pass

            found_stim = self.environment.stimulus[each]
            visible_chunk = chunk_from_stimulus(found_stim, "visual_location", position=False)

            if visible_chunk <= chunk_used_for_search:
                found = chunk_from_stimulus(found_stim, "visual_location", position=True)
                current_x = position[0]
                current_y = position[1]
                closest = utilities.calculate_pythagorean_distance(self.environment.current_focus, position)
                x_closest = utilities.calculate_onedimensional_distance(self.environment.current_focus, position, horizontal=True)
                y_closest = utilities.calculate_onedimensional_distance(self.environment.current_focus, position, horizontal=False)

        return found, found_stim

    def automatic_search(self, stim):
        """
        Automatically search for a new stim in environment.
        """
        new_chunk = None
        found = None
        closest = float("inf")
        for st in stim:
            if st not in self.recent:
                position = st['position']
                #check on closest
                try: 
                    if utilities.calculate_pythagorean_distance(self.environment.current_focus, position) > closest:
                        continue
                except TypeError:
                    pass

                closest = utilities.calculate_pythagorean_distance(self.environment.current_focus, position)

                new_chunk = chunk_from_stimulus(st, "visual_location")
                found = st
        
        return new_chunk, found

    def test(self, state, inquiry):
        """
        Is current state busy/free/error?
        """
        return getattr(self, state) == inquiry

class Visual(buffers.Buffer):
    """
    Visual buffer. This sees objects in the environment.
    """

    def __init__(self, environment, default_harvest=None):
        self.environment = environment
        buffers.Buffer.__init__(self, default_harvest, None)
        self.current_focus = self.environment.current_focus
        self.state  = self._FREE
        self.preparation = self._FREE
        self.processor = self._FREE
        self.execution = self._FREE
        self.autoattending = self._FREE
        self.attend_automatic = True #the current focus automatically attends
        self.last_mvt = 0

        #parameters
        self.model_parameters = {}

    @property
    def default_harvest(self):
        """
        Default harvest of visual buffer.
        """
        return self.dm

    @default_harvest.setter
    def default_harvest(self, value):
        try:
            self.dm = value
        except ValueError:
            raise ACTRError('The default harvest set in the visual buffer is not a possible declarative memory')


    def add(self, elem, time=0, harvest=None):
        """
        Clear current buffer (into a memory) and adds a new chunk. Decl. memory is either specified as default_harvest, when Visual is initialized, or it can be specified as the argument of harvest.
        """
        self.clear(time, harvest)
        super().add(elem)

    def clear(self, time=0, harvest=None):
        """
        Clear buffer, adds cleared chunk into decl. memory. Decl. memory is either specified as default_harvest, when Visual is initialized, or it can be specified here as harvest.
        """
        if harvest != None:
            if self._data:
                harvest.add(self._data.pop(), time)
        else:
            if self._data:
                self.dm.add(self._data.pop(), time)

    def automatic_buffering(self, stim, model_parameters):
        """
        Buffer visual object automatically.
        """
        model_parameters = model_parameters.copy()
        model_parameters.update(self.model_parameters)

        new_chunk = chunk_from_stimulus(stim, "visual", position=False)
        
        if new_chunk:
            angle_distance = 2*utilities.calculate_visual_angle(self.environment.current_focus, (stim['position'][0], stim['position'][1]), self.environment.size, self.environment.simulated_screen_size, self.environment.viewing_distance) #the stimulus has to be within 2 degrees from the focus (foveal region)
            encoding_time = utilities.calculate_delay_visual_attention(angle_distance=angle_distance, K=model_parameters["eye_mvt_scaling_parameter"], k=model_parameters['eye_mvt_angle_parameter'], emma_noise=model_parameters['emma_noise'], vis_delay=stim.get('vis_delay'))
        return new_chunk, encoding_time

    def modify(self, otherchunk, actrvariables=None):
        """
        Modify the chunk in visual buffer according to the info in otherchunk.
        """
        super().modify(otherchunk, actrvariables)

    def stop_automatic_buffering(self):
        """
        Stop automatic buffering of the visual buffer.
        """
        self.attend_automatic = False

    def shift(self, otherchunk, harvest=None, actrvariables=None, model_parameters=None):
        """
        Return a chunk, time needed to attend and shift eye focus to the chunk, and the landing site of eye mvt.
        """
        if model_parameters == None:
            model_parameters = {}
        model_parameters = model_parameters.copy()
        model_parameters.update(self.model_parameters)

        if actrvariables == None:
            actrvariables = {}
        try:
            mod_attr_val = {x[0]: utilities.check_bound_vars(actrvariables, x[1]) for x in otherchunk.removeunused()}
        except ACTRError as arg:
            raise ACTRError(f"Shifting towards the chunk '{otherchunk}' is impossible; {arg}")

        vis_delay = None

        for each in self.environment.stimulus:
            try:
                if self.environment.stimulus[each]['position'] == (float(mod_attr_val['screen_pos'].values.screen_x.values), float(mod_attr_val['screen_pos'].values.screen_y.values)):
                    vis_delay = self.environment.stimulus[each].get('vis_delay')
                    stim = self.environment.stimulus[each].copy()
                    stim.update({'cmd': mod_attr_val['cmd']})
            except (AttributeError, KeyError):
                raise ACTRError("The chunk in the visual buffer is not defined correctly. It is not possible to move attention.")

        new_chunk = chunk_from_stimulus(stim, "visual", position=False) #creates new chunk

        if model_parameters['emma']:
            angle_distance = utilities.calculate_visual_angle(self.environment.current_focus, [float(new_chunk.screen_pos.values.screen_x.values), float(new_chunk.screen_pos.values.screen_y.values)], self.environment.size, self.environment.simulated_screen_size, self.environment.viewing_distance)
            encoding_time = utilities.calculate_delay_visual_attention(angle_distance=angle_distance, K=model_parameters["eye_mvt_scaling_parameter"], k=model_parameters['eye_mvt_angle_parameter'], emma_noise=model_parameters['emma_noise'], vis_delay=vis_delay)
            preparation_time = utilities.calculate_preparation_time(emma_noise=model_parameters['emma_noise'])
            execution_time = utilities.calculate_execution_time(angle_distance, emma_noise=model_parameters['emma_noise'])
            landing_site = utilities.calculate_landing_site([float(new_chunk.screen_pos.values.screen_x.values), float(new_chunk.screen_pos.values.screen_y.values)], angle_distance, emma_landing_site_noise=model_parameters['emma_landing_site_noise'])
        elif not model_parameters['emma']:
            encoding_time = 0.085
            preparation_time = 0
            execution_time = 0.085
            landing_site = (float(new_chunk.screen_pos.values.screen_x.values), float(new_chunk.screen_pos.values.screen_y.values))
        return new_chunk, (encoding_time, preparation_time, execution_time), landing_site

    def move_eye(self, position):
        """
        Move eyes in environment to a new position.
        """
        self.environment.current_focus = [int(position[0]), int(position[1])]
        self.current_focus = self.environment.current_focus

    def test(self, state, inquiry):
        """
        Is current state busy/free/error?
        """
        return getattr(self, state) == inquiry

def chunk_from_stimulus(stimulus, buffer_name, position=True):
    """
    Given a stimulus dict from the environment, a buffer name, and whether to encode position, returns a chunk to be used in that buffer.
    """
    # extract a possible extended chunk type from the stimulus
    # defaults to utilities.VISUALLOCATION/.VISUAL
    if buffer_name == "visual_location":
        stim_typename = stimulus.get(buffer_name + "_typename", utilities.VISUALLOCATION)
    elif buffer_name == "visual":
        stim_typename = stimulus.get(buffer_name + "_typename", utilities.VISUAL)
    else:
        raise ValueError("buffer_name must be either ""visual_location"" or ""visual""")

    # a list of reserved values for control parameters, never encoded into the chunk
    stim_control = ['text', 'position', 'vis_delay', 'visual_location_typename', 'visual_typename', 'externally_visible']

    # determining the values that will be visible in the chunk
    # by default, for visual location chunks this is just 'screen_x' and 'screen_y', but others are merged from stimulus['externally_visible']
    # in contrast, for visual chunks, all non-control keys will be encoded regardless (with 'text' as 'value', see below)
    # be careful when adding to stimulus['externally_visible']: visual search checks if the stimulus chunk subsumes the search chunk...
    # ... so ALL externally visible features of a stimulus must be included in a search in order to fixate it

    if buffer_name == "visual_location":
        visible_features = []
        try:
            visible_features += stimulus.get('externally_visible', [])
        except AttributeError:
            raise ValueError("stimulus['externally_visible'] should be a list of strings")
    else:
        visible_features = [key for key in stimulus if key not in stim_control]

    temp_dict = {key: stimulus[key] for key in stimulus if key in visible_features}
    if position:
        temp_dict.update({'screen_x': int(stimulus['position'][0]),
                          'screen_y': int(stimulus['position'][1])})
    if buffer_name == "visual":
        location = chunk_from_stimulus(stimulus, "visual_location")
        temp_dict.update({'screen_pos': location})
        temp_dict.update({'value': stimulus.get('text', '')})
    visible_chunk = chunks.Chunk(stim_typename, **temp_dict)

    return visible_chunk
