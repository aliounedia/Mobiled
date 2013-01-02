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

Provides unit tests to test the Mobiled.network.rpc.contact module
"""

#!/usr/bin/env python

import unittest

import entangled.kademlia.contact

class ContactOperatorsTest(unittest.TestCase):
    """ Basic tests case for boolean operators on the Contact class """
    def setUp(self):
        self.firstContact = entangled.kademlia.contact.Contact('firstContactID', '127.0.0.1', 1000, None, 1)
        self.secondContact = entangled.kademlia.contact.Contact('2ndContactID', '192.168.0.1', 1000, None, 32)
        self.secondContactCopy = entangled.kademlia.contact.Contact('2ndContactID', '192.168.0.1', 1000, None, 32)
        self.firstContactDifferentValues = entangled.kademlia.contact.Contact('firstContactID', '192.168.1.20', 1000, None, 50)

    def testBoolean(self):
        """ Test "equals" and "not equals" comparisons """
        self.failIfEqual(self.firstContact, self.secondContact, 'Contacts with different IDs should not be equal.')
        self.failUnlessEqual(self.firstContact, self.firstContactDifferentValues, 'Contacts with same IDs should be equal, even if their other values differ.')
        self.failUnlessEqual(self.secondContact, self.secondContactCopy, 'Different copies of the same Contact instance should be equal')

    def testStringComparisons(self):
        """ Test comparisons of Contact objects with str types """
        self.failUnlessEqual('firstContactID', self.firstContact, 'The node ID string must be equal to the contact object')
        self.failIfEqual('some random string', self.firstContact, "The tested string should not be equal to the contact object (not equal to it's ID)")

    def testIllogicalComparisons(self):
        """ Test comparisons with non-Contact and non-str types """
        for item in (123, [1,2,3], {'key': 'value'}):
            self.failIfEqual(self.firstContact, item, '"eq" operator: Contact object should not be equal to %s type' % type(item).__name__)
            self.failUnless(self.firstContact != item, '"ne" operator: Contact object should not be equal to %s type' % type(item).__name__)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ContactOperatorsTest))
    return suite

if __name__ == '__main__':
    # If this module is executed from the commandline, run all its tests
    unittest.TextTestRunner().run(suite())
