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

Wrapper script to run all included test scripts
"""

#!/usr/bin/env python

import os, sys
import unittest

def runTests():
    testRunner = unittest.TextTestRunner()
    testRunner.run(additional_tests())

def additional_tests():
    """ Used directly by setuptools to run unittests """
    sys.path.insert(0, os.path.dirname(__file__))
    suite = unittest.TestSuite()
    tests = os.listdir(os.path.dirname(__file__))
    tests = [n[:-3] for n in tests if n.startswith('test') and n.endswith('.py')]
    for test in tests:
        m = __import__(test)
        if hasattr(m, 'suite'):
            suite.addTest(m.suite())
    sys.path.pop(0)
    return suite

    
if __name__ == '__main__':
    # Add parent folder to sys path so it's easier to use
    sys.path.insert(0,os.path.abspath('..'))
    runTests()
