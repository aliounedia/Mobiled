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

Provides a MobilIVR node running in a separate thread.
"""

import threading

import mobilIVR.node

import twisted.internet.reactor

class MobilIVR(mobilIVR.node.MobilIVRNode):
    """ MobilIVR node running in a separate thread
    
    This is useful for using mobilIVR as a service/library in other projects
    with their own main loops (such as certain web applications).
    """
    def __new__(cls, *args, **kwargs):
        if not '_node' in cls.__dict__:
            cls._node = object.__new__(cls, *args, **kwargs)
            cls._node._isSetup = False
            cls._node._isStarted = False
        return cls._node

    class startingThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.setName('MobilIVR singelton')

        def run(self):
            twisted.internet.reactor.run(installSignalHandlers=0) #IGNORE:E1101

    def __init__(self, udpPort=4000, knownNodeAddress=None):
        """ Constructor for a singleton MobilIVR node running in a
        separate thread
        
        @note: The first time an instance of this class is created, the node
               must be set up before use (using the setup* and/or load* APIs
               in the MobilIVRNode class), and then started using start(). This
               is not required for any subsequent instances that are created
               during the course of the host application.
        
        @param udpPort: The UDP port number on which the node will run in the
                        peer-to-peer network
        @type udpPort: int
        @param knownNodeAddress: (Optional) A tuple containing the IP address
                                 (str) and UDP port number of another node on
                                 the peer-to-peer network
        @type knownNodeAddress: tuple
        """
        if self._node._isSetup == False:
            self._node._isSetup = True
            if knownNodeAddress != None:
                self._knownNodes = [knownNodeAddress]
            else:
                self._knownNodes = None
            mobilIVR.node.MobilIVRNode.__init__(self, udpPort=udpPort)

    def start(self):
        if self._node._isStarted == False:
            print ' ======> starting node'
            self._node._isStarted = True
            self._node.joinNetwork(self._knownNodes)
            t = MobilIVR.startingThread()
            t.start()
        else:
            print ' =====> node is already running'
