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
Abstractions of containers (or items) for different kinds of data which a
L{Node<dialogScripting.node.Node>} needs.

@author: Mark Zsilavecz
@contact: mzsilavecz@csir.co.za
"""

import hashlib

from constants import *


class ContainerError(Exception):
    """
    Basic exception raised by the container classes.
    """

class AudioItem:
    """
    Holds data for audio prompts at a node. A prompt can either be an audio
    filename to be played back or text to be spoken by TTS.
    
    Multiple C{AudioItem}s can be added to a node, but each item must have a 
    sequential position (C{int}) starting at 0.
    """
        
    def __init__(self, data):
        """
        Initialises the object.
        
        @param data: Contains the source type and value for the audio item in the form:
                     {'SOURCE': source type, 'VALUE': value},

                     The source type key in the dictionary is C{'SOURCE'} and its
                     value must be one of the following constants:
                      - L{SRC_FILE<dialogScripting.constants.SRC_FILE>}
                      - L{SRC_TEXTF<dialogScripting.constants.SRC_TEXT>}
                      
                     
                     The value key in the dictionary is C{'VALUE'} and its value
                     is either an audio file name, or text to be spoken by TTS, or it can
                     contain a C{dict} of multiple tts text phrases or audio file names. 
                     The keys of the dictionary represent the audio index, which is set 
                     in L{Dialog.setAudioIndex(index)<dialogScripting.dialog.Dialog.setAudioIndex>}. 
                     This is useful when multi-lingual content is used, where the same prompt 
                     is represented by multilingual audio files or text phrases.
                     e.g. {0 : 'ENGLISH PROMPT', 1: 'AFRIKAANS PROMPT', 2: 'ZULU PROMPT'}
     
        @type data: C{dict} of {C{str}: C{str}}
        
                    
        """
        if data.has_key('SOURCE') and data.has_key('VALUE'):
            self._source = data['SOURCE']
            self._value = data['VALUE']
        else:
            raise ContainerError('AudioItem cannot be created. Invalid "dict".')
    
    def __str__(self):
        """
        String representation of this C{AudioItem}.
        
        @return: The string representation.
        @rtype: C{str}
        """
        return 'Source: %-20sValue: %s' %(self._source, self._value)
    
    def get(self):
        """
        Gets the data of this C{AudioItem}.
        
        @return: The C{AudioItem} data in the form::
                 {'SOURCE': source type, 'VALUE': value}
        @rtype: C{dict} of {C{str}: C{str}}
        """
        return {'SOURCE':self._source, 'VALUE':self._value}

class InputSettings:
    """
     Holds data for a nodes input settings. 
    
     Only one C{InputSettings} item is allowed per node
    """

    def __init__(self, data):
        """
        Initialises the object.

        @param data: Contains the nodes input settings in the form of a dictionary. The keys 
        specify the following settings:
          1. C{INPUTMODE}: C{str} for the mode of input, which can be the following:
            L{DTMF_INPUT<dialogScripting.constants.DTMF_INPUT>}, or 
            L{ASR_INPUT<dialogScripting.constants.ASR_INPUT>}
          2. C{MAXTIME}: C{int} for the maximum time (in milliseconds) to wait for user input (DTMF or ASR)
          3. C{MAXVISITCOUNT}: C{int} for the maximum number of times that the node may be visited upon an error before 
             it will reroute to another one.
          4. C{USEALLDTMF}: C{bool} set to False if only the specified DTMF input options should interrupt
             playback. Defaults to True to accept all dtmf digits as valid interrupts/input.
          5. C{BARGEINDURATION}: C{int} for the duration of speech input in I{milliseconds} that will interrupt 
             prompt audio playback
          6. C{CONSECUTIVESPEECHDURATION}: C{int} for the total duration of speech in I{milliseconds} to capture that will 
             end speech recognition
          7. C{SILENCETIMEOUT}: C{int} for the duration of silence in I{milliseconds} that will stop the recognizer  
             waiting for speech after prompt playback.
          8. C{GRAMMAR}: C{str} specifying the name of the grammar that the speech recognizer should use.
     
        @type data: C{dict} of {C{str}: C{str} or C{int} or C{bool}}
        
        @note: C{BARGEINDURATION}, C{CONSECUTIVESPEECHDURATION}, C{SILENCETIMEOUT},C{GRAMMAR} and C{VALIDOPTIONS} 
        only need to be set if this is an  ASR input node, i.e. C{INPUTMODE} is 
        L{ASR_INPUT<dialogScripting.constants.ASR_INPUT>}
        @note: C{USEALLDTMF} only needs to be set if this is a DTMF input node, i.e. C{INPUTMODE} is 
        L{DTMF_INPUT<dialogScripting.constants.DTMF_INPUT>}
    
        """
        self._useAllDtmfInput = None
        self._maxTime = None
        self._maxVisitCount = None
        self._bargeInDuration = None
        self._consecutiveSpeechDuration = None
        self._silenceTimeout = None
        self._grammar = None
        self._inputMode = None
        
        if data.has_key('MAXTIME') and data.has_key('MAXVISITCOUNT') and data.has_key('INPUTMODE')\
            and ((data['INPUTMODE'] == DTMF_INPUT)):
            self._maxTime = data['MAXTIME']
            self._maxVisitCount = data['MAXVISITCOUNT']
            self._inputMode = data['INPUTMODE']

            if data.has_key('USEALLDTMF'):
                self._useAllDtmfInput = data['USEALLDTMF']
            else:
                self._useAllDtmfInput = True

        elif data.has_key('MAXTIME') and data.has_key('MAXVISITCOUNT') and \
             data.has_key('BARGEINDURATION') and data.has_key('CONSECUTIVESPEECHDURATION') and \
             data.has_key('INPUTMODE') and (data['INPUTMODE'] == ASR_INPUT) and \
             data.has_key('GRAMMAR') and (data.has_key('SILENCETIMEOUT')):
            self._maxTime = data['MAXTIME']
            self._maxVisitCount = data['MAXVISITCOUNT']
            self._bargeInDuration = data['BARGEINDURATION']
            self._consecutiveSpeechDuration = data['CONSECUTIVESPEECHDURATION']
            self._silenceTimeout = data['SILENCETIMEOUT']
            self._inputMode = data['INPUTMODE']
            self._grammar = data['GRAMMAR']
        else:
            raise ContainerError('InputSettings cannot be created. Invalid or missing "dict" fields.')

    def getUseAllDtmfInput(self):
        """
        Gets the useAllDtmfInput setting
        @return: The useAllDtmfInput setting
        @rtype: C{bool}
        """
        return self._useAllDtmfInput

    def getInputMode(self):
        """
        Gets the input mode.
        @return: The input mode:
          L{DTMF_INPUT<dialogScripting.constants.DTMF_INPUT>}, or 
          L{ASR_INPUT<dialogScripting.constants.ASR_INPUT>}
        @rtype: C{str}
        """
        return self._inputMode

    def getMaxTime(self):
        """
        Gets the max time to wait for user input (DTMF or ASR)

        @return: The max time to wait for user input (DTMF or ASR)
        @rtype: C{int}
        """
        return self._maxTime
    
    def getMaxVisitCount(self):
        """
        Gets the maximum visit count for a node.
        
        @return: The maximum visit count for a node.
        @rtype: C{int}
        """
        return self._maxVisitCount

    def getBargeInDuration(self):
        """
        Gets the barge in duration. 
        @return: The barge in duration.
        @rtype: C{int}
        """
        return self._bargeInDuration

    def getConsecutiveSpeechDuration(self):
        """
        Gets the consecutive speech duration.
        @return: The consecutive speech duration.
        @rtype: C{int}
        """
        return self._consecutiveSpeechDuration

    def getSilenceTimeoutDuration(self):
        """
        Gets the silence timeout duration
        @return: The silence timeout duration
        @rtype: C{int}
        """
        return self._silenceTimeout


    def getGrammar(self):
        """
        Gets the name of the grammar that should be used by the speech recognizer
        @return: The grammar file  
        """
        return self._grammar

class OptionItem:
    """
    Holds data for options (inputs) to audio prompts at a node. An option can be
    either a DTMF digit or an ASR hypothesis.
    
    Multiple C{OptionItem}s can be added to a node.
    """
    
    def __init__(self, option, dest):
        """
        Initilises the object.
        
        @param option: The option which the user can select or enter. Note that
                       both ASR (hypothesis) and DTMF (digit) options must be
                       specified as strings.
        @type option: C{str}
        @param dest: The node destination to which the option will evaluate. It 
                     can be another node specified by its raw string name or a
                     relative node destination which must be one of the
                     following constants:
                      - L{PREVIOUS<dialogScripting.constants.PREVIOUS>}
                      - L{CURRENT<dialogScripting.constants.CURRENT>}
                     
                     Absolute node names will be hashed for efficient lookups.
        @type dest: C{str}
        """        
        self._option = option
        
        # create a hash of the option destination
        #destHash = self._hashValue(dest)
        #self._dest = destHash
        
        # check if dest is a default (PREVIOUS or CURRENT)
        if dest in POSITION: # FIX: gschlunz: allow POSITION as option destination
            self._dest = dest
        else:
            self._dest = self._hashValue(dest)
        # Store the destination in its original form
        self._rawDest = dest
        
    def __str__(self):
        """
        String representation of this C{OptionItem}.
        
        @return: The string representation.
        @rtype: C{str}
        """
        return 'Option: %-25sDest: %s' %(self._option, self._dest)
    
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
    
    def getOption(self):
        """
        Gets the option of this C{OptionItem}.
        
        @return: the ASR hypothesis or DTMF digit option.
        @rtype: C{str}
        """
        return self._option
    
    def getDest(self):
        """
        Gets the node destination of this C{OptionItem}.
        
        @return: The hashed absolute or raw relative destination.
        @rtype: C{str}
        """
        return self._dest
    
    def getRawDest(self):
        """
        Gets the node destination in original format.
        
        @return: The raw, unhashed destination.
        @rtype: C{str}
        """
        return self._rawDest
   
   
class ErrorItem:
    """
    Holds data for the errors which may occur whilst a node is executing. There
    are 3 types: B{UNKNOWN}, B{TIMEOUT} and B{REROUTE}.
    
    Only one C{ErrorItem} per node is allowed.
    """
    
    def __init__(self, data):
        """
        Initialises the object.
        
        @param data: Contains the 3 errors and their node destinations for the
                     error item. The error keys in the dictionary are as follows:
                      - C{'UNKNOWN'} - when input is given, but which is not
                        specified in an
                        L{OptionItem<dialogScripting.containers.OptionItem>} of
                        DTMF input nodes
                        e.g. DTMF '3', where only '1' and '2' are options
                      - C{'TIMEOUT'} - when the node times out whilst waiting
                        for required input.
                      - C{'REROUTE'} - when the maximum visit count of the
                        current node is reached upon successive B{UNKNOWN} or
                        B{TIMEOUT} events.
                     
                     The node destination values in the dictionary can be
                     another node specified by its raw string name or a relative
                     node destination which must be one of the following
                     constants:
                      - L{PREVIOUS<dialogScripting.constants.PREVIOUS>}
                      - L{CURRENT<dialogScripting.constants.CURRENT>}
                     
                     Absolute node names will be hashed for efficient lookups.
        @type data: C{dict} of {C{str}: C{str}}
        """
        if data.has_key('TIMEOUT') and data.has_key('UNKNOWN') and data.has_key('REROUTE'):
            # create a hash of the timeout destination
            #self._timeout = self._hashValue(data['TIMEOUT'])
            
            # check if timeout is a default (PREVIOUS or CURRENT)
            if data['TIMEOUT'] in POSITION: # FIX: gschlunz: allow POSITION as timeout destination
                self._timeout = data['TIMEOUT']
            else:
                self._timeout = self._hashValue(data['TIMEOUT'])
            # store timeout destination in its original form
            self._rawTimeout = data['TIMEOUT']
            # create a hash of the unknown destination
            #self._unknown = self._hashValue(data['UNKNOWN'])
            
            # check if unknown is a default (PREVIOUS or CURRENT)
            if data['UNKNOWN'] in POSITION: # FIX: gschlunz: allow POSITION as unknown destination
                self._unknown = data['UNKNOWN']
            else:
                self._unknown = self._hashValue(data['UNKNOWN'])
            # store unknown destination in its original form
            self._rawUnknown = data['UNKNOWN']
            # create a hash of the reroute destination
            #self._reRoute = self._hashValue(data['REROUTE'])
            
            # check if reroute is a default (PREVIOUS or CURRENT)
            if data['REROUTE'] in POSITION: # FIX: gschlunz: allow POSITION as rerouting destination
                self._reRoute = data['REROUTE']
            else:
                self._reRoute = self._hashValue(data['REROUTE'])
            # store reroute destination in its original form
            self._rawReRoute = data['REROUTE']
        else:
            raise ContainerError('ErrorItem cannot be created. Invalid "dict".')
        
    def __str__(self):
        """
        String representation of this C{ErrorItem}.
        
        @return: The string representation.
        @rtype: C{str}
        """
        return 'Timeout: %-20s Unknown: %s' %(self._timeout, self._unknown)
    
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
    
    def getTimeout(self):
        """
        Gets the node destination associated with a B{TIMEOUT} error.
        
        @return: The hashed absolute or raw relative B{TIMEOUT} destination.
        @rtype: C{str}
        """
        return self._timeout
    
    def getRawTimeout(self):
        """
        Gets the B{TIMEOUT} node destination in original format.
        
        @return: The raw, unhashed B{TIMEOUT} destination.
        @rtype: C{str}
        """
        return self._rawTimeout
        
    def getUnknown(self):
        """
        Gets the node destination associated with an B{UNKNOWN} error.
        
        @return: The hashed absolute or raw relative B{UNKNOWN} destination.
        @rtype: C{str}
        """
        return self._unknown
    
    def getRawUnknown(self):
        """
        Gets the B{UNKNOWN} node destination in original format.
        
        @return: The raw, unhashed B{UNKNOWN} destination.
        @rtype: C{str}
        """
        return self._rawUnknown
    
    def getReRoute(self):
        """
        Gets the node destination associated with a B{REROUTE} error.
        
        @return: The hashed absolute or raw relative B{REROUTE} destination.
        @rtype: C{str}
        """
        return self._reRoute
    
    def getRawReroute(self):
        """
        Gets the B{REROUTE} node destination in original format.
        
        @return: The raw, unhashed B{REROUTE} destination.
        @rtype: C{str}
        """
        return self._rawReRoute

    
class RecordItem:
    """
    Holds data required to record audio at a node.
    
    Only one C{RecordItem} per node is allowed.
    """
    
    def __init__(self, data):
        """
        Initialises the object.
        
        @param data: Contains the information to allow a node to record speech
                     from a caller. The dictionary must hold the following keys
                     (the value types are stated in brackets):
                      - C{'FILENAME'} (C{str}) for the name of the file.
                      - C{'MAXTIME'} (C{str}) for the maximum recording time.
                      - C{'INTKEYS'} (C{str}) for the keys which will interrupt
                        the recording.
                      - C{'PLAYBEEP'} (C{bool}) for whether a beep should be
                        played beforehand as prompt.
                      - C{'SILENCETIMEOUT'} (C{int}) for the amount of silence that will
                        interrupt the recording
                      - C{'CUSTOMSILDET'} (C{bool}) for whether custom silence detection should be
                        used
        @type data: C{dict} of {C{str}: (C{str} or C{bool})}
        """
        if data.has_key('FILENAME') and data.has_key('MAXTIME') and\
           data.has_key('INTKEYS') and data.has_key('PLAYBEEP') and data.has_key('SILENCETIMEOUT'):
            self._filename = data['FILENAME']
            self._maxTime = data['MAXTIME']
            #self._intKeys = data['KEYS']
            self._intKeys = data['INTKEYS'] # FIX: gschlunz: corrected dict key
            self._playBeep = data['PLAYBEEP']
            self._silenceTimeout = data['SILENCETIMEOUT']
            if data.has_key('CUSTOMSILDET'):
                self.custom_silence_detection = data['CUSTOMSILDET']
            else:
                self.custom_silence_detection = False
        else:
            raise ContainerError('RecordItem cannot be created. Invalid "dict".')
        
    def __str__(self):
        """
        String representation of this C{RecordItem}.
        
        @return: The string representation.
        @rtype: C{str}
        """
        return 'Filename: %-20sTime: %-8sInterrupts: %-10sPlay Beep: %-6s'\
                %(self._filename, self._maxTime, self._intKeys, self._playBeep)
    
    def getRecord(self):
        """
        Gets the data of this C{RecordItem}.
        
        @return: The C{RecordItem} data in the form::
                  {'FILENAME': filename, 
                   'MAXTIME': maximum time, 
                   'INTKEYS': interrupt keys, 
                   'PLAYBEEP': beep condition}
        @rtype: C{dict} of {C{str}: (C{str} or C{bool})}
        """
        return {'FILENAME':self._filename, 
                'MAXTIME':self._maxTime, 
                'INTKEYS':self._intKeys, 
                'PLAYBEEP':self._playBeep,
                'SILENCETIMEOUT':self._silenceTimeout,
                'CUSTOMSILDET':self.custom_silence_detection}
    
    
class CustomItem:
    """
    Holds data required to execute a custom function at a node.
    
    Multiple C{CustomItem}s can be added to a node, but each item must have a 
    sequential position (C{int}) starting at 0.
    """
    
    def __init__(self, data):
        """
        Initialises the object.
        
        @param data: Contains the information to allow a node to call a 
                     function with customized implementation, e.g. accessing a database. 
                     The dictionary must hold the following keys (the value types are stated in
                     brackets):
                      - C{'PATH'} (C{str}) for the path to the module.
                      - C{'MODULE'} (C{str}) for the name of the module.
                      - C{'CLASS'} (C{str}) for the name of the class (B{UNUSED}).
                      - C{'FUNCTION'} (C{str}) for the name of the function to
                        call.
        @type data: C{dict} of {C{str}: C{str}}
        """
        if data.has_key('PATH') and data.has_key('MODULE') and \
            data.has_key('FUNCTION') and data.has_key('CLASS'):
            self._path = data['PATH']
            self._module = data['MODULE']
            self._function = data['FUNCTION']
            self._class = data['CLASS']
        else:
            raise ContainerError('CustomItem cannot be created. Invalid "dict".')
           
    def __str__(self):
        """
        String representation of this C{CustomItem}.
        
        @return: The string representation.
        @rtype: C{str}
        """
        return 'Function: %-20sClass: %-15sModule: %-15sPath: %s'\
               %(self._function, self._class, self._module, self._path)
               
    def get(self):
        """
        Gets the data of this C{CustomItem}.
        
        @return: The C{CustomItem} data in the form::
                  {'PATH': module path, 
                   'MODULE': module name, 
                   'CLASS': class name, 
                   'FUNCTION': function name}
        @rtype: C{dict} of {C{str}: C{str}}
        """
        return {'FUNCTION':self._function, 'CLASS':self._class,
                'MODULE':self._module, 'PATH':self._path}

