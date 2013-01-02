#----------------------------------------------------------------------------#
#                                                                            #
#    Copyright (C) 2008 Department of Arts and Culture,                      #
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

Provides unit tests for the StaticTupleSpace
"""

#!/usr/bin/env python

import hashlib
import cPickle
import unittest

import sys
sys.path.append('../../')
from network.staticTupleSpace import StaticTupleSpacePeer
from network.rpc.msgtypes import ResponseMessage
from network.rpc.contact import Contact
from twisted.internet import protocol, defer, selectreactor


class TuplePublishingAndLookupTest(unittest.TestCase):           
    """ This test suite tests the publishing and lookup of tuples with a StaticTupleSpacePeer 
    """
    def testPut(self):
        node = StaticTupleSpacePeer()
        inputData = ('resource','ivr',node.id)
        parsedInput = (inputData[0], inputData[1])
        serializedInput = cPickle.dumps(parsedInput)
        
            
        # Attempt to publish the data tuple
        node.put(inputData)
        
        # Check that the data is in the data store
        h = hashlib.sha1()
        h.update(serializedInput)
        mainKey = h.digest()
        
                
        dataStoreTuple = node.dataStore.__getitem__(mainKey)
        ownerID = node.dataStore.originalPublisherID(mainKey)
        
        self.failUnlessEqual(serializedInput, dataStoreTuple, "Input data not equal to the data found in the dataStore")
        self.failUnlessEqual(ownerID, node.id, "Input owner ID not equal to the owner ID found in the dataStore")
        
        
    def testFindTuple(self):
        node = StaticTupleSpacePeer()
        inputData = ('resource','ivr',node.id)
        
        # Attempt to publish the data tuple
        node.put(inputData)
        
        # Attempt to find the data
        returnedTuple = node.findTuple(('resource', 'ivr'))
        
        # check that the expected result was returned
        expectedResult = ('resource', 'ivr', node.id)
        self.failUnlessEqual(returnedTuple, expectedResult, "Tuple returned from findTuple not the same as the expected result")
                
        
    def testGetOwnedTuples(self):
        node = StaticTupleSpacePeer()
        inputData = [('ownresource1','ivr',node.id),
                     ('ownresource2','ivr',node.id),
                     ('otherResource1','ivr','otherid123456')]
        
        expectedResult = []
        
        # Attempt to publish the data tuple
        for item in inputData:
            node.put(item)
        
                
        
        returnedTuples = node.getOwnedTuples()
        
        # check that the expected result was returned
        # construct the expected result
        
        for i in range(2):
            parsedStr = (inputData[i][0], inputData[i][1])
            serializedStr = cPickle.dumps(parsedStr)
            
            expectedResult.append([node.id, serializedStr])
        expectedResult.reverse()
        
        
        # Only tuples owned by this node (has this nodes id) should be returned
        self.failUnlessEqual(returnedTuples, expectedResult, "Tuples returned from getOwnedTuples not the same as the expected result."   \
                        " Only tuples owned by this node (has this nodes id) should be returned")
        
    def testGetAllTuples(self):
        node = StaticTupleSpacePeer()
        inputData = [('ownresource1','ivr',node.id),
                     ('otherResource1','ivr','otherid123456')]
        
        expectedResult = []
        
        # Attempt to publish the data tuple
        for item in inputData:
            node.put(item)
               
        returnedTuples = node.getAllTuples()
        
        # check that the expected result was returned
        # construct the expected result
        
        for i in range(2):
            parsedStr = (inputData[i][0], inputData[i][1])
            serializedStr = cPickle.dumps(parsedStr)
            
            expectedResult.append([inputData[i][2], serializedStr])
                
              
        # All tuples should be returned, regardless of owner id
        self.failUnlessEqual(returnedTuples, expectedResult, "Tuples returned from getOwnedTuples not the same as the expected result."   \
                        " All tuples should be returned, regardless of owner id")
        
#    def testFindContact(self):

#    def joinNetwork(self):



""" Some scaffolding for the NetworkCreation class."""

class FakeRPCProtocol(protocol.DatagramProtocol):
    def __init__(self):
        self.reactor = selectreactor.SelectReactor() 
        self.testResponse = None
        self.network = None
        self.dataStore = None
        
   
    def createNetwork(self, contactNetwork):
         """ set up a list of contacts together with their closest contacts
         @param contactNetwork: a sequence of tuples, each containing a contact together with its closest 
         contacts:  C{(<contact>, <closest contact 1, ...,closest contact n>)}
         """
         self.network = contactNetwork
         
    def createDataStore(self, _dataStore):
         self.dataStore = _dataStore
        
    """ Fake RPC protocol; allows entangled.kademlia.contact.Contact objects to "send" RPCs """
    def sendRPC(self, contact, method, args, rawResponse=False):
        #print method + " " + str(args)
        
        if method == "getOwnedTuples":        
            # Determine which contact this is by using the address information
            for item in self.network:
                if ((item[1][0] == contact.address) and (item[1][1] == contact.port)):
                    actualID = item[0]
                    resources = []
                    # get the resources at this node
                    for dataItem in self.dataStore:
                        if actualID == dataItem[0]:
                            resources.append(dataItem)
                    
                    message = ResponseMessage("rpcId", actualID, resources)
                    
            df = defer.Deferred()
            df.callback((message,(contact.address, contact.port)))
            return df
      
    def _send(self, data, rpcID, address):
        """ fake sending data """
        
            

class NetworkCreationTest(unittest.TestCase):
    """ This test suite tests that a StaticTupleSpacePeer can contact its peers (know addresses) and 
        obtain the tuples(data) stored at those peers
    """
       
    def setUp(self):
                        
        # create a fake protocol to imitate communication with other nodes
        self._protocol = FakeRPCProtocol()
        
        # Note: The reactor is never started for this test. All deferred calls run sequentially, 
        # since there is no asynchronous network communication
        
        # create the node to be tested in isolation
        self.node = StaticTupleSpacePeer(networkProtocol=self._protocol)
        
        self.updPort = 81173
        
        
        # create a network with IP addresses, port numbers and the corresponding node ID
        self.network = [['nodeID1',('127.0.0.1', 12345)],['nodeID2',('146.24.1.1', 34567)], ['nodeID3',('147.22.1.16', 234566)]]
        self.dataStore = [['nodeID1', ('resource1','ivr1', 'nodeID1')], ['nodeID2', ('resource2','ivr2', 'nodeID2')],\
                           ['nodeID3', ('resource3','ivr3', 'nodeID3')]]
        self._protocol.createNetwork(self.network)
        self._protocol.createDataStore(self.dataStore)
        
    def testJoinNetwork(self):
        # get the known addresses from self.network
        knownAddresses = []
        for item in self.network:
            knownAddresses.append(item[1])
        
        # Attempt to join the network of known addresses
        self.node.joinNetwork(knownAddresses)
                       
        # Check that the contacts have been added to the nodes contactsList
        # construct the contacts used for testing
        expectedContactsList = []
        for item in self.network:
            cont = Contact(item[0], item[1][0], item[1][1], self._protocol)
            expectedContactsList.append(cont)
        
#        print 'expected list '
#        for conti in expectedContactsList:
#            print str(conti)
        
        actualContactsList = self.node.contactsList
        
#        print 'actual contacts list ' + str(actualContactsList)
#        for conti in actualContactsList:
#            print str(conti)
        
        # Check that the expected contacts list are the same as the actual contacts list populated during the join sequence
        self.failUnlessEqual(expectedContactsList, actualContactsList, \
                                 "Contacts List populated by peer during join sequence doesn't contain the expected contacts")
        
        
        # Check that the dataStore has been populated 
        for item in self.dataStore:
            expectedTuple = item[1]
            #print 'searching for: ' + str(item[1])
            returnedTuple = self.node.get(expectedTuple)
            #print 'returned Tuple ' + str(returnedTuple)
            
            # Check that the returnedTuple is the same as the expected tuple
            self.failUnlessEqual(expectedTuple[1], returnedTuple[1], \
                                 "The data store was not populated correctly, expected tuple to be stored")
        
        
    
                      

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TuplePublishingAndLookupTest))
    suite.addTest(unittest.makeSuite(NetworkCreationTest))
    return suite

if __name__ == '__main__':
    # If this module is executed from the commandline, run all its tests
    unittest.TextTestRunner().run(suite())
