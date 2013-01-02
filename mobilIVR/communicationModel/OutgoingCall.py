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

Provides a communication model for outgoing calls
"""


#!/usr/bin/env python

import twisted.internet.reactor
from mobilIVR.utils.Session import setupNode, cleanup

import mobilIVR.application

from mobilIVR.ivr import IVRDialer

class HelloWorldOutgoingIVR(mobilIVR.application.Application):
    """
    Demonstrates how to dial a number and then provide an IVR user interface
    to the resulting call.
    
    This example mobilIVR application dials a number, greets the person
    being called, and hangs up.
    """
    
    def run(self, node):
        """ Called when a message is received """
        try:
		dialer = IVRDialer(node) # defined in mobilIVR.ivr.__init__
		print 'finding an available outgoing IVR resource'
		# find an ivr resource - this is a blocking call handled by the node, returning the address/port of an Asterisk Manager API server
		dialer.getResource()
		print 'resource found, establishing call with ivr script'
		# Creates/dials an outbound call, and returns an AGI IVR interface which we can use for interaction with the end user
		ivr = dialer.dial('00726349901')
		# Greet the user...
		ivr.say('Hello world')
		# ...and hang up the call
	except Exception, e:
		print 'Error: ' + str(e)
	finally:
		ivr.hangup()
		# Since this is just a demo, let's stop the entire program
		print 'call completed, terminating application and node'
		node.shutdown()


if __name__ == '__main__':
    # Set up our local node
    node = setupNode()
    # Publish our test application
    node.runApplication(HelloWorldOutgoingIVR())
    # Start everything, and clean up afterwards if necessary
    twisted.internet.reactor.run()
    cleanup()

