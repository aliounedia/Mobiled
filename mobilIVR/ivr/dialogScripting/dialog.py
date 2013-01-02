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
The dialogScripting entry point: an abstraction of the interactive voice
response (IVR) dialog which steps through nodes in a finite state machine
(FSM)-like manner.

Each node represents a state in the dialog with a specific audio prompt which
expects certain user input (such as DTMF or ASR). The input (or a default
fallback) decides which node in the dialog should be run next. Error handling in
the node caters for incorrect input by redirecting the user to another node
specialised for this purpose. Optional functionality may be added to a node to
allow processing of any data at that point.

@author: Mark Zsilavecz
@contact: mzsilavecz@csir.co.za
"""

import sys, os, re
from datetime import datetime
import hashlib

from node import *
from constants import *
#from containers import *
import loggingmessages
from history import CallHistory

import traceback
#TODO: logging of times: record time(start/end) of each audio item in a node, 
#      option and dest selected
# store previous option

import mobilIVR.ivr.fastagi_constants as fastagi_constants
from mobilIVR.logger import setupLogger, closeLogFileHandler

class DialogError(Exception):
    """
    Basic exception raised by the L{Dialog<dialogScripting.dialog.Dialog>} class.
    """

class Dialog:
    """
    Abstracts an IVR dialog. It holds all the L{Node<dialogScripting.node.Node>}s
    and provides methods to add and run them.
    
    @ivar _nodes: The set of constituent nodes.
    @type _nodes: C{dict} of {C{str}: L{Node<dialogScripting.node.Node>}}
    @ivar _node_start: The starting node.
    @type _node_start: L{Node<dialogScripting.node.Node>}
    @ivar _node_curr: The currently executed node.
    @type _node_curr: L{Node<dialogScripting.node.Node>}
    @ivar _nodes_visited: A history of the hashed names of previously visited
                          nodes.
    @type _nodes_visited: C{list} of [C{str}]
    """
    
    def __init__(self, ivr_handle):
        """
        Initialises the object.
        
        @param ivr_handle: Provides access to the C{mobilIVR.ivr.fastAGI.IVRInterface}
        @type ivr_handle: C{mobilIVR.ivr.fastAGI.IVRInterface}
        """
        self._nodes = {}
        self._global_opts = {}
        
        self._node_start = None
        self._node_curr = None
        self._nodes_visited = []
        
        self._time_start = None
        self._time_end = None
        
        self._customResults = {}
        
        self.ivr_handle = ivr_handle
        self.callerID = ivr_handle.callerID
        self.dialedNumber = ivr_handle.dialedNumber
        self.uniqueID = ivr_handle.getVariable("UNIQUEID")
          
        self._audioIndex = 0
        self.delayAfterInput = 0

        self._lastInput = None
        self._lastAsrConfidenceScore = None
        self._lastAsrConfidenceLevelHigh = None
        
        self._record_res = None
         
        #self._repeatTimeout = {'COUNT':0, 'MAX':0}
        #self._repeatUnknown = {'COUNT':0, 'MAX':0}
        self._statistics = {'START':None, 'END':None, 'NODES':[]}
        self._history = None
        
        self._log = setupLogger(debug=True, name=self.uniqueID.replace('.','_'))
        self._dialog_completed = False
        
        
        
    def setStartNode(self, start):
        """
        Sets the starting node.
        
        @param start: The raw string name of the starting node.
        @type start: C{str}
        
        """
        # hash the start node name, ensure naming format consistency same as Node objects internal representation 
        startHash = self._hashValue(start)
        
        self._node_start = startHash
        
        return
            
    def setGlobalOptions(self, options):
        """
        Defines the global input options applicable
        to all nodes in the dialog.
        
        @param options: The global input options.
        @type options: C{dict} of {C{str}: C{str}}
        @see: The documentation on the C{options} keyword argument in
              L{Node.__init__<dialogScripting.node.Node.__init__>}
        """
        # Add option items.
        self._global_opts = {}
        if options is not None:
            for opt in options.keys():
                self._global_opts[opt] = OptionItem(opt, options[opt])
        
        return
    
    def setAudioIndex(self, index):
        """
        Sets the audio index, which is used as a key for selecting a nodes audio in the case where
        the audio['VALUE'] type is a dictionary.
        
        @param index: the index or key to use when accessing the audio['VALUE'] from a dictionary
        @see: The documentation describing audio items L{AudioItem<dialogScripting.containers.AudioItem.__init__>} and 
        L{Node.__init__<dialogScripting.node.Node.__init__>}
        """
        self._audioIndex = index

    def setDelayAfterInput(self, delay):
        """
        Sets the default amount of time to wait after dtmf input has been provided.
        
        @param delay: the delay duration in seconds
        @type delay: int
        """
        self.delayAfterInput = delay

    def _setLastInput(self, _input): 
        """
        Sets the most recent input (ASR utterance or DTMF digit)
        @param option: the most recent input
        @type option: C{str}
        """
        self._lastInput = _input
    
    def addCustomNode(self, name, custom, goto=None, applyGlobals=True, exit=False):
        """
        Adds a custom node to the dialog. This is essentially an interface to the 
        the constructor of L{Node<dialogScripting.node.Node>}.

        @see: The documentation on the node constructor
              L{Node.__init__<dialogScripting.node.Node.__init__>}
        """
        self.addNode(name=name, inputSettings=None, error=None, custom=custom,\
                     goto=goto, applyGlobals=applyGlobals, exit=exit)

    def addPlaybackNode(self, name, audio, goto=None, custom=None, applyGlobals=True,exit=False):
        """
        Adds an audio playback node to the dialog. This is essentially an interface to the 
        the constructor of L{Node<dialogScripting.node.Node>}.

        @see: The documentation on the node constructor
              L{Node.__init__<dialogScripting.node.Node.__init__>}
        """
        self.addNode(name=name, inputSettings=None, error=None, goto=goto, \
                     audio=audio, custom=custom, applyGlobals=applyGlobals, exit=exit) 

    def addDtmfInputNode(self, name, inputSettings, error, audio=None, options=None, custom=None,\
                         applyGlobals=True, exit=False):
        """
        Adds a DTMF input prompt node to the dialog. This is essentially an interface to the 
        the constructor of L{Node<dialogScripting.node.Node>}.
        
        @note: For the L{inputSettings<dialogScripting.containers.InputSettings>} parameter, 
               the C{INPUTMODE} field is set by this method to 
               L{DTMF_INPUT<dialogScripting.constants.DTMF_INPUT>}

        @see: The documentation on the node constructor
              L{Node.__init__<dialogScripting.node.Node.__init__>}
        """
        inputSettings['INPUTMODE'] = DTMF_INPUT
        self.addNode(name=name, inputSettings=inputSettings, error=error, audio=audio, custom=custom, \
                     options=options, applyGlobals=applyGlobals, exit=exit)

    def addAsrInputNode(self, name, inputSettings, error, goto, audio=None, custom=None):
        """
        Adds an ASR input prompt node to the dialog. This is essentially an interface to the
        constructor of L{Node<dialogScripting.node.Node>}.

        Once an input phrase has been recognized with a high confidence, this node will navigate to the destination 
        specified in the goto parameter. If there is a low recognition confidence, the node will navigate to the UNKNOWN
        error destination. If nothing is recognized (e.g. silence) after c{inputSettings[SILENCETIMEOUT]} seconds, the node 
        will navigate  to the TIMEOUT error destination. 

        @note: For the L{inputSettings<dialogScripting.containers.InputSettings>} parameter, 
        the C{INPUTMODE} field is set by this method to L{ASR_INPUT<dialogScripting.constants.ASR_INPUT>}

        @see: The documentation on the node constructor
              L{Node.__init__<dialogScripting.node.Node.__init__>}
        """

        inputSettings['INPUTMODE'] = ASR_INPUT

        self.addNode(name=name, inputSettings=inputSettings, error=error, goto=goto, audio=audio, \
                     custom=custom)
    
    def addNode(self, name,  inputSettings=None, error=None, goto=None, audio=None, \
                custom=None, options=None, record=None, applyGlobals=True, exit=False): 
        """
        Adds a new node to the dialog. This is basically a wrapper method
        around the constructor of a L{Node<dialogScripting.node.Node>}.
        
        @see: The documentation on the node constructor
              L{Node.__init__<dialogScripting.node.Node.__init__>}
        """
        # hash the node name, ensure naming format consistency same as Node objects internal representation 
        nameHash = self._hashValue(name)
                      
        self._nodes[nameHash] = Node(name, inputSettings=inputSettings, error=error, goto=goto, \
                                     audio=audio, custom=custom, options=options, record=record, \
                                     applyGlobals=applyGlobals, exit=exit)
        return
        
    def run(self):
        """
        Runs the IVR dialog by launching the starting node in the FSM. The
        specified functions are used to execute the audio prompts and recordings
        for each node.
        
        Each node signals events in its execution life cycle to access its
        various L{container<dialogScripting.containers>}s (or items) and finally
        to determine the next node.
        
        The order in which events are processed is:
         1. L{EVENT_CUSTOM<dialogScripting.constants.EVENT_CUSTOM>}. This is the
            start-off event for all nodes. All
            L{CustomItem<dialogScripting.containers.CustomItem>}s will be
            accessed and their custom functions executed before anything else.
            Upon completion, an audio event is signaled - see
            L{Node.getCustom<dialogScripting.node.Node.getCustom>}.
         2. L{EVENT_AUDIO<dialogScripting.constants.EVENT_AUDIO>}. All
            L{AudioItem<dialogScripting.containers.AudioItem>}s are processed to
            produce the audio prompts at the node; only at the final item is
            user input allowed. Upon completion, either a record, option or exit
            event is signaled - see
            L{Node.getAudio<dialogScripting.node.Node.getAudio>}.
         3. L{EVENT_OPTION<dialogScripting.constants.EVENT_OPTION>}. The user
            input is processed as follows:
             - if a B{TIMEOUT} occurred, a timeout event is signaled.
             - if no input was required, the next node is set to the default
               B{GOTO} destination and a custom event is signaled.
             - if input was required, the user input is compared against the
               options in the
               L{OptionItem<dialogScripting.containers.OptionItem>}s and
               resolved into the correct destination - see
               L{Node.getDest<dialogScripting.node.Node.getDest>}. If the
               destination exists, the next node is set to it and a custom event
               is signaled. If it does not exist, an unknown event is signaled.
         4. L{EVENT_RECORD<dialogScripting.constants.EVENT_RECORD>}. The
            L{RecordItem<dialogScripting.containers.RecordItem>} information is
            used to record audio from the user. Upon completion, either an exit
            or option event is signaled - see
            L{Node.getRecord<dialogScripting.node.Node.getRecord>}.
         5. Error events:
             5.1. L{EVENT_UNKNOWN<dialogScripting.constants.EVENT_UNKNOWN>}. If
                  the visit count of the node is still below its limit, the
                  next node is set to the unknown destination which is resolved
                  from the
                  L{ErrorItem<dialogScripting.containers.ErrorItem>} - see
                  L{Node.getDest<dialogScripting.node.Node.getDest>}. If the
                  visit count is over its limit, a reroute event is signaled.
             5.2. L{EVENT_TIMEOUT<dialogScripting.constants.EVENT_TIMEOUT>}. If
                  the visit count of the node is still below its limit, the
                  next node is set to the timeout destination which is resolved
                  from the
                  L{ErrorItem<dialogScripting.containers.ErrorItem>} - see
                  L{Node.getDest<dialogScripting.node.Node.getDest>}. If the
                  visit count is over its limit, a reroute event is signaled.
             5.3. L{EVENT_REROUTE<dialogScripting.constants.EVENT_REROUTE>}. The
                  next node is set to the reroute destination which is resolved
                  from the
                  L{ErrorItem<dialogScripting.containers.ErrorItem>} - see
                  L{Node.getDest<dialogScripting.node.Node.getDest>}.
         6. L{EVENT_EXIT<dialogScripting.constants.EVENT_EXIT>}. The dialog is
            instructed to exit.
                
        
        @attention: The first 4 functions which return DTMF and ASR input must
                    return it in the following format:
                     - less than zero (type C{int}) if a B{TIMEOUT} occurs,
                     - zero (type C{int}) if no input is required (i.e. the node
                       must select the default B{GOTO} destination) and
                     - greater than zero (type C{str}), which is the input
                       result itself, if input is required
        @see: The L{ivr<dialogScripting.ivr>} module for function templates
        """
        
        # Call a function from an external Python module.
        def runExternal(custom, node, results):
            if custom['PATH']:
                sys.path.append(custom['PATH'])
            ext_module = None
            ext_func = None
            try:
                # Check if the function is an attribute of a dialog child class
                if hasattr(self, custom['FUNCTION']):
                    funct = getattr(self, custom['FUNCTION'])
                    try:
                        funct(node, results)
                    except Exception, e:
                        traceback.print_exc()
                        raise DialogError('Function failed: %s [%s]' 
                                          %(custom['FUNCTION'], e))
                # Else run as an external module
                elif custom['MODULE']:
                    ext_module = __import__(custom['MODULE'])
                    if hasattr(ext_module, custom['FUNCTION']):
                        ext_func = getattr(ext_module, custom['FUNCTION'])
                        try:
                            ext_func(node, results)
                        except Exception, e:
                            raise DialogError('Function failed: %s [%s]' 
                                            %(custom['FUNCTION'], e))
                    else:
                        raise DialogError('Cannot find function: %s' 
                                        %custom['FUNCTION'])
                else:
                    raise DialogError('Cannot find function: %s' 
                                    %custom['FUNCTION'])
            
            except ImportError:
                raise DialogError('Could not import module: [%s in %s]' 
                                  %(custom['MODULE'], custom['PATH']))
            finally:
                if sys.modules.has_key(ext_module):
                    sys.modules.pop(ext_module)
                del ext_module
                del ext_func
            return 
            
        # Gets the name of the next node from the selected option and sets the 
        # current node to the correct node.
        def getNextNode(option):
            def previous(visited, offset=0):
                return visited[len(visited) - (2 + offset)]
            
            #self._nodes_visited.append(self._node_curr.getName())
            if (len(self._nodes_visited) == 0) or (self._nodes_visited[-1] != self._node_curr.getName()): # FIX: gschlunz: only record first of consecutive visits so that PREVIOUS works
                self._nodes_visited.append(self._node_curr.getName())
            
            #self._customResults['PREVIOUS_OPTION'] = option
            end_time = datetime.now()
            self._node_curr.setTimeExit(str(end_time))
            self._statistics['NODES'].append(self._node_curr.getStats())
            node = self._node_curr.getDest(option, self._global_opts, self._nodes_visited)

            if node != None:
                inf = loggingmessages.SELECTING_NEXT_NODE % (option, ((node in POSITION) and node) or self._nodes[node].getRawName())
                self._log.info(inf)

                            
            if node is not None:
                if node == 'CURRENT':
                    self._history.end_node(end_time)
                    self.finalizeNode(self._node_curr)
                    self._node_curr.reset()
                elif node == 'PREVIOUS':
                    self._history.end_node(end_time)
                    self.finalizeNode(self._node_curr)
                    self._node_curr.reset()
                    self._node_curr = self._nodes[previous(self._nodes_visited)]
                else:
                    if self._nodes.has_key(node):
                        self._history.end_node(end_time)
                        self.finalizeNode(self._node_curr)
                        self._node_curr.reset()
                        self._node_curr = self._nodes[node]
                    else:
                        self._node_curr.setEvent(EVENT_UNKNOWN)
            else:
                self._node_curr.setEvent(EVENT_UNKNOWN)
                       
            self._node_curr.setTimeEnter(str(end_time))
            self._node_curr.setLastOption(option)
            self._history.start_node(self._node_curr.getRawName(), end_time)
            return 
        
        # While in a dialog, step through the nodes and depending on the event
        # perform an action.
        try:
            if not self._validate():
                raise DialogError('Dialog is not valid.')
                                   
            start_time = datetime.now()
            self._statistics['START'] = str(start_time)
            self._history = CallHistory(session_id    = self.ivr_handle.getVariable("UNIQUEID"),
                                        answer_time   = start_time,
                                        caller_number = self.ivr_handle.callerID,
                                        dailed_number = self.ivr_handle.dialedNumber)
            self._node_curr = self._nodes[self._node_start]
            
            self._history.start_node(self._node_curr.getRawName(), start_time)
            isExit = False
            result = 0
            event = -1 # FIX: gschlunz: added for debug
            while not isExit:
                prev_event = event # FIX: gschlunz: added for debug
                event = self._node_curr.getEvent()
                if (event == EVENT_CUSTOM) and (event != prev_event): # FIX: gschlunz: added for debug
                    print '----------------------------------------------------------------------------'
                    inf = loggingmessages.CURRENT_NODE % (self._node_curr.getRawName())
                    self._log.info(inf)
                
                if event == EVENT_CUSTOM:
                    custom = self._node_curr.getCustom()
                    if custom is not None:
                        temp = runExternal(custom, self._node_curr, self._customResults)
                    #if not temp:
                    #   raise DialogError()
                    
                elif event == EVENT_AUDIO:
                    audio = self._node_curr.getAudio()
                    # check if the audio value is a dictionary, in this case select the audio
                    # based on the global audio index
                     
                    if audio:
                        if type(audio['VALUE']) == dict:
                            audioValue = audio['VALUE'][self._audioIndex]
                        else:
                            audioValue = audio['VALUE']
                        
                        audio_start = str(datetime.now())
                        valid = ''

                        currentInputSettings = self._node_curr.getInputSettings()
                        playBackMode = None
                        if currentInputSettings:
                            playBackMode = currentInputSettings.getInputMode()
                        else:
                            # if no input settings are specified, default to <dialogScripting.constants.DTMF_INPUT> mode
                            playBackMode = DTMF_INPUT
                        
                        if playBackMode == DTMF_INPUT:
                            if audio['SOURCE'] == SRC_FILE:
                                nodeOptions = self._node_curr.getOptions()
                                
                                if nodeOptions and len(nodeOptions) > 0:
                                    # if options exist, take all possible dtmf_digits as input if possible (node setting)
                                    if self._node_curr.getUseAllDtmfInput():
                                        valid = ALL_DTMF_DIGITS # defined in constants
                                    # else only take the current options as valid input
                                    else:
                                        globalOptionsString = self.getGlobalOptionsString()
                                        specificOptionsString = self.getNodeOptionsString(self._node_curr)
                                        valid = specificOptionsString + globalOptionsString
                                    
                                elif len(self._global_opts) > 0:
                                # if no options, but global options exist, only take global options as input
                                    valid = self.getGlobalOptionsString()

                                # check if input will be received for appropriate logging
                                if self._node_curr.getMaxtime() == 0:
                                  inf = loggingmessages.PLAY_AUDIO % (self._node_curr.getRawName())
                                  self._log.info(inf)
                                else:
                                  inf = loggingmessages.PLAY_AUDIO_WAIT_INPUT_DTMF % (self._node_curr.getRawName())
                                  self._log.info(inf)
                                    

                                result = self.ivr_handle.playDTMF(audioValue, valid, self._node_curr.getMaxtime(), self.delayAfterInput)
                            elif audio['SOURCE'] == SRC_TEXT:
                                nodeOptions = self._node_curr.getOptions()
                                
                                if nodeOptions and len(nodeOptions) > 0:
                                    # if options exist, take all possible dtmf_digits as input if possible (node setting)
                                    if self._node_curr.getUseAllDtmfInput():
                                        valid = ALL_DTMF_DIGITS # defined in constants
                                    # else only take the current options as valid input
                                    else:
                                        globalOptionsString = self.getGlobalOptionsString()
                                        specificOptionsString = self.getNodeOptionsString(self._node_curr)
                                        valid = specificOptionsString + globalOptionsString

                                        
                                elif len(self._global_opts) > 0:
                                # if no options, but global options exist, only take global options as input
                                    valid = self.getGlobalOptionsString()

                                # check if input will be received for appropriate logging
                                if self._node_curr.getMaxtime() == 0:
                                  inf = loggingmessages.PLAY_AUDIO % (self._node_curr.getRawName())
                                  self._log.info(inf)
                                else:
                                  inf = loggingmessages.PLAY_AUDIO_WAIT_INPUT_DTMF % (self._node_curr.getRawName())
                                  self._log.info(inf)
                                
                                result = self.ivr_handle.sayDTMF(audioValue, valid, self._node_curr.getMaxtime())
                            else:
                                raise DialogError('Unrecognised data source type.')
                        
                        elif playBackMode == ASR_INPUT:

                            inf = loggingmessages.PLAY_AUDIO_WAIT_INPUT_ASR % (self._node_curr.getRawName())
                            self._log.info(inf)

                            if audio['SOURCE'] == SRC_FILE:
                                currentInputSettings = self._node_curr.getInputSettings()
                                #maxTime = currentInputSettings.getMaxTime()
                                maxTime = self._node_curr.getMaxtime()
                                maxVisit = currentInputSettings.getMaxVisitCount()
                                bargeInDuration = currentInputSettings.getBargeInDuration()
                                consecutiveSpeechDuration = currentInputSettings.getConsecutiveSpeechDuration()
                                silenceTimeout = currentInputSettings.getSilenceTimeoutDuration()
                                grammar = currentInputSettings.getGrammar()

                                result = self.ivr_handle.playASR(audioValue, grammar, maxTime, bargeInDuration, consecutiveSpeechDuration,\
                                                      silenceTimeout)

                            elif audio['SOURCE'] == SRC_TEXT:
                                currentInputSettings = self._node_curr.getInputSettings()
                                #maxTime = currentInputSettings.getMaxTime()
                                maxTime = self._node_curr.getMaxtime()
                                maxVisit = currentInputSettings.getMaxVisitCount()
                                bargeInDuration = currentInputSettings.getBargeInDuration()
                                consecutiveSpeechDuration = currentInputSettings.getConsecutiveSpeechDuration()
                                silenceTimeout = currentInputSettings.getSilenceTimeoutDuration()
                                grammar = currentInputSettings.getGrammar()

                                result = self.ivr_handle.sayASR(audioValue, grammar, maxTime, bargeInDuration, consecutiveSpeechDuration,\
                                                      silenceTimeout)
                            else:
                                raise DialogError('Unrecognised data source type.')
                        else:
                            raise DialogError('Unrecognised data source type.')

                        self._node_curr.setTimeAudio(audio_start, str(datetime.now()))
                        if result > 0:
                            self._node_curr.setTimeInput(str(datetime.now()))
                            # ensure that if any input is received during playback, that the next event
                            # is an option event
                            self._node_curr.setEvent(EVENT_OPTION)
                            #bargein = True
                            # lock ??
                    
                elif event == EVENT_OPTION:
                    if result == 0:
                        getNextNode('GOTO')
                    elif result > 0:
                        
                        if playBackMode == DTMF_INPUT:
                            dtmf = result[0]
                            dtmf_time = result[1]
                            dtmf_is_bargin = result[2]
                            dtmf_playback_stop_time = result[3]
                            inf = loggingmessages.DTMF_INPUT % (str(dtmf))
                            inf += '; Input timestamp: %s;' %(str(dtmf_time))
                            inf += ' Barge in = %s' % (str(dtmf_is_bargin))
                            inf += ' Playback stop time = %s' % (str(dtmf_playback_stop_time))
                            self._history.set_dtmf_results(dtmf, dtmf_time, dtmf_is_bargin)
                            getNextNode(dtmf)
                            # only set the last input once the next node has been selected by getNextNode
                            self._setLastInput(dtmf)
                        elif playBackMode == ASR_INPUT:
                            # unpack the ASR result tuple (utterance, confidence level, confidence score)
                            utterance = result[0]
                            asrConfidenceLevel = result[1]
                            asrConfidenceScore = result[2]

                            self._lastAsrConfidenceScore = asrConfidenceScore
                                                                                                               
                            if asrConfidenceLevel == fastagi_constants.ASR_HIGH_CONFIDENCE:
                                # For high confidence, route to the GOTO destination
                                self._lastAsrConfidenceLevelHigh = True
                                getNextNode('GOTO')
                                inf = loggingmessages.ASR_INPUT % ('\'' + utterance + ' (High confidence '\
                                                      + str(asrConfidenceScore) + ')\'')
                            elif asrConfidenceLevel == fastagi_constants.ASR_LOW_CONFIDENCE:
                                # For low confidence, route to the UNKNOWN destination
                                self._lastAsrConfidenceLevelHigh = False
                                #getNextNode('UNKNOWN')
                                self._node_curr.setEvent(EVENT_UNKNOWN)
                                inf = loggingmessages.ASR_INPUT % ('\'' + utterance + ' (Low confidence '\
                                                      + str(asrConfidenceScore) + ')\'')

                            # only set the last input once the next node has been selected by getNextNode
                            bargedIn = result[3]
                            bargeInTime = int(result[4])*20 # 20 ms frames
                            if bargedIn == '1':
                            	inf += ' Barged in:%s at %s ms' %(bargedIn,bargeInTime)
                            self._setLastInput(utterance)
                            self._history.set_asr_results(utterance, asrConfidenceScore, asrConfidenceLevel,
                                                          bargedIn == '1', bargeInTime)

                        self._log.info(inf)
                        
                        result = 0
                    elif result < 0:
                        #getNextNode('TIMEOUT')
                        self._node_curr.setEvent(EVENT_TIMEOUT) # FIX: gschlunz: handle timeout via timeout event to allow rerouting
                        result = 0
                        self._setLastInput(None)
                
                elif event == EVENT_RECORD:
                    inf = loggingmessages.RECORDING_AUDIO % (self._node_curr.getRawName())
                    self._log.info(inf)

                    record_start = str(datetime.now())
                    #record = self._node_curr.getRecord()['FILENAME'],
                    record = self._node_curr.getRecord().getRecord() # FIX: gschlunz: method calls must return dict
                    self._record_res = self.ivr_handle.recordAudio(record['FILENAME'], record['MAXTIME'],
                                record['INTKEYS'], record['PLAYBEEP'], record['SILENCETIMEOUT'],
                                record['CUSTOMSILDET'])
                    if self._record_res[2] == '1':
                        self._log.info('Recording terminated using # key')
                    self._history.set_record_results(self._record_res[1], self._record_res[2])
                    #self._node_curr.setEvent(EVENT_OPTION)
                    self._node_curr.setTimeRecord(record_start, str(datetime.now()))
                
                elif event == EVENT_UNKNOWN:
                    visitCount = self._node_curr.getVisitCount()

                    if playBackMode == DTMF_INPUT:
                        inf = loggingmessages.INVALID_DTMF_INPUT 
                        self._history.set_is_invalid(True)
                    elif playBackMode == ASR_INPUT:
                        inf = loggingmessages.INVALID_ASR_INPUT 
                        self._history.set_is_invalid(True)
                    self._log.info(inf)    

                    if (visitCount < self._node_curr.getMaxVisitCount()):
                                        
                        getNextNode('UNKNOWN')
                    else:
                        inf = '>>> run: UNKNOWN: rerouting...'
                        #self._log.info(inf)
                        #getNextNode('REROUTE')
                        self._node_curr.setEvent(EVENT_REROUTE) # FIX: gschlunz: handle rerouting via rerouting event

                    inf = loggingmessages.NODE_VISIT_COUNT % (str(visitCount))
                    self._log.info(inf)
                                        
                elif event == EVENT_TIMEOUT:
                    visitCount = self._node_curr.getVisitCount()
                    #inf = '>>> run: TIMEOUT: visitCount =', visitCount
                    self._history.set_is_timeout(True)
                    inf = loggingmessages.TIMEOUT 
                    self._log.info(inf)
                    inf = loggingmessages.NODE_VISIT_COUNT % (str(visitCount))
                    self._log.info(inf)
                    #self._log.info(inf)
                    if (visitCount < self._node_curr.getMaxVisitCount()):
                        getNextNode('TIMEOUT')
                    else:
                        inf = '>>> run: TIMEOUT: rerouting...'
                        #self._log.info(inf)
                        #getNextNode('REROUTE')
                        self._node_curr.setEvent(EVENT_REROUTE) # FIX: gschlunz: handle rerouting via rerouting event
                
                elif event == EVENT_REROUTE:  # FIX: gschlunz: added rerouting event handler
                    self._history.set_is_maxtries(True)
                    getNextNode('REROUTE')
                
                elif event == EVENT_EXIT:
                    inf = loggingmessages.END_NODE_NOTICE % (self._node_curr.getRawName())
                    self._log.info(inf)
                    isExit = True
                    self._dialog_completed = True
                
                else:
                    raise DialogError('Event not defined.')
            
            
        except Exception, e:
            traceback.print_exc()
            raise DialogError(e)
        finally:
            exit_time = datetime.now()
            self._history.end_node(exit_time)
            self._history.set_hangup_time(exit_time)
            self.finalizeDialog()
            self._statistics['END'] = str(datetime.now())
        return
    
    def getNode(self, nodeName):
        """
        Returns the requested Node
        @param NodeName: The name of the node requested, or None if the node doesn't exist.
        @type NodeName: C{dialogScripting.node.Node} or C{None}
        """
        node = None
        try:            
            node = self._nodes[nodeName]
        except Exception, e:
            pass

        return node
    
    def getPreviousNode(self):
        """
        Returns the previous node that was visited
        @return: The previous node
        @rtype: C{dialogScripting.node.Node} or C{None}
        """
        def previous(visited):
            return visited[len(visited) - 1]
        previous_node = None
        try:
            previous_node = self._nodes[previous(self._nodes_visited)]
        except Exception, e:
            self._log.error('Error retrieving previous node: ' + str(e))
        return previous_node

    def getCallerID(self):
        """
        Returns the callerID for this Dialog session
        """
        return self.callerID

    def getDialedNumber(self):
        """
        Returns the originally dialed number
        """    
        return self.dialedNumber

    def getUniqueSessionID(self):
        """
        Returns the uniqeID for this Dialog session
        """
        return self.uniqueID
    
    def getIvrHandle(self):
        """
        Returns the ivrHandle 
        """
        return self.ivr_handle

    def getSessionLogger(self):
        """
        Returns a call's session logger
        @return: Session logger
        @rtype: C{logger}
        """
        return self._log

    def setCustomHistory(self, dic):
        """
        Sets history custom value for the given node.
        @param dic: custom history
        @type dic: C{dic}
        """
        self._history.set_custom(dic)

    def getCallHistory(self):
        """
        Returns a call's history
        @return: Call history
        @rtype: C{CallHistory}
        """
        return self._history

    def getGlobalOptionsString(self):
        """
        Returns the global options, if any. Global options are concatenated into a string
        @rtype: C{String}
        """
        globalOptions = self._global_opts.keys()
        globalOptionsString = ''
        if len(globalOptions) > 0:
            for option in globalOptions:
                globalOptionsString = globalOptionsString + option
        
        return globalOptionsString
    
    def getNodeOptionsString(self, node):
        """
        Returns the nodes options. Options are concatenated into a string
        @rtype: C{String}
        """
        options = node.getOptions()
        optionsString = ''
        if len(options) > 0:
            for option in options:
                optionsString = optionsString + option
                
        return optionsString

    def finalizeDialog(self):
        """
        Interface to be implemented within the IVR application. Typically used for ensuring that 
        final operations are performed after the call dialog has completed gracefully, or with an exception.
        @note: This method will be called by L{Dialog<dialogScripting.dialog.Dialog>} once the dialog terminates.
        """   

    def finalizeNode(self, node):
        """
        Interface to be implemented within the IVR application. Meant for cleanup and reset
        needs after a node has completed.  Called after each node completes, but before the nodes
        'reset' method is called.
        @param node: Node being finalized
        @type node: L{Node<dialogScripting.node.Node>}s
        """   

    def getLastInput(self): 
        """
        @return: Returns the most recent input option
        @rtype: C{str}
        """
        return self._lastInput

    def getLastAsrConfidenceScore(self):
        """
        @return: Returns the most recent asr input confidence score
        @rtype: C{float}
        """
        return self._lastAsrConfidenceScore

    def wasLastAsrConfidenceLevelHigh(self):
        """
        @return: Returns C{True} if the most recent asr input confidence level was high, else C{False}
        @rtype: C{bool}
        """
        return self._lastAsrConfidenceLevelHigh
    
    def getLastRecordingSilencePercentage(self):
        """
        @return: Returns the last recordings percentage silence.
        @rtype: C{float}
        """
        if self._record_res[1] is not None:
            return float(self._record_res[1])
    
    def _convertDTMF(self, dtmf):
        """
        Removes the offset from the DTMF result returned by Asterisk.
        
        @param dtmf: The Asterisk DTMF result as an integer.
        @type dtmf: C{int}
        @return: The proper DTMF digit as a string.
        @rtype: C{str}
        """
        if dtmf == 42:  # Asterisk (*)
            return "*"
        elif dtmf == 35:  # Hash (#)
            return "#"
        else:
            return str(dtmf - 48)  
    
    def _validate(self):
        """
        Validates this dialog. It checks that the file names given in the dialog
        are valid, i.e. that the audio files and external Python modules exist.
        It also checks that all the nodes referenced in this dialog exist.
        
        @return: Whether the dialog is valid or not.
        @rtype: C{bool}
        """
        nodes = self._nodes.keys()
        valid = True
        for node in nodes:
            # Check audio file names.
            #audio = self._nodes[node].getAllAudio()
            #for item in audio.keys():
                #temp = audio[item].get()
                #src = temp['SOURCE']
                #filename = temp['VALUE'][self._audioIndex]
                #if src == SRC_FILE_DTMF or src == SRC_FILE_ASR:
                    #if not os.path.isfile(filename):
                        #print 'Audio file does not exist: %s, Node: %s' \
                               #%(filename, self._nodes[node].getRawName())
                        #valid = False
            # Check external Python module file names.
            custom = self._nodes[node].getAllCustom()
            for item in custom.keys():
                temp = custom[item].get()
                path = temp['PATH']
                if not path:
                    path = ''
                module = temp['MODULE']
                if module:
                    if not os.path.isfile(os.path.join(str(path), str(module) + '.py')):
                        print 'Module does not exist: %s, Node: %s' \
                              %(module, self._nodes[node].getRawName())
                        valid = False
            # Check node names (in the destination field of options).
            options = self._nodes[node].getAllOptions()
            for option in options.keys():
                dest = options[option].getDest()

# NOTE deactivating for now, EVAL functionality not checked
# TODO: Will have to use different split, not based on spaces since names / destinations with spaces results in multiple dests
# Enforce format ?
#                temp = re.sub(r'^EVAL\:| +if +| +elif +| +else +|prev\=\=|'\
#                               'prev\!\=|last\=\=|last\!\=|\(|\)|\:', ' ', 
#                               dest).strip(' ')
#                parts =  re.split(r' +', temp)
                
                parts = [dest]
                                
                for item in parts:
                    # First check for defaults (PREVIOUS, CURRENT)
                    if not options[option].getRawDest() in POSITION: # FIX: gschlunz: allow POSITION as option destination
                        if (item != None) and (not self._nodes.has_key(item)):
                            print 'Node name or option destination is not valid. Node: %s, Option destination: %s' \
                                   %(self._nodes[node].getRawName(),  options[option].getRawDest())
                            valid = False
            
            # Check goto has valid destination
            gotoDest = self._nodes[node].getGoto()
            # First check for defaults (PREVIOUS, CURRENT)
            if not gotoDest in POSITION:
                if (gotoDest != None) and (not self._nodes.has_key(gotoDest)):
                    print 'Goto destination is not valid. Node: %s, Option destination: %s' \
                                   %(self._nodes[node].getRawName(),  self._nodes[node].getRawGoto())
                    valid = False
                
            # Check error (timeout & unknown) have valid destination
            if self._nodes[node].getError() != None:
              timeoutDest = self._nodes[node].getError().getTimeout()
              unknownDest = self._nodes[node].getError().getUnknown()
              # First check for defaults (PREVIOUS, CURRENT)
              if not timeoutDest in POSITION: # FIX: gschlunz: allow POSITION as timeout destination
                  if (timeoutDest != None) and (not self._nodes.has_key(timeoutDest)):
                      print 'Error timeout destination is not valid. Node: %s, Error timeout destination: %s' \
                                %(self._nodes[node].getRawName(),  self._nodes[node].getError().getRawTimeout())
                      valid = False
              if not unknownDest in POSITION: # FIX: gschlunz: allow POSITION as unknown destination
                  if (unknownDest != None) and (not self._nodes.has_key(unknownDest)):
                      print 'Error unknown destination is not valid. Node: %s, Error Unknown destination: %s' \
                                %(self._nodes[node].getRawName(),  self._nodes[node].getError().getRawUnknown())
                      valid = False
            
        return valid
    
    #{ Logging Methods
    def writeStats(self, filename):
        try:
            file = open(filename, 'w')
            file.write('Start: %s\r\n' %self._statistics['START'])
            file.write('End:   %s\r\n' %self._statistics['END'])
            
            file.write('%-20s %-20s %-30s %-30s %-30s %-30s %-30s\r\n' 
                       %('Name:', 'Option:', 'Entered:', 'Exited:', 'Input:', 'Audio:', 'Record:'))
            for node in self._statistics['NODES']:
                file.write('%-20s %-20s %-30s %-30s %-30s %-30s %-30s\r\n' 
                           %(node['NAME'], node['OPTION'], node['ENTERED'], node['EXITED'], node['INPUT'], node['AUDIO'], node['RECORD']))
            file.close()
        except IOError, e:
            raise DialogError(e)
        return
    #}
    
    def __str__(self):
        """
        String representation of this C{Dialog}.
        
        @return: The string representation.
        @rtype: C{str}
        """
        string = ''
        for node in sorted(self._nodes.keys()):
            string += '%s' %self._nodes[node]
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

    def __del__(self):
        """ Make sure that the session log file is closed """

        # Do final logging
        if self._dialog_completed:
            inf = loggingmessages.USER_HANGUP_NOTICE % (loggingmessages.EXPECTED_HANGUP)
        else:
            inf = loggingmessages.USER_HANGUP_NOTICE % (loggingmessages.UNEXPECTED_HANGUP)
        self._log.info(inf)

        closeLogFileHandler(self._log)
      
        

   
