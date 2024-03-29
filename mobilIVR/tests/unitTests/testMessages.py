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

Provides unit tests to test the Mobiled.network.rpc.msgtypes and Mobiled.network.rpc.msgformat modules
"""

#!/usr/bin/env python


import unittest

from entangled.kademlia.msgtypes import Message, RequestMessage, ResponseMessage, ErrorMessage
from entangled.kademlia.msgformat import MessageTranslator, DefaultFormat

class DefaultFormatTranslatorTest(unittest.TestCase):
    """ Test case for the default message translator """
    def setUp(self):
        self.cases = ((RequestMessage('node1', 'rpcMethod', {'arg1': 'a string', 'arg2': 123}, 'rpc1'),
                       {DefaultFormat.headerType: DefaultFormat.typeRequest,
                        DefaultFormat.headerNodeID: 'node1',
                        DefaultFormat.headerMsgID: 'rpc1',
                        DefaultFormat.headerPayload: 'rpcMethod',
                        DefaultFormat.headerArgs: {'arg1': 'a string', 'arg2': 123}}),
                        
                      (ResponseMessage('rpc2', 'node2', 'response'),
                       {DefaultFormat.headerType: DefaultFormat.typeResponse,
                        DefaultFormat.headerNodeID: 'node2',
                        DefaultFormat.headerMsgID: 'rpc2',
                        DefaultFormat.headerPayload: 'response'}),
                        
                      (ErrorMessage('rpc3', 'node3', "<type 'exceptions.ValueError'>", 'this is a test exception'),
                       {DefaultFormat.headerType: DefaultFormat.typeError,
                        DefaultFormat.headerNodeID: 'node3',
                        DefaultFormat.headerMsgID: 'rpc3',
                        DefaultFormat.headerPayload: "<type 'exceptions.ValueError'>",
                        DefaultFormat.headerArgs: 'this is a test exception'}),
                      
                      (ResponseMessage('rpc4', 'node4', [('H\x89\xb0\xf4\xc9\xe6\xc5`H>\xd5\xc2\xc5\xe8Od\xf1\xca\xfa\x82', '127.0.0.1', 1919), ('\xae\x9ey\x93\xdd\xeb\xf1^\xff\xc5\x0f\xf8\xac!\x0e\x03\x9fY@{', '127.0.0.1', 1921)]),
                       {DefaultFormat.headerType: DefaultFormat.typeResponse,
                        DefaultFormat.headerNodeID: 'node4',
                        DefaultFormat.headerMsgID: 'rpc4',
                        DefaultFormat.headerPayload: [('H\x89\xb0\xf4\xc9\xe6\xc5`H>\xd5\xc2\xc5\xe8Od\xf1\xca\xfa\x82', '127.0.0.1', 1919), ('\xae\x9ey\x93\xdd\xeb\xf1^\xff\xc5\x0f\xf8\xac!\x0e\x03\x9fY@{', '127.0.0.1', 1921)]})
                      )
        self.translator = DefaultFormat()
        self.failUnless(isinstance(self.translator, MessageTranslator), 'Translator class must inherit from entangled.kademlia.msgformat.MessageTranslator!')

    def testToPrimitive(self):
        """ Tests translation from a Message object to a primitive """
        for msg, msgPrimitive in self.cases:
            translatedObj = self.translator.toPrimitive(msg)
            self.failUnlessEqual(len(translatedObj), len(msgPrimitive), "Translated object does not match example object's size")
            for key in msgPrimitive:
                self.failUnlessEqual(translatedObj[key], msgPrimitive[key], 'Message object type %s not translated correctly into primitive on key "%s"; expected "%s", got "%s"' % (msg.__class__.__name__, key, msgPrimitive[key], translatedObj[key]))
            
    def testFromPrimitive(self):
        """ Tests translation from a primitive to a Message object """
        for msg, msgPrimitive in self.cases:
            translatedObj = self.translator.fromPrimitive(msgPrimitive)
            self.failUnlessEqual(type(translatedObj), type(msg), 'Message type incorrectly translated; expected "%s", got "%s"' % (type(msg), type(translatedObj))) 
            for key in msg.__dict__:
                self.failUnlessEqual(msg.__dict__[key], translatedObj.__dict__[key], 'Message instance variable "%s" not translated correctly; expected "%s", got "%s"' % (key, msg.__dict__[key], translatedObj.__dict__[key]))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DefaultFormatTranslatorTest))
    return suite

if __name__ == '__main__':
    # If this module is executed from the commandline, run all its tests
    unittest.TextTestRunner().run(suite())
