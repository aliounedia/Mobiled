#----------------------------------------------------------------------------#
#                                                                            #
#    Copyright (C) 2009 Department of Arts and Culture,                      #
#                       Republic of South Africa                             #
#    Contributer: Meraka Institute, CSIR                                     #
#    Author: Mark Zsilavecz                                                  #
#    Contact: mzsilavecz@csir.co.za                                          #
#                                                                            #
#    License:                                                                #
#    Redistribution and use in source and binary forms, with or without      #
#    modification, are permitted provided that the following conditions are  #
#    met:                                                                    #
#                                                                            #
#     * Redistributions of source code must retain the above copyright       #
#       notice, this list of conditions and disclaimer. <See COPYING file>   #
#                                                                            #
#     * Redistributions in binary form must reproduce the above copyright    #
#       notice, this list of conditions and disclaimer <See COPYING file>    #
#       in the documentation and/or other materials provided with the        #
#       distribution.                                                        #
#                                                                            #
#     * Neither the name of the Department of Arts and Culture nor the names #
#       of its contributors may be used to endorse or promote products       #
#       derived from this software without specific prior written permission.#
#----------------------------------------------------------------------------#


#    The docstrings in this module contain epytext markup: API               #
#    documentation  may be created by processing this file with epydoc:      #
#    http://epydoc.sf.net                                                    #

"""
An abstraction of the finite state machine (FSM)-like nodes which constitute a
L{Dialog<dialogScripting.dialog.Dialog>}.

@author: Mark Zsilavecz
@contact: mzsilavecz@csir.co.za
"""

import re, sys
import hashlib

from constants import *
from containers import *


class NodeError(Exception):
    """
    Basic exception raised by the L{Node<dialogScripting.node.Node>} class.
    """

class Node:
    """
    Abstracts a node in a L{Dialog<dialogScripting.dialog.Dialog>}. It holds all
    the L{container<dialogScripting.containers>}s with data and provides methods
    to access, add and remove them.
    
    @ivar _name: The hashed name of this node.
    @type _name: C{str}
    @ivar _rawName: The raw string name of this node.
    @type _rawName: C{str}
    @ivar _error: The error item of this node.
    @type _error: L{ErrorItem<dialogScripting.containers.ErrorItem>}
    @ivar _goto: The default next node destination of this node. An absolute
                 node name is hashed, but a relative destination is kept as a
                 raw string.
    @type _goto: C{str}
    @ivar _audio: The audio items of this node.
    @type _audio: C{dict} of {C{int}: L{AudioItem<dialogScripting.containers.AudioItem>}}
    @ivar _custom: The custom items of this node.
    @type _custom: C{dict} of {C{int}: L{CustomItem<dialogScripting.containers.CustomItem>}}
    @ivar _options: The option items of this node.
    @type _options: C{dict} of {C{str}: L{OptionItem<dialogScripting.containers.OptionItem>}}
    @ivar _record: The record item of this node.
    @type _record: L{RecordItem<dialogScripting.containers.RecordItem>}
    @ivar _event: The current event signaled by this node. It can be one of the
                  following constants:
                   - L{EVENT_CUSTOM<dialogScripting.constants.EVENT_CUSTOM>}
                   - L{EVENT_AUDIO<dialogScripting.constants.EVENT_AUDIO>}
                   - L{EVENT_OPTION<dialogScripting.constants.EVENT_OPTION>}
                   - L{EVENT_RECORD<dialogScripting.constants.EVENT_RECORD>}
                   - L{EVENT_UNKNOWN<dialogScripting.constants.EVENT_UNKNOWN>}
                   - L{EVENT_TIMEOUT<dialogScripting.constants.EVENT_TIMEOUT>}
                   - L{EVENT_REROUTE<dialogScripting.constants.EVENT_REROUTE>}
                   - L{EVENT_EXIT<dialogScripting.constants.EVENT_EXIT>}
    @type _event: C{int}
    """
    
    def __init__(self, name, inputSettings=None, error=None, goto=None, audio=None, custom=None, 
                 options=None, record=None, applyGlobals=True, exit=False):
        """
        Initialises the object.
        
        @param name: The name by which this node will be referenced, stored as a hash of the string.
        @type name: C{str}

        @param inputSettings: The data for the single 
        L{InputSettings<dialogScripting.containers.InputSettings>}
        @type inputSettings: C{dict} of C{str}: C{str} or C{int} or C{bool}

        @see: L{InputSettings<dialogScripting.containers.InputSettings>}

        @param error: The data for the single
                      L{ErrorItem<dialogScripting.containers.ErrorItem>} in the
                      form::
                       {'UNKNOWN': node destination, 
                        'TIMEOUT': node destination, 
                        'REROUTE': node destination}
        @type error: C{dict} of {C{str}: C{str}}

        @see: L{ErrorItem.__init__<dialogScripting.containers.ErrorItem.__init__>}

        @param goto: The default next node destination. It can be another node
                     specified by its raw string name or a relative node
                     destination which must be one of the following constants:
                      - L{PREVIOUS<dialogScripting.constants.PREVIOUS>}
                      - L{CURRENT<dialogScripting.constants.CURRENT>}
                     
                     Its use is mutually exclusive to that of any
                     L{OptionItem<dialogScripting.containers.OptionItem>}.
        @type goto: C{str}

        @param audio: The data for single or multiple I{indexed}
                      L{AudioItem<dialogScripting.containers.AudioItem>}s in the
                      form::
                       {0:{'SOURCE': source type, 
                           'VALUE': value},
                        1:{ ... },
                        ... }
        @type audio: C{dict} of C{int}: C{dict} of C{str}: C{str} or C{dict}
        @note: The audio value can be a string containing the tts text or audio file location, or it can
        contain a C{dict} of multiple tts text phrases or audio locations. The keys of the dictionary represent
        the audio index, which is set in Dialog.setAudioIndex(). This is useful when multi-lingual content is used, 
        where the same prompt is represented by multilingual audio files or text phrases.
        e.g. {0 : 'ENGLISH PROMPT', 1: 'AFRIKAANS PROMPT', 2: 'ZULU PROMPT'}

        @see: L{Dialog.setAudioIndex(index)<dialogScripting.dialog.Dialog.setAudioIndex>}
        @see: L{AudioItem.__init__<dialogScripting.containers.AudioItem.__init__>}

        @param custom:  A dictionary that refers to a modules function, where custom functionality 
        has been implemented.
        @type custom: C{dict} of {C{int}: C{dict} of {C{str}: C{str}}}
        @note: The custom implemenated functionality is always executed before any specified dialog functionality,
        such as audio playback, input, etc. 
        @see: L{CustomItem.__init__<dialogScripting.containers.CustomItem.__init__>}
                    
        @param options: The data for single or multiple
                        L{OptionItem<dialogScripting.containers.OptionItem>}s in
                        the form::
                         {option 1: node destination 1, 
                          option 2: ... ,
                          ... }
                        
                        Its use is mutually exclusive to that of the C{goto}
                        destination.
        @type options: C{dict} of {C{str}: C{str}}
        @see: L{OptionItem.__init__<dialogScripting.containers.OptionItem.__init__>}

        @param record: The data for the single
                       L{RecordItem<dialogScripting.containers.RecordItem>} in
                       the form::
                        {'FILENAME': filename, 
                         'MAXTIME': maximum time, 
                         'INTKEYS': interrupt keys, 
                         'PLAYBEEP': beep condition}
        @type record: C{dict} of {C{str}: (C{str} or C{bool})}
        @see: L{RecordItem.__init__<dialogScripting.containers.RecordItem.__init__>}

        @param applyGlobals: Whether global options are active for this node.
        @type applyGlobals: C{bool}

        @param exit:  Whether the dialog will exit after this node has finished executing.
        @type exit: C{bool}
        """
        try:
            # store name as the hash of the string
            self._name = self._hashValue(name)
            # store the name in its original form
            self._rawName = name
            
            # store the goto destination as a hash of the string
            if goto != None:
                # check if goto is a default (PREVIOUS or CURRENT)
                if goto in POSITION:
                    self._goto = goto
                else:
                    self._goto = self._hashValue(goto)
                self._rawGoto = goto
            else: 
                self._goto = None
                self._rawGoto = None
            
            self._record = None
            
            if error != None:
              self._error  = ErrorItem(error)
            else:
                self._error = error

            if inputSettings != None:
                self._inputSettings = InputSettings(inputSettings)
            else:
                self._inputSettings = inputSettings

            
            self._applyGlobals = applyGlobals
            self._event = EVENT_CUSTOM
            
            self._time_enter = None
            self._time_exit = None
            self._time_input = None
            self._time_audio = []
            self._time_record = None
            self._chosen_option = None
            self._visitCount = 0
            
            self._exit = exit
            self._audio_index = 0
            self._custom_index = 0
            self._lastOption = None
                                   
            # Add audio items.
            self._audio = {}
            if audio is not None:
                for pos in audio:
                    self._audio[pos] = AudioItem(audio[pos])
            
                       
            # Add option items.
            self._options = {}
            if options is not None:
                for opt in options.keys():
                    self._options[opt] = OptionItem(opt, options[opt])
            
            # Add custom items.
            self._custom = {}
            if custom is not None:
                for pos in custom:
                    self._custom[pos] = CustomItem(custom[pos])
            
            # Add record item.
            if record is not None:
                self._record = RecordItem(record)
        
        except ContainerError, e:
            raise NodeError('Node cannot be created: %s' %e)
      
    def reset(self):
        """
        Resets the node. The sequential access to the audio and custom items of
        the node is reset and an
        L{EVENT_CUSTOM<dialogScripting.constants.EVENT_CUSTOM>} is signaled.
        """
        self._audio_index = 0
        self._custom_index = 0
        self._event = EVENT_CUSTOM
        
    def getCustom(self):
        """
        Gets the custom function data from the next
        L{CustomItem<dialogScripting.containers.CustomItem>}. If no more items
        remain, an L{EVENT_AUDIO<dialogScripting.constants.EVENT_AUDIO>} is
        signaled.
        
        @return: The custom item data.
        @rtype: C{dict} of {C{str}: C{str}}
        """
        if self._custom.has_key(self._custom_index):
            custom = self._custom[self._custom_index].get()
            self._custom_index += 1
        else:
            custom = None
            self._event = EVENT_AUDIO
        return custom
             
    def getAudio(self):
        """
        Gets the audio prompt data from the next
        L{AudioItem<dialogScripting.containers.AudioItem>}. If no more items
        remain, one event out of the following is signaled:
         1. L{EVENT_RECORD<dialogScripting.constants.EVENT_RECORD>} if a
            L{RecordItem<dialogScripting.containers.RecordItem>} exists.
         2. L{EVENT_EXIT<dialogScripting.constants.EVENT_EXIT>} if the node can
            exit the dialog.
         3. else L{EVENT_OPTION<dialogScripting.constants.EVENT_OPTION>}.
        
        @return: The audio item data.
        @rtype: C{dict} of {C{str}: C{str}}
        """
        # Increment the node visit count if this is the first audio item
        if self._audio_index == 0:
            self._visitCount += 1
        
        if self._audio.has_key(self._audio_index):
            audio = self._audio[self._audio_index].get()
            self._audio_index += 1
        else:
            audio = None
            if self._record is not None:
                self._event = EVENT_RECORD
            elif self._record is None and self._exit == False:
                self._event = EVENT_OPTION
            else:
                self._event = EVENT_EXIT
        return audio
    
    
    def getDest(self, option, globalOpts, visited):
        """
        Gets the correct node destination based on the option provided. Relative
        destination options are returned as is; goto, error and normal input
        options are resolved into node destinations by querying the
        corresponding containers. If a non-error option is valid, the visit
        count of this node is reset to zero.
        
        @param option: The destination option.
        @type option: C{str}
        @param globalOpts: The global options available.
        @type globalOpts: C{dict}
        @param visited: A history of the hashed names of previously visited
                        nodes.
        @type visited: C{list} of [C{str}]
        @return: The node destination associated with the option or C{None} if
                 if no association exists.
        @rtype: C{str}
        """
        self._chosen_option = option
        # Evaluate a destination expression.
        def evaluate(statement, visited):
            
            
            # NOTE EVAL Inactive for now due to hashing of internals
            # Internal hash representation used for node names, destinations, conflicts with EVAL
            # TODO: Will have to hash EVAL destination node names
            
            def splitExpr(expression):
                op, expression = re.split(r'\(', expression)
                #op = op.lower() ??Necessary??
                if op == 'else':
                    result = expression
                    test = None
                    subject = None
                elif op == 'if' or op == 'elif':
                    temp, result = re.split(r':', expression)
                    test, subject = re.split(r'\=(?=\w)', temp)
                
                return op, test, subject, result
            
            if re.match(r'^ *EVAL: *', statement) is not None:
                temp = re.split(r'^ *EVAL: *', statement)[1]
                parts = re.split(r'\)', re.sub(r' ', '', temp))
                
                dest = None
                for part in parts:
                    if part:
                        op, test, subject, result = splitExpr(part)
                        if test == 'prev=':
                            # If subject is in visited return result
                            if subject in visited:
                                dest = result
                                break
                        elif test == 'prev!':
                            # If subject is in visited return result
                            if subject not in visited:
                                dest = result
                                break
                        elif test == 'last=':
                            # If subject was last return result
                            if subject == visited[len(visited) - 1]:
                                dest = result
                                break
                        elif test == 'last!':
                            # If subject was not last return result
                            if subject != visited[len(visited) - 1]:
                                dest = result
                                break
                        elif test is None:
                            # If all before false return result
                            dest = result
                            break
            else:
                dest = statement
            return dest
        
        # Get the correct destination.
        if option == 'CURRRENT':
            dest = 'CURRRENT'
            # reset the visit count since a valid option was chosen
            self._visitCount = 0
        elif option == 'PREVIOUS':
            dest = 'PREVIOUS'
            # reset the visit count since a valid option was chosen
            self._visitCount = 0
        elif option == 'GOTO':
            dest = evaluate(self._goto, visited)
            # reset the visit count since a valid option was chosen
            self._visitCount = 0
        elif option == 'TIMEOUT':
            dest = evaluate(self._error.getTimeout(), visited)
        elif option == 'UNKNOWN':
            dest = evaluate(self._error.getUnknown(), visited)
        elif option == 'REROUTE': # FIX: gschlunz: added rerouting option
            dest = evaluate(self._error.getReRoute(), visited)
            # reset the visit count upon reroute
            self._visitCount = 0
        elif globalOpts.has_key(option):
            dest = evaluate(globalOpts[option].getDest(), visited)
            # reset the visit count since a valid option was chosen
            self._visitCount = 0
        elif self._options.has_key(option):
            dest = evaluate(self._options[option].getDest(), visited)
            # reset the visit count since a valid option was chosen
            self._visitCount = 0
        elif option == 'IGNORE':
            raise NodeError('Fix: this option should not be reached.')
        else:
            dest = None
        return dest


    def getOptions(self):
        """
        Gets the options in all the
        L{OptionItem<dialogScripting.containers.OptionItem>}s of this node.
        
        @return: The option item options.
        @rtype: C{list} of [C{str}]
        """
        #return self.optionItems.keys()
        return self._options.keys() # FIX: gschlunz: corrected option item access

    def getInputSettings(self):
        """
        Gets the L{InputSettings<dialogScripting.containers.InputSettings>} of this node.
        """
        return self._inputSettings
    
    def getMaxtime(self): 
        """
        Gets the maximum waiting time (in milliseconds) for input once all the
        audio prompts for this node has been played. i.e. zero if there are
        still audio items in the queue or else the actual maximum time. The node
        visit count is incremented if the queue is empty.
        
        @return: The maximum waiting time, or zero.
        @rtype: C{int}
        """
        if self._audio.has_key(self._audio_index):
            time = 0
        elif self._inputSettings:
            time = self._inputSettings.getMaxTime()
        else:
            time = 0
            
        return time

    def getBargeInDuration(self):
        """
        Gets the barge in speech input duration

        @return: The Barge in speech input duration
        @rtype: C{int}
        """
        if self._inputSettings:
            return self._inputSettings.getBargeinDuration()
        else:
            return 0

    def getConsecutiveSpeechDuration(self):
        """
        Gets the consecutive speech input duration 

        @return: The consecutive speech input duration
        @rtype: C{int}
        """
        if self._inputSettings:
            return self._inputSettings.getConsecutiveSpeechDuration()
        else:
            return 0
    
    def getMaxVisitCount(self):
        """
        Gets the maximum number of times that this node may be visited upon an
        error before it will reroute to another one.
        
        @return: The maximum visit count.
        @rtype: C{int}
        """
        if self._inputSettings:
          return self._inputSettings.getMaxVisitCount()
        else:
          return 0
        
    def getRecord(self): 
        """
        Gets the recording data from the
        L{RecordItem<dialogScripting.containers.RecordItem>}. One event out of
        the following is signaled:
         1. L{EVENT_EXIT<dialogScripting.constants.EVENT_EXIT>} if the node can
            exit the dialog.
         2. else L{EVENT_OPTION<dialogScripting.constants.EVENT_OPTION>}.
        
        @return: The custom item data.
        @rtype: C{dict} of {C{str}: C{str}}
        """
        if self._exit == False:
            self._event = EVENT_OPTION
        else:
            self._event = EVENT_EXIT
        return self._record
    
    def getName(self):
        """
        Gets the hashed name of this node.
        
        @return: The hashed name.
        @rtype: C{str}
        """
        return self._name
    
    def getEvent(self):
        """
        Gets the latest event signaled by this node. It will be one of the
        following constants:
         - L{EVENT_CUSTOM<dialogScripting.constants.EVENT_CUSTOM>}
         - L{EVENT_AUDIO<dialogScripting.constants.EVENT_AUDIO>}
         - L{EVENT_OPTION<dialogScripting.constants.EVENT_OPTION>}
         - L{EVENT_RECORD<dialogScripting.constants.EVENT_RECORD>}
         - L{EVENT_UNKNOWN<dialogScripting.constants.EVENT_UNKNOWN>}
         - L{EVENT_TIMEOUT<dialogScripting.constants.EVENT_TIMEOUT>}
         - L{EVENT_REROUTE<dialogScripting.constants.EVENT_REROUTE>}
         - L{EVENT_EXIT<dialogScripting.constants.EVENT_EXIT>}
        
        @return: The event.
        @rtype: C{int}
        """
        return self._event
    
    def setEvent(self, event):
        """
        Sets/Signals an event at this node. It must be one of the following
        constants:
         - L{EVENT_CUSTOM<dialogScripting.constants.EVENT_CUSTOM>}
         - L{EVENT_AUDIO<dialogScripting.constants.EVENT_AUDIO>}
         - L{EVENT_OPTION<dialogScripting.constants.EVENT_OPTION>}
         - L{EVENT_RECORD<dialogScripting.constants.EVENT_RECORD>}
         - L{EVENT_UNKNOWN<dialogScripting.constants.EVENT_UNKNOWN>}
         - L{EVENT_TIMEOUT<dialogScripting.constants.EVENT_TIMEOUT>}
         - L{EVENT_REROUTE<dialogScripting.constants.EVENT_REROUTE>}
         - L{EVENT_EXIT<dialogScripting.constants.EVENT_EXIT>}
        
        @param event: The event.
        @type event: C{int}
        """
        self._event = event
    
    #{ Logging Methods
    def setTimeEnter(self, time): self._time_enter = time
    
    def setTimeExit(self, time): self._time_exit = time
    
    def setTimeInput(self, time): self._time_input = time
    
    def setTimeAudio(self, start_time, end_time): 
        self._time_audio.append((start_time, end_time))
      
    def setTimeRecord(self, start_time, end_time): 
        self._time_record = (start_time, end_time)
    
    def setLastOption(self, option): 
        """
        Sets the most recent DTMF option, or default node routing option C{PREVIOUS, GOTO}
        @param option: the most recent option (DTMF or default)
        @type option: C{str}
        @deprecated: This access method has been replaced by L{getLastInput, dialogScripting.dialog.Dialog.setLastInput}
        """
        self._lastOption = option
    
    def getLastOption(self): 
        """
        @return: Returns the most recent DTMF option, or default node routing option C{PREVIOUS, GOTO}
        @rtype: C{str}
        @deprecated: This access method has been replaced by L{getLastInput, dialogScripting.dialog.Dialog.getLastInput}
        """
        return self._lastOption
    
    def getStats(self): 
        return {'NAME':self._name, 'ENTERED':self._time_enter, 
                'EXITED':self._time_exit, 'INPUT':self._time_input,
                'AUDIO':self._time_audio, 'RECORD':self._time_record,
                'OPTION':self._chosen_option}
    #}
    
    def getAllAudio(self):
        """
        Gets all the L{AudioItem<dialogScripting.containers.AudioItem>}s of this
        node.
        
        @return: All the audio items.
        @rtype: C{dict} of {C{int}: L{AudioItem<dialogScripting.containers.AudioItem>}}
        """
        return self._audio # Only used in validating.
    
    def getAllCustom(self):
        """
        Gets all the L{CustomItem<dialogScripting.containers.CustomItem>}s of
        this node.
        
        @return: All the custom items.
        @rtype: C{dict} of {C{int}: L{CustomItem<dialogScripting.containers.CustomItem>}}
        """
        return self._custom # Only used in validating.
    
    def getAllOptions(self):
        """
        Gets all the L{OptionItem<dialogScripting.containers.OptionItem>}s of
        this node.
        
        @return: All the option items.
        @rtype: C{dict} of {C{str}: L{OptionItem<dialogScripting.containers.OptionItem>}}
        """
        return self._options # Only used in validating.
    
    def getGoto(self):
        """
        Gets the default next node destination of this node. An absolute node
        name will be hashed, but a relative destination will be the raw string.
        
        @return: The default next node destination.
        @rtype: C{str}
        """
        return self._goto # Only used in validating.
    
    def getRawGoto(self):
        """
        Gets the raw string name of the default next node destination of this
        node.
        
        @return: The raw string default node destination.
        @rtype: C{str}
        """
        return self._rawGoto # Only used in validating.
    
    def getRawName(self):
        """
        Gets the raw string name of this node.
        
        @return: The raw string name.
        @rtype: C{str}
        """
        return self._rawName # Only used in validating.
    
    def getError(self):
        """
        Gets the L{ErrorItem<dialogScripting.containers.ErrorItem>} of this node.
        
        @return: The error item.
        @rtype: L{ErrorItem<dialogScripting.containers.ErrorItem>}
        """
        return self._error # Only used in validating.
    
    def getVisitCount(self):
        """
        Gets the current visit count of this node.
        
        @return: The current visit count.
        @rtype: C{int}
        """
        return self._visitCount # Only used in validating.
    
    def getUseAllDtmfInput(self):
        """
        Gets the useAllDtmfInput setting used for indicating if all dtmf digits can be used as valid input.        @rtype: C{boolean}
        """
        if self._inputSettings:
            return self._inputSettings.getUseAllDtmfInput()
        else:
            return True
        
    # Methods meant for use by external functions.
    def addAudio(self, data, pos=None):
        """
        Replaces an L{AudioItem<dialogScripting.containers.AudioItem>} at the
        specified position (index) of this node using the given audio prompt
        data. If C{pos = None}, the item is appended.
        
        @param data: The audio prompt data.
        The data for single L{AudioItem<dialogScripting.containers.AudioItem>} in the
        form:: {'SOURCE': source type,'VALUE': value},
        @type data: C{dict} of {C{str}: C{str} or C{dict}}
        @note: the audio value can be a string containing the tts text or audio file location, or it can
        contain a C{dict} of multiple tts text phrases or audio locations. The keys of the dictionary represent
        the audio index, which is set in Dialog.setAudioIndex(). This is useful when multi-lingual content is used, where the same prompt is represented by multilingual audio files or text phrases.
        @see: L{AudioItem.__init__<dialogScripting.containers.AudioItem.__init__>}
              for the particulars of C{data}.
        """
        if pos is None:
            index = len(self._audio.keys())
            self._audio[index] = AudioItem(data)
        else:
            self._audio[pos] = AudioItem(data)
        return
        
    def addOption(self, option, dest):
        """
        Adds or replaces an L{OptionItem<dialogScripting.containers.OptionItem>}
        at this node using the specified input option and node destination.
        
        @param option: The input option.
        @type option: C{str}
        @param dest: The node destination.
        @type dest: C{str}
        @see: L{OptionItem.__init__<dialogScripting.containers.OptionItem.__init__>}
              for the particulars of C{option} and C{dest}.
        """
        self._options[option] = OptionItem(option, dest)
        return
        
    def addRecord(self, record):
        """
        Sets the L{RecordItem<dialogScripting.containers.RecordItem>} of this
        node using the specified recording information.
        
        @param record: The recording information.
        @type record: C{dict} of {C{str}: (C{str} or C{bool})}
        @see: L{RecordItem.__init__<dialogScripting.containers.RecordItem.__init__>}
              for the particulars of C{record}.
        """
        if record is not None:
            #self._recordItem(data)
            self._record = RecordItem(record) # FIX: gschlunz: corrected recording item addition
        return
    
    def addGoto(self, goto):
        """
        Sets the default next node destination of this node. An absolute node
        name is hashed, but a relative destination is kept as a raw string.
        
        @param goto: The default next node destination.
        @type goto: C{str}
        """
        #self._goto = goto
        if goto != None: # FIX: gschlunz: goto must be hashed if absolute node name
            # check if goto is a default (PREVIOUS or CURRENT)
            if goto in POSITION:
                self._goto = goto
            else:
                self._goto = self._hashValue(goto)
            self._rawGoto = goto
        else: 
            self._goto = None
            self._rawGoto = None
        return
    
    def removeAudio(self, pos):
        """
        Removes an L{AudioItem<dialogScripting.containers.AudioItem>} at the
        specified position (index) of this node only if the position is the last
        one.
        
        @param pos: The index of the audio item to be removed.
        @type pos: C{int}
        """
        index = len(self._audio.keys()) - 1
        if pos == index:
            self._audio.pop(pos)
        return

    def setExit(self, exit):
        """
        Sets the exit state for this node
        @param exit: C{True} to set this node to an exit state, C{False} otherwise.
        @type exit: C{bool}
        """
        self._exit = exit
    
    def __str__(self):
        """
        String representation of this C{Node}.
        
        @return: The string representation.
        @rtype: C{str}
        """
        string = '========== NODE: %s ==========\n' %self._name
        string += '\n-----Custom Items-----'
        for key in sorted(self._custom):
            string += '\nPos: %-3s %s' %(key, self._custom[key])
        string += '\n-----Audio Items------'
        for key in sorted(self._audio):
            string += '\nPos: %-3s %s' %(key, self._audio[key])
        string += '\n-----Option Items-----'
        for key in sorted(self._options):
            string += '\n%s' %(self._options[key])
        string += '\n-----Record Item------\n%s' %self._record
        string += '\n-----Goto Item------\n%s' %self._goto
        string += '\n-----Error Item-------\n%s\n\n' %self._error
        return string
    
    def _hashValue(self,value):
        """
        Computes a SHA hash of a value.
        
        @param value: A string value.
        @type value: C{str}
        @return: the SHA hash.
        @rtype: C{str}
        """
        # Generate a hash of the data to be stored        
        h = hashlib.sha1()
        h.update(value)
        hash = h.digest()
        
        return hash
