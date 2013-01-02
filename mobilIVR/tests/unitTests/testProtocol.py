#----------------------------------------------------------------------------#
#                                                                            #
#    Copyright (C) 2009 Department of Arts and Culture,                      #
#                       Republic of South Africa                             #
#    Contributer: Meraka Institute, CSIR                                     #
#    Author: Francois Aucamp                                                 #
#    Maintenance: Bryan Mcalister                                            #
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

Provides unit tests to test the Mobiled.network.rpc.protocol module
"""


#!/usr/bin/env python

import sys
sys.path.append('../../')

import time
import unittest

from twisted.internet import defer
from twisted.python import failure
import twisted.internet.selectreactor
from twisted.internet.protocol import DatagramProtocol

import network.rpc.protocol
import network.rpc.contact
import network.rpc.constants
import network.rpc.msgtypes
from network.staticTupleSpace import rpcmethod


class FakeNode(object):
    """ A fake node object implementing some RPC and non-RPC methods to 
    test the Kademlia protocol's behaviour
    """
    def __init__(self, id):
        self.id = id
        self.contacts = []
        
    @rpcmethod
    def ping(self):
        return 'pong'
    
    def pingNoRPC(self):
        return 'pong'
    
    @rpcmethod
    def echo(self, value):
        return value
    
    def addContact(self, contact):
        self.contacts.append(contact)
    
    def removeContact(self, contact):
        self.contacts.remove(contact)

    def indirectPingContact(self, protocol, contact):
        """ Pings the given contact (using the specified KademliaProtocol
        object, not the direct Contact API), and removes the contact
        on a timeout """
        df = protocol.sendRPC(contact, 'ping', {})
        def handleError(f):
            if f.check(network.rpc.protocol.TimeoutError):
                self.removeContact(contact)
                return f
            else:
                # This is some other error
                return f
        df.addErrback(handleError)
        return df

class ProtocolTest(unittest.TestCase):
    """ Test case for the Protocol class """
    def setUp(self):
        del network.rpc.protocol.reactor
        network.rpc.protocol.reactor = twisted.internet.selectreactor.SelectReactor()
        self.node = FakeNode('node1')
        self.protocol = network.rpc.protocol.KademliaProtocol(self.node)

    def testReactor(self):
        """ Tests if the reactor can start/stop the protocol correctly """
        network.rpc.protocol.reactor.listenUDP(0, self.protocol)
        network.rpc.protocol.reactor.callLater(0, network.rpc.protocol.reactor.stop)
        network.rpc.protocol.reactor.run()

    def testRPCTimeout(self):
        """ Tests if a RPC message sent to a dead remote node times out correctly """
        deadContact = network.rpc.contact.Contact('node2', '127.0.0.1', 91825, self.protocol)
        self.node.addContact(deadContact)
        # Make sure the contact was added
        self.failIf(deadContact not in self.node.contacts, 'Contact not added to fake node (error in test code)')
        # Set the timeout to 0 for testing
        tempTimeout = network.rpc.constants.rpcTimeout
        network.rpc.constants.rpcTimeout = 0
        network.rpc.protocol.reactor.listenUDP(0, self.protocol)            
        # Run the PING RPC (which should timeout)
        df = self.node.indirectPingContact(self.protocol, deadContact)
        # Stop the reactor if a result arrives (timeout or not)
        df.addBoth(lambda _: network.rpc.protocol.reactor.stop())
        network.rpc.protocol.reactor.run()
        # See if the contact was removed due to the timeout
        self.failIf(deadContact in self.node.contacts, 'Contact was not removed after RPC timeout; check exception types.')
        # Restore the global timeout
        network.rpc.constants.rpcTimeout = tempTimeout
        
    def testRPCRequest(self):
        """ Tests if a valid RPC request is executed and responded to correctly """
        remoteContact = network.rpc.contact.Contact('node2', '127.0.0.1', 91825, self.protocol)
        self.node.addContact(remoteContact)
        self.error = None
        def handleError(f):
            self.error = 'An RPC error occurred: %s' % f.getErrorMessage()
        def handleResult(result):
            expectedResult = 'pong'
            if result != expectedResult:
                self.error = 'Result from RPC is incorrect; expected "%s", got "%s"' % (expectedResult, result)
        # Publish the "local" node on the network    
        network.rpc.protocol.reactor.listenUDP(91825, self.protocol)
        # Simulate the RPC
        df = remoteContact.ping()
        df.addCallback(handleResult)
        df.addErrback(handleError)
        df.addBoth(lambda _: network.rpc.protocol.reactor.stop())
        network.rpc.protocol.reactor.run()
        self.failIf(self.error, self.error)
        # The list of sent RPC messages should be empty at this stage
        self.failUnlessEqual(len(self.protocol._sentMessages), 0, 'The protocol is still waiting for a RPC result, but the transaction is already done!')

    def testRPCAccess(self):
        """ Tests invalid RPC requests
        
        Verifies that a RPC request for an existing but unpublished
        method is denied, and that the associated (remote) exception gets
        raised locally """
        remoteContact = network.rpc.contact.Contact('node2', '127.0.0.1', 91825, self.protocol)
        self.node.addContact(remoteContact)
        self.error = None
        def handleError(f):
            try:
                f.raiseException()
            except AttributeError, e:
                # This is the expected outcome since the remote node did not publish the method
                self.error = None
            except Exception, e:
                self.error = 'The remote method failed, but the wrong exception was raised; expected AttributeError, got %s' % type(e)
                
        def handleResult(result):
            self.error = 'The remote method executed successfully, returning: "%s"; this RPC should not have been allowed.' % result
        # Publish the "local" node on the network    
        network.rpc.protocol.reactor.listenUDP(91825, self.protocol)
        # Simulate the RPC
        df = remoteContact.pingNoRPC()
        df.addCallback(handleResult)
        df.addErrback(handleError)
        df.addBoth(lambda _: network.rpc.protocol.reactor.stop())
        network.rpc.protocol.reactor.run()
        self.failIf(self.error, self.error)
        # The list of sent RPC messages should be empty at this stage
        self.failUnlessEqual(len(self.protocol._sentMessages), 0, 'The protocol is still waiting for a RPC result, but the transaction is already done!')

    def testRPCRequestArgs(self):
        """ Tests if an RPC requiring arguments is executed correctly """
        remoteContact = network.rpc.contact.Contact('node2', '127.0.0.1', 91825, self.protocol)
        self.node.addContact(remoteContact)
        self.error = None
        def handleError(f):
            self.error = 'An RPC error occurred: %s' % f.getErrorMessage()
        def handleResult(result):
            expectedResult = 'This should be returned.'
            if result != 'This should be returned.':
                self.error = 'Result from RPC is incorrect; expected "%s", got "%s"' % (expectedResult, result)
        # Publish the "local" node on the network    
        network.rpc.protocol.reactor.listenUDP(91825, self.protocol)
        # Simulate the RPC
        df = remoteContact.echo('This should be returned.')
        df.addCallback(handleResult)
        df.addErrback(handleError)
        df.addBoth(lambda _: network.rpc.protocol.reactor.stop())
        network.rpc.protocol.reactor.run()
        self.failIf(self.error, self.error)
        # The list of sent RPC messages should be empty at this stage
        self.failUnlessEqual(len(self.protocol._sentMessages), 0, 'The protocol is still waiting for a RPC result, but the transaction is already done!')

    def testDatagramLargeMessageReconstruction(self):
        """ Tests if a large amount of data can be successfully re-constructed from multiple UDP datagrams """
        remoteContact = network.rpc.contact.Contact('node2', '127.0.0.1', 91825, self.protocol)
        self.node.addContact(remoteContact)
        self.error = None
        #responseData = 8143 * '0' # Threshold for a single packet transmission
        responseData = 300000 * '0'
        def handleError(f):
            if f.check((network.rpc.protocol.TimeoutError)):
                self.error = 'RPC from the following contact timed out: %s' % f.getErrorMessage()
            else:
                self.error = 'An RPC error occurred: %s' % f.getErrorMessage()
        def handleResult(result):
            if result != responseData:
                self.error = 'Result from RPC is incorrect; expected "%s", got "%s"' % (responseData, result)
        # Publish the "local" node on the network    
        network.rpc.protocol.reactor.listenUDP(91825, self.protocol)
        # ...and make it think it is waiting for a result from an RPC
        msgID = 'abcdefghij1234567890'
        df = defer.Deferred()
        timeoutCall = network.rpc.protocol.reactor.callLater(network.rpc.constants.rpcTimeout, self.protocol._msgTimeout, msgID)
        self.protocol._sentMessages[msgID] = (remoteContact.id, df, timeoutCall)
        # Simulate the "reply" transmission
        msg = network.rpc.msgtypes.ResponseMessage(msgID, 'node2', responseData)
        msgPrimitive = self.protocol._translator.toPrimitive(msg)
        encodedMsg = self.protocol._encoder.encode(msgPrimitive)
        udpClient = ClientDatagramProtocol()
        udpClient.data = encodedMsg
        udpClient.msgID = msgID
        network.rpc.protocol.reactor.listenUDP(0, udpClient)
        df.addCallback(handleResult)
        df.addErrback(handleError)
        df.addBoth(lambda _: network.rpc.protocol.reactor.stop())
        network.rpc.protocol.reactor.run()
        self.failIf(self.error, self.error)
        # The list of sent RPC messages should be empty at this stage
        #self.failUnlessEqual(len(self.protocol._sentMessages), 0, 'The protocol is still waiting for a RPC result, but the transaction is already done!')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ProtocolTest))
    return suite

if __name__ == '__main__':
    # If this module is executed from the commandline, run all its tests
    unittest.TextTestRunner().run(suite())