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
@author: Bryan McAlister

Provides a Static Tuple Space  
"""

#!/usr/bin/env python

import hashlib, random
import time
import socket
import cPickle
from twisted.internet import defer
import twisted.internet.reactor
from twisted.python import failure

from rpc import protocol
from rpc.contact import Contact
from rpc.msgtypes import ErrorMessage
from datastore import DictDataStore

def rpcmethod(func):
    """ Decorator to expose StaticTupleSpace methods as remote procedure calls
    
    Apply this decorator to methods in the StaticTupleSpace class (or a subclass) in order
    to make them remotely callable via the RPC mechanism.
    """
    func.rpcmethod = True
    return func

class DataFormatError(Exception):
    """ Raised when the format of data to be published or found is not correct 
    """

class StaticTupleSpacePeer():
    """ Enables tuples to be stored locally, and in turn allows non-local tuples to be located at
        static network locations provided as input at start-up 
    """
    def __init__(self, id=None, udpPort=4000, dataStore=None, routingTable=None, networkProtocol=None):
        if id != None:
            self.id = id
        else:
            self.id = self._generateID()
        self.port = udpPort
        
        if networkProtocol == None:
            self._protocol = protocol.KademliaProtocol(self)
        else:
            self._protocol = networkProtocol
        
        self._joinDeferred = None
        self.contactsList = []
        self.dataStore = DictDataStore()
        

    def put(self, sTuple, originalPublisherID=None):
        """ Used to write a tuple or serialized (string) data into a tuple space
        
        @note: This method is generally called "out" in tuple space literature,
               but is renamed to "put" in this implementation to match the 
               renamed "in"/"get" method (see the description for C{get()}).
        
        @param sTuple: The tuple to write into the static tuple space (it
                       is named "sTuple" to avoid a conflict with the Python
                       C{tuple} data type).
        @type sTuple: tuple
        
        @rtype: twisted.internet.defer.Deferred
        """
        
        if isinstance(sTuple, tuple):
            # Parse the tuple
            sData = (sTuple[0], sTuple[1])
            ownerID = sTuple[2]
            
            # Serialize the data
            tupleValue = cPickle.dumps(sData)
        elif isinstance(sTuple, str):
            tupleValue = sTuple
            ownerID = originalPublisherID
        else:
            raise DataFormatError("Error, expected a tuple or a serialized string as input")
        
        # TODO: may need to implement more advanced tuple space, based on data types
        #       for now tuples need to match exactly (element value as well as element order)     
        
        # Generate a hash of the data to be stored        
        h = hashlib.sha1()
        h.update(tupleValue)
        mainKey = h.digest()
        
        originallyPublished = 0        
        now = int(time.time())
        
#        print 'publishing :'
#        print 'key ' + str((mainKey,)) 
#        print 'value' + tupleValue 
        
        # TODO: Check if the tuple has already been stored, also check that other peers tuples don't replace
        # locally stored tuples
        self.dataStore.setItem(mainKey, tupleValue, now, originallyPublished, ownerID)
        
        df = defer.Deferred() 
        # invoke call-back now
        df.callback(tupleValue)
        
        return df

    
    def get(self, template):
        """ Reads and removes (consumes) a tuple from the tuple space (blocking)
        
        @type template: tuple
        
        @note: This method is generally called "in" in tuple space literature,
               but is renamed to "get" in this implementation to avoid
               a conflict with the Python C{in} keyword.
        @return: a matching tuple,  or None if no matching tuples were found
        """
        
        # TODO: consider to implement blocking mechanism that waits until a tuple is found
        # TODO: consider to implement mechanism that removes the tuple (resource marshalling)
        
     
        return self.findTuple(template)

    
    def getIfExists(self, template, getListenerTuple=False):
        """ Reads and removes (consumes) a tuple from the tuple space (non-blocking)
        
        @type template: tuple
        
        @param getListenerTuple: If set to True, look for a I{listener tuple}
                                 for this template; this is typically used
                                 to remove event handlers.
        @type getListenerTuple: bool
        
        @return: a matching tuple,  or None if no matching tuples were found
        
        @note: This method is generally called "in" in tuple space literature,
               but is renamed to "get" in this implementation to avoid
               a conflict with the Python C{in} keyword.
        """
        return self.findTuple(template)
    
    
    def read(self, template, numberOfResults=1):
        """ Non-destructively reads a tuple in the tuple space (blocking)
        
        This operation is similar to "get" (or "in") in that the peer builds a
        template and waits for a matching tuple in the tuple space. Upon
        finding a matching tuple, however, it copies it, leaving the original
        tuple in the tuple space.
        
        @note: This method is named "rd" in some other implementations.
        
        @param numberOfResults: The maximum number of matching tuples to return.
                                If set to 1 (default), return the tuple itself,
                                otherwise return a list of tuples. If set to 0
                                or lower, return all results.
        @type numberOfResults: int
        
        @return: a matching tuple, or list of tuples (if C{numberOfResults} is
                 not set to 1, or None if no matching tuples were found
        @rtype: twisted.internet.defer.Deferred
        """
        returnedTuple = self.findTuple(template)
        
        if returnedTuple != None:
            #returnTuples = []
            #returnTuples.append(returnedTuple)
            #return returnTuples
            return returnedTuple
        else:
            return None

    
    def readIfExists(self, template, numberOfResults=1):
        """ Non-destructively reads a tuple in the tuple space (non-blocking)
        
        This operation is similar to "get" (or "in") in that the peer builds a
        template and waits for a matching tuple in the tuple space. Upon
        finding a matching tuple, however, it copies it, leaving the original
        tuple in the tuple space.
        
        @note: This method is named "rd" in some other implementations.
        
        @param numberOfResults: The maximum number of matching tuples to return.
                                If set to 1 (default), return the tuple itself,
                                otherwise return a list of tuples. If set to 0
                                or lower, return all results.
        @type numberOfResults: int
        
        @return: a matching tuple, or list of tuples (if C{numberOfResults} is
                 not set to 1, or None if no matching tuples were found
        @rtype: twisted.internet.defer.Deferred
        """
        returnedTuple = self.findTuple(template)
        
        if returnedTuple != None:
            #returnTuples = []
            #returnTuples.append(returnedTuple)
            #return returnTuples
            return returnedTuple
        else:
            return None

    @rpcmethod
    def findTuple(self, value):
        """ Used to search the dataStore for a tuple, if invoked locally it 
            searches this peers datastore. If it is invoked via RPC it will 
            search for the tuple at the remote peer
        
            @param value: The tuple to search for  
            
            return: a matching tuple,  or None if no matching tuples were found
        """
        
        if isinstance(value, tuple):
            # parse the tuple 
            dataTuple = (value[0], value[1])
            
            # Serialize the tuple
            serialValue = cPickle.dumps(dataTuple)
        elif isinstance(value, str):
            serialValue = value
        else:
            raise DataFormatError("Error, expected a tuple or a serialized string as input")
        
        # print 'searching for ' + serialValue
        
        # Generate a hash of the value       
        h = hashlib.sha1()
        h.update(serialValue)
        mainKey = h.digest()
        
        keys = self.dataStore.keys()
        
        try:
            dataStoreTuple = self.dataStore.__getitem__(mainKey)
        except Exception:
            
            # The data wasn't found, so return None
            return None
        
        
        # Note, returning value given as input since it was found in the data store
        # and it is in tuple format, not serialized as in the data store
        # TODO: Implement mechanism to handle tuple type (resource/handler)
        if len(value) == 5:
            extraArgs = []
            if value[3] == None:
                extraArgs.append('')
            else:
                extraArgs.append(value[3])
            if value[4] == None:
                extraArgs.append('')
            else:
                extraArgs.append(value[4])
            
            returnTuple = (value[0], value[1], self.dataStore.originalPublisherID(mainKey), extraArgs[0], extraArgs[1])
        else:
            returnTuple = (value[0], value[1], self.dataStore.originalPublisherID(mainKey))
        return returnTuple
        
    
    @rpcmethod 
    def getOwnedTuples(self):
        """ Used to obtain all of the tuples owned by this peer via RPC, 
                        
            @return: a list containing all of the tuples and their owner ID's 
                     in the following format [(ownerID, tuple1), ..., (ownerID, tuple n)]
            @rtype: list
        """
        
        dataStoreKeys = self.dataStore.keys()
        tuples = []
        
        for key in dataStoreKeys:
            if (self.dataStore.originalPublisherID(key) == self.id):           
                idTuple = []
                idTuple.append(self.id)
                idTuple.append(self.dataStore.__getitem__(key))
                tuples.append(idTuple)
        
        return tuples
    
    @rpcmethod
    def getAllTuples(self):
        """ Used to obtain all of the tuples stored at a remote peer via RPC, 
                       
            @return: a list containing all of the tuples and their owner ID's 
                     in the following format [(ownerID, tuple1), ..., (ownerID, tuple n)]
            @rtype: list
        """
        dataStoreKeys = self.dataStore.keys()
        tuples = []
        
        for key in dataStoreKeys:
            idTuple = []
            idTuple.append(self.dataStore.originalPublisherID(key))
            idTuple.append(self.dataStore.__getitem__(key))
            tuples.append(idTuple)
            
        return tuples
            
    def findContact(self, contactID):
        """ Used to search for a contact inside of this peers contactList
            @return: a contact if it was found
        """
        
        #print 'searching for ' + str((contactID,))
        for contact in self.contactsList:
            #print 'contact ' + str((contact.id,))
                       
            if contact.id == contactID:
                return contact
            
    
    def refreshDataStore(self):
        """ Refreshs the datastore, ensuring that the tuples obtained from remote peers are still valid and that
            those peers are still alive """
        
        # TODO: Implement this
    
    def joinNetwork(self, knownNodeAddresses=None):
        """ 
        Causes the peer to join the static network; A list of known contacts addresses is given as input.
        Each of these contacts are polled to see if they are alive. 
        
        @param knownNodeAddresses: A sequence of tuples containing IP address
                                   information for existing nodes on the
                                   Kademlia network, in the format:
                                   C{(<ip address>, (udp port>)}
        @type knownNodeAddresses: tuple
        
        @return: Deferred, will call-back once join has completed
        @rtype: twisted.internet.defer.Deferred
        """
        def addContact(responseTuple):
            """ adds a contact once it has responded to the remote procedure call """
            responseMsg = responseTuple[0]
            originatingAddress = responseTuple[1]
            
            contactID = responseTuple[0].nodeID
            #print 'id ' + str((responseMsg.nodeID,))
            #print 'response ' + str(responseMsg.response)            
            #print 'address ' + str(originatingAddress)
            
            if contactID != None:
                activeContact = Contact(contactID, originatingAddress[0], originatingAddress[1], self._protocol)
                self.contactsList.append(activeContact)
                
                
                                
                # Check for an errorMessage in the responseMsg
                if isinstance(responseMsg, ErrorMessage):
                    self._joinDeferred.errback(failure.Failure(Exception('Error response from RPC call: ' + str(responseMsg.response))))
                    #print 'Error response from RPC call: ' + str(responseMsg.response)
                else:
                    # Check if any tuples were returned by this contact
                    response = responseMsg.response
                    if isinstance(response, list):
                        # obtain the tuples and their owner ID's
                        for item in response:
                            # Place this item into the local data store
                            ownerID = item[0]
                            tupleValue = item[1]
                            self.put(tupleValue, ownerID)
                            
#                        print 'received tuples'
#                        print response
#                        
#                        localTuples = self.getAllTuples()
#                        print 'locally stored tuples'
#                        for tuple in localTuples:
#                            print str(tuple)
                    else:
                        self._joinDeferred.errback(failure.Failure(Exception('RPC response from contact invalid, expected a list')))
                        
                # Check if all the contacts have been reached
                if len(self.contactsList) == len(knownNodeAddresses):
                    # invoke joinDeferred callback to signal that join has completed
                    self._joinDeferred.callback(self.contactsList)
        
        def checkInitStatus(error): 
            """ Invoked when RPC attempt to contact fails
                @type failure: twisted.python.failure.Failure 
            """
            error.trap(protocol.TimeoutError)
            deadContactID = error.getErrorMessage()
            
            # TODO: Log this error
            #print 'Error, communication with contact failed!'
            
            # Remove this contact from the tentativeContacts list
            badContacts = []
            for cont in tentativeContacts:
                if cont.id == deadContactID:
                    badContacts.append(cont)
            for cont in badContacts:
                # TODO: log this error
                #print 'dead contact removed!' 
                tentativeContacts.remove(cont)
          
            # Check if all the other contacts have responded (Thus join completed)
            if (len(self.contactsList) > 0) and  \
                (len(self.contactsList) == (len(knownNodeAddresses) - (len(knownNodeAddresses) - len(tentativeContacts)))):
                # invoke joinDeferred errback to signal that join did not complete successfully
                self._joinDeferred.errback(failure.Failure(Exception('Not all contacts responded')))
            # Check if all of the contacts did not respond
            elif len(tentativeContacts) == 0:
                # invoke joinDeferred errback to signal that join did not complete successfully
                self._joinDeferred.errback(failure.Failure(Exception('None of the contacts could be reached')))
                # TODO: log this error
                
        # Prepare the underlying Kademlia protocol
        self._listeningPort = twisted.internet.reactor.listenUDP(self.port, self._protocol) #IGNORE:E1101
                   
        self._joinDeferred = defer.Deferred() 
        tentativeContacts = []
        
        # Create temporary contact information for the list of addresses of known nodes
        if knownNodeAddresses != None:
            bootstrapContacts = []
            for address, port in knownNodeAddresses:
                contact = Contact(self._generateID(), address, port, self._protocol)
                
                tentativeContacts.append(contact)
                                                
                # Check that the contact exists, and obtain its actual id and a list of all the tuples stored 
                # by this contact
                rpcMethod = getattr(contact, 'getOwnedTuples')
                df = rpcMethod(rawResponse=True)
                df.addCallback(addContact)
                df.addErrback(checkInitStatus)
        # if no known contacts, just call-back without trying to connect to peers
        else:
            self._joinDeferred.callback(None)
                                
                #self.contactsList.append(contact)
        
        # TODO: schedule a call to a statusCheckMethod which ensures that contacts are active
            
    def _iterativeFind(self, contactID):
        """ Used in Distributed Hash Table, still accessed by current mobilIVR system, thus just 
            here as a blank for interface purposes
        """
        emptyList = []
        return emptyList
    
    def addContact(self, contact):
        """ add a contact """
        
    def removeContact(self, contact):
        """ remove the contact """        
    
    def _generateID(self):
        """ Generates a 160-bit pseudo-random identifier
        
        @return: A globally unique 160-bit pseudo-random identifier
        @rtype: str
        """
        hash = hashlib.sha1()
        hash.update(str(random.getrandbits(255)))
        return hash.digest()
    
     

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print 'Usage:\n%s UDP_PORT  [KNOWN_NODE_IP  KNOWN_NODE_PORT]' % sys.argv[0]
        print 'or:\n%s UDP_PORT  [FILE_WITH_KNOWN_NODES]' % sys.argv[0]
        print '\nIf a file is specified, it should containg one IP address and UDP port\nper line, seperated by a space.'
        sys.exit(1)
    try:
        int(sys.argv[1])
    except ValueError:
        print '\nUDP_PORT must be an integer value.\n'
        print 'Usage:\n%s UDP_PORT  [KNOWN_NODE_IP  KNOWN_NODE_PORT]' % sys.argv[0]
        print 'or:\n%s UDP_PORT  [FILE_WITH_KNOWN_NODES]' % sys.argv[0]
        print '\nIf a file is specified, it should contain one IP address and UDP port\nper line, seperated by a space.'
        sys.exit(1)

    if len(sys.argv) == 4:
        knownNodes = [(sys.argv[2], int(sys.argv[3]))]
    elif len(sys.argv) == 3:
        knownNodes = []
        f = open(sys.argv[2], 'r')
        lines = f.readlines()
        f.close()
        for line in lines:
            ipAddress, udpPort = line.split()
            knownNodes.append((ipAddress, int(udpPort)))
    else:
        knownNodes = None

    node = DistributedTupleSpacePeer( udpPort=int(sys.argv[1]) )
    node.joinNetwork(knownNodes)
    twisted.internet.reactor.run()
    
