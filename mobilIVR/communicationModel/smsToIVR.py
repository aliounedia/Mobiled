#----------------------------------------------------------------------------#
#                                                                            #
#    Copyright (C) 2009 Department of Arts and Culture,                      #
#                       Republic of South Africa                             #
#    Contributer: Meraka Institute, CSIR                                     #
#    Author: Francois Aucamp                                                 #
#    Maintenance: Bryan McAlister                                            #
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
@author: Francois Aucamp

Provides a communication model for receiving an SMS and invoking an outgoing IVR call
"""

#!/usr/bin/env python

import twisted.internet.reactor
from mobilIVR.utils.Session import setupNode, cleanup

import mobilIVR.application

from mobilIVR.ivr import IVRDialer

class SMSToAudioCall(mobilIVR.application.SMSHandler):
    """ 
    Demonstrates how to handle an incoming SMS message,
    and how to call back the sender, and read the SMS back to him/her.
    
    This example mobilIVR application waits for an SMS, and when it receives
    one, it calls the user and reads the SMS back to him/her using
    text-to-speech.
    """

    def handleSMS(self, callerID, message, node):
        """ Called when a message is received """
        # See the simpler examples for descriptions of the steps taken in this method
        dialer = IVRDialer(node)
        print 'finding an available outgoing IVR resource'
        dialer.getResource()
        print 'resource found; establishing outgoing call'
        ivr = dialer.dial(callerID)
        ivr.say('You sent the following message')
        ivr.say(message)
        ivr.hangup()
        print 'call completed, application ended'

if __name__ == '__main__':
    # Set up our local node
    node = setupNode()
    # Publish our test application
    node.runApplication(SMSToAudioCall())
    # Start everything, and clean up afterwards if necessary
    twisted.internet.reactor.run() #IGNORE:E1101
    cleanup()
 
