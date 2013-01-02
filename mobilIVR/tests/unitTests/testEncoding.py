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

Provides unit tests to test the Mobiled.network.rpc.encoding module
"""


#!/usr/bin/env python

import unittest

import entangled.kademlia.encoding

class BencodeTest(unittest.TestCase):
    """ Basic tests case for the Bencode implementation """
    def setUp(self):
        self.encoding = entangled.kademlia.encoding.Bencode()
        # Thanks goes to wikipedia for the initial test cases ;-)
        self.cases = ((42, 'i42e'),
                      ('spam', '4:spam'),
                      (['spam',42], 'l4:spami42ee'),
                      ({'foo':42, 'bar':'spam'}, 'd3:bar4:spam3:fooi42ee'),
                      # ...and now the "real life" tests
                      ([['abc', '127.0.0.1', 1919], ['def', '127.0.0.1', 1921]], 'll3:abc9:127.0.0.1i1919eel3:def9:127.0.0.1i1921eee'))
        # The following test cases are "bad"; i.e. sending rubbish into the decoder to test what exceptions get thrown
        self.badDecoderCases = ('abcdefghijklmnopqrstuvwxyz',
                                '')                        
                      
    def testEncoder(self):
        """ Tests the bencode encoder """
        for value, encodedValue in self.cases:
            result = self.encoding.encode(value)
            self.failUnlessEqual(result, encodedValue, 'Value "%s" not correctly encoded! Expected "%s", got "%s"' % (value, encodedValue, result))
        
    def testDecoder(self):
        """ Tests the bencode decoder """
        for value, encodedValue in self.cases:
            result = self.encoding.decode(encodedValue)
            self.failUnlessEqual(result, value, 'Value "%s" not correctly decoded! Expected "%s", got "%s"' % (encodedValue, value, result))
        for encodedValue in self.badDecoderCases:
            self.failUnlessRaises(entangled.kademlia.encoding.DecodeError, self.encoding.decode, encodedValue)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BencodeTest))
    return suite

if __name__ == '__main__':
    # If this module is executed from the commandline, run all its tests
    unittest.TextTestRunner().run(suite())
