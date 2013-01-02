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

Provides a class that encapsulates a remote contact
"""

#!/usr/bin/env python

class Contact(object):
    """ Encapsulation for remote contact
    
    This class contains information on a single remote contact, and also
    provides a direct RPC API to the remote node which it represents
    """
    def __init__(self, id, ipAddress, udpPort, networkProtocol, firstComm=0):
        self.id = id
        self.address = ipAddress
        self.port = udpPort
        self._networkProtocol = networkProtocol
        self.commTime = firstComm
        
    def __eq__(self, other):
        if isinstance(other, Contact):
            return self.id == other.id
        elif isinstance(other, str):
            return self.id == other
        else:
            return False
    
    def __ne__(self, other):
        if isinstance(other, Contact):
            return self.id != other.id
        elif isinstance(other, str):
            return self.id != other
        else:
            return True
        
    def __str__(self):
        return '<%s.%s object; IP address: %s, UDP port: %d>' % (self.__module__, self.__class__.__name__, self.address, self.port)
    
    def __getattr__(self, name):
        """ This override allows the host node to call a method of the remote
        node (i.e. this contact) as if it was a local function.
        
        For instance, if C{remoteNode} is a instance of C{Contact}, the
        following will result in C{remoteNode}'s C{test()} method to be
        called with argument C{123}::
         remoteNode.test(123)
        
        Such a RPC method call will return a Deferred, which will callback
        when the contact responds with the result (or an error occurs).
        This happens via this contact's C{_networkProtocol} object (i.e. the
        host Node's C{_protocol} object).
        """
        def _sendRPC(*args, **kwargs):
            return self._networkProtocol.sendRPC(self, name, args, **kwargs)
        return _sendRPC
