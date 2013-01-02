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
DialogScripting constants.

@author: Mark Zsilavecz
@contact: mzsilavecz@csir.co.za

@var EVENT_CUSTOM: Signals that a custom function of the current node should be called.
@type EVENT_CUSTOM: C{int}
@var EVENT_AUDIO: Signals that an audio prompt of the current node should be spoken or played.
@type EVENT_AUDIO: C{int}
@var EVENT_OPTION: Signals that the option (input response) to the audio prompt of the current node should be processed.
@type EVENT_OPTION: C{int}
@var EVENT_RECORD: Signals that audio should be recorded for the current node.
@type EVENT_RECORD: C{int}
@var EVENT_UNKNOWN: Signals that an unknown option was received by the current node.
@type EVENT_UNKNOWN: C{int}
@var EVENT_TIMEOUT: Signals that the current node timed out whilst waiting for an option. 
@type EVENT_TIMEOUT: C{int}
@var EVENT_REROUTE: Signals that the current node reached its maximum visit count and must reroute to another node.
@type EVENT_REROUTE: C{int}
@var EVENT_EXIT: Signals that the dialog should exit.
@type EVENT_EXIT: C{int}

@var SRC_FILE_DTMF: Specifies that the audio prompt plays an audio file as output and expects DTMF as input.
@type SRC_FILE_DTMF: C{str}
@var SRC_TEXT_DTMF: Specifies that the audio prompt says text via TTS as output and expects DTMF as input.
@type SRC_TEXT_DTMF: C{str}
@var SRC_FILE_ASR: Specifies that the audio prompt plays an audio file as output and expects ASR as input.
@type SRC_FILE_ASR: C{str}
@var SRC_TEXT_ASR: Specifies that the audio prompt says text via TTS as output and expects ASR as input.
@type SRC_TEXT_ASR: C{str}

@var PREVIOUS: Indicates the previous node as destination.
@type PREVIOUS: C{str}
@var CURRENT: Indicates the current node as destination.
@type CURRENT: C{str}
@var POSITION: Collection of valid relative node destinations.
@type POSITION: C{list} of C{str}
"""

#{ Node Events
EVENT_CUSTOM  = 0
EVENT_AUDIO   = 1
EVENT_OPTION  = 2
EVENT_RECORD  = 3
EVENT_UNKNOWN = 4
EVENT_TIMEOUT = 5
EVENT_REROUTE = 6# FIX: gschlunz: added rerouting event
EVENT_EXIT    = 7
#}

#{ Input prompt types
DTMF_INPUT = 'DTMF_INPUT'
ASR_INPUT = 'ASR_INPUT'
#}

#{ Audio Prompt Source Types
#SRC_FILE_DTMF = 'SRC_FILE_DTMF'
#SRC_TEXT_DTMF = 'SRC_TEXT_DTMF'
#SRC_FILE_ASR  = 'SRC_FILE_ASR'
#SRC_TEXT_ASR  = 'SRC_TEXT_ASR'
SRC_FILE = 'SRC_FILE'
SRC_TEXT = 'SRC_TEXT'

#}

#{ Relative Node Destinations
POSITION = ['PREVIOUS','CURRENT']
PREVIOUS = 'PREVIOUS'
CURRENT = 'CURRENT'
#}

#DTMF input possibilites
DTMF_1 = '1'
DTMF_2 = '2'
DTMF_3 = '3'
DTMF_4 = '4'
DTMF_5 = '5'
DTMF_6 = '6'
DTMF_7 = '7'
DTMF_8 = '8'
DTMF_9 = '9'
DTMF_0 = '0'
DTMF_AST = '*'
DTMF_HASH = '#'

ALL_DTMF_DIGITS = '0123456789*#'

# {call transfer failure reasons
CALL_TRANSFER_BUSY = 'BUSY'
CALL_TRANSFER_NO_ANSWER = 'NO_ANSWER'







