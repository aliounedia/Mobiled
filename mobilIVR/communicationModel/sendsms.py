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

Provides a communication model for sending an SMS
"""

#!/usr/bin/env python

import twisted.internet.reactor
from mobilIVR.utils.Session import setupNode, cleanup

import mobilIVR.application
from mobilIVR.sms import SMSSender

class HelloWorldSMS(mobilIVR.application.Application):
    """
    Example of how to send an SMS.
    
    This MobilIVR application sends an SMS, and exits.
    """
        
    def run(self, node):
        sms = SMSSender(node)
        # blocking resource-gathering call
        print 'finding an available outgoing SMS resource'
        sms.getResource()
        print 'resource found; sending message'
        sms.sendMessage('hello world', '1234567')
        print 'sms sent, terminating application and node'
        node.shutdown()


if __name__ == '__main__':
    # Set up our local node
    node = setupNode()
    # Publish our test application
    node.runApplication(HelloWorldSMS())
    # Start everything, and clean up afterwards if necessary
    twisted.internet.reactor.run()
    cleanup()
