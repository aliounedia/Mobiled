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

"Wrapper" resource to combine the Asterisk Manager API and FastAGI server into one easily-importable module
"""

import time
import random

import twisted.internet.reactor

import mobilIVR.resources

import manager_api

class ResourceNotFound(Exception):
    """ Raised when an outgoing ivr resource could not be located
    """

class IVRDialer(mobilIVR.resources.Resource):
    """
    "Wrapper" resource to combine the Asterisk Manager API and FastAGI
    server into one easily-importable module
    """
    def __init__(self, node):
        self._localNode = node
        self._astManAPIAddress = None
        self._astManAPIPort = None
        self._astManAPIUsername = None
        self._astManAPIPassword = None
        self._astManAPIChannel = None
        self.gateway_address = None
        self.prefix = None
        self.internal_extension_length = None
        self.agiRequestHandler = None
        self._resourceTuple = None
        self._rogueHandler = False
   
    def getResource(self):
        """ Find and retrieve an instance of this resource; blocking operation
        
        This is used for initiating outgoing calls.
        
        @raise ResourceNotFound: Raised if the resource cannot be located
        """
        #TODO: stop this dialer object from claiming more than one resource
        def gotResourceDetails(remoteContact, resourceInfo, resourceTuple):
            self._gotResource = True
            if resourceInfo != None:
                self._localNode.claimedResources += 1
                self._astManAPIAddress, self._astManAPIPort, self._astManAPIChannel, self._astManAPIUsername, self._astManAPIPassword, self.gateway_address, self.prefix, self.internal_extension_length = resourceInfo
                self._resourceTuple = resourceTuple
                if self._astManAPIAddress in ('127.0.0.1', 'localhost') and remoteContact != None:
                    self._astManAPIAddress = remoteContact.address
            else:
                self._resourceTuple = None
                self._localNode._log.error('No outgoing ivr resource could be located!')
                raise ResourceNotFound('No outgoing ivr resource could be located!')
        self._gotResource = False
        self._localNode._log.info('Attempting to locate outgoing ivr resource')
        twisted.internet.reactor.callFromThread(self._localNode.getResource, 'ivr', gotResourceDetails, removeResource=True)
        while self._gotResource == False:
            time.sleep(0.1)
    
    def getResourceIfExists(self):
        """ Find and retrieve an instance of this resource; non-blocking operation
        
        This is used for initiating outgoing calls.
        
        @raise ResourceNotFound: Raised if the resource cannot be located
        """
        def gotResourceDetails(remoteContact, resourceInfo, resourceTuple):
            self._gotResource = True
            if resourceInfo != None:
                self._localNode.claimedResources += 1
                self._astManAPIAddress, self._astManAPIPort, self._astManAPIChannel, self._astManAPIUsername, self._astManAPIPassword, self.gateway_address, self.prefix, self.internal_extension_length = resourceInfo
                self._resourceTuple = resourceTuple
                if self._astManAPIAddress in ('127.0.0.1', 'localhost') and remoteContact != None:
                    self._astManAPIAddress = remoteContact.address
            else:
                self._resourceTuple = None
                raise ResourceNotFound('No outgoing ivr resource could be located!')
        self._gotResource = False
        twisted.internet.reactor.callFromThread(self._localNode.getResource, 'ivr', gotResourceDetails, blocking=False, removeResource=True)
        while self._gotResource == False:
            time.sleep(0.1)
        return self._astManAPIAddress != None
    
    def releaseResource(self):
        """ Release this resource (call this when done with it).
        
        This frees up the outgoing IVR telephone line for use by other applications.
        
        @TODO: some way of specifying WHICH resource to release......
        """
        def releaseCompleted():
            self._localNode.claimedResources -= 1
            self._resourceTuple = None
            self._gotResource = False
        
        if self._resourceTuple != None:
            # Release the resource (put it back into the tuple space)
            self._gotResource = True
            twisted.internet.reactor.callFromThread(self._localNode.publishResource, 'ivr', originalPublisherID=self._resourceTuple[2], returnCallbackFunc=releaseCompleted) #IGNORE:E1101
            while self._gotResource == True:
                time.sleep(0.1)
        
    def dial(self, number):
        """ Dial a number; this returns when the call is active; this object can then be used for IVR interaction
        
        @raise Exception: Raised (with error message) if the dial failed
        @raise ResourceNotFound: Raised if no outgoing ivr resource could be located
        
        @return: An IVRInterface instance which can be used to interact (using
                 IVR) with the person being called
        @rtype: mobilIVR.fastagi.IVRInterface
        """
        # First check if an outgoing ivr resource was located
        if self._resourceTuple == None:
            raise ResourceNotFound('No outgoing ivr resource could be located!')
        # Prime server for incoming FastAGI request
        handlerID = self._astManAPIChannel+str(random.randint(0, 999))
        self._localNode.fastAGIServer.setIVRHandler(handlerID, self)
                
        # do ManAPI calling thing
        self.agiRequestHandler = False
        manAPI = manager_api.ManAPIClient(self._astManAPIAddress, self._astManAPIPort, self._astManAPIUsername, self._astManAPIPassword)
        try:
            #print 'init dial; local FastAGI address is:', self._localNode.fastAGIServer.server_address
            
            # Add prefix to number if it is specified, and if the number is an external number
            if self.prefix and not self.internal_extension_length:
                # in this case always add the prefix, since no extension length specified
                number = self.prefix + number
            elif self.prefix and len(number) > int(self.internal_extension_length):
                number = self.prefix + number
            
            # Add gateway address to number if it is specified
            if self.gateway_address:
                number = number + '@' + self.gateway_address
            
            self._localNode._log.info('Invoking outgoing call on ' + number)
            manAPI.dial(number, self._astManAPIChannel, self._localNode.fastAGIServer.server_address, handlerID)
            currentWaitTime = 0
            while not self.agiRequestHandler:
                time.sleep(0.1)
                currentWaitTime += 0.1
                if currentWaitTime > 10:
                    self._rogueHandler = True
                    self._localNode._log.error('Dialout failed, handler response timeout')
                    raise Exception('Dialout failed, handler response timeout')            
        except Exception, e:
            self._localNode._log.error('Error while attempting to invoke outgoing call: ' + str(e))
            # Let the script handle this
            raise
 
        # Wait until server responds
        #while self.agiRequestHandler == False:
        # if no dial exception and if the handler has not yet been set, wait for a reasonable duration, then quit
        # move below check into previous exception scope, handler must be false if dial fails,
        # if dial succeeds, wait for a reasonable time to receive the call handler, then finally quit
        
            #TODO: implement a timeout in case Asterisk never responds
            #time.sleep(0.1)
        self._localNode._log.info('Handing control over to IVR application')
        return self.agiRequestHandler
