#----------------------------------------------------------------------------#
#                                                                            #
#    Copyright (C) 2009 Department of Arts and Culture,                      #
#                       Republic of South Africa                             #
#    Contributer: Meraka Institute, CSIR                                     #
#    Author: Francois Aucamp                                                 #
#    Maintenance: Bryan McAlister
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

Provides modules for low level RPC messaging
"""

#!/usr/bin/env python

import hashlib
import random

class Message(object):
    """ Base class for messages - all "unknown" messages use this class """
    def __init__(self, rpcID, nodeID):
        self.id = rpcID
        self.nodeID = nodeID


class RequestMessage(Message):
    """ Message containing an RPC request """
    def __init__(self, nodeID, method, methodArgs, rpcID=None):
        if rpcID == None:
            hash = hashlib.sha1()
            hash.update(str(random.getrandbits(255)))  
            rpcID = hash.digest()
        Message.__init__(self, rpcID, nodeID)
        self.request = method
        self.args = methodArgs


class ResponseMessage(Message):
    """ Message containing the result from a successful RPC request """
    def __init__(self, rpcID, nodeID, response):
        Message.__init__(self, rpcID, nodeID)
        self.response = response


class ErrorMessage(ResponseMessage):
    """ Message containing the error from an unsuccessful RPC request """
    def __init__(self, rpcID, nodeID, exceptionType, errorMessage):
        ResponseMessage.__init__(self, rpcID, nodeID, errorMessage)
        if isinstance(exceptionType, type):
            self.exceptionType = '%s.%s' % (exceptionType.__module__, exceptionType.__name__)
        else:
            self.exceptionType = exceptionType
