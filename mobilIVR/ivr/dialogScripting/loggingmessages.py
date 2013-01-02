#----------------------------------------------------------------------------#
#                                                                            #
#    Copyright (C) 2009 Department of Arts and Culture,                      #
#                       Republic of South Africa                             #
#    Contributer: Meraka Institute, CSIR                                     #
#    Author: Bryan McAlister                                                 #
#    Contact: bmcalister@csir.co.za                                          #
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

@author: Bryan McAlister
@contact: bmcalister@csir.co.za  
"""

CURRENT_NODE = "Current node name: %s"
PLAY_AUDIO = "Playing audio; node name = %s"
PLAY_AUDIO_WAIT_INPUT_ASR = "Playing audio and waiting for ASR input; node name = %s"
PLAY_AUDIO_WAIT_INPUT_DTMF = "Playing audio and waiting for DTMF input; node name = %s"
RECORDING_AUDIO = "Recording audio; node name = %s"

ASR_INPUT = "ASR input receieved = %s"
DTMF_INPUT = "DTMF input receieved = %s"
INVALID_ASR_INPUT = "Invalid ASR input received"
INVALID_DTMF_INPUT = "Invalid DTMF input received"
TIMEOUT = 'Input timeout occurred' 

NODE_VISIT_COUNT = "Node visit count = %s"

# SELECT Default GOTO or UNKNOWN or REROUTE node
SELECTING_NEXT_NODE = "Selecting next node for option = %s; destination node name = %s"

#SELECTING_NEXT_NODE_ASR_INPUT = "Selecting next node with ASR input = %s; destination node name = %s"
#SELECTING_NEXT_NODE_DTMF_INPUT = "Selecting next node for DTMF input = %s; destination node name = %s"

# ASR confirmation implemented at app level
ASR_USER_CONFIRM_TRUE = "User confirmed ASR candidate: %s"
# TODO:
ASR_USER_CONFIRM_FALSE_EXIT = "Asr confirmation max tries limit reached"

END_NODE_NOTICE = "End node reached: node name = %s"
USER_HANGUP_NOTICE = "User hangup; reason = %s"
EXPECTED_HANGUP = 'Expected hangup'
UNEXPECTED_HANGUP = 'Unexpected hangup'

CALL_TRANSFERRING = "Call is being transferred ... "
# TODO:
CALL_TRANSFER_SUCCESS = "Call transfer success"
CALL_TRANSFER_FAILURE = "Call transfer failure %s"

# TODO
RECORD_AUDIO_SUCCESS = "Record of audio succeeded"
RECORD_AUDIO_FAILURE = "Record of audio failed"

# TODO
UNEXPECTED_FAILURE = "Unexpected failure, call ended"



































