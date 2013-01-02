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

Provides a basic interface for resource implementations, providing mechanisms
for finding and setting up these resources
"""

class Resource(object):
    """ Basic interface for resource implementations, providing mechanisms
    for finding and setting up these resources """
    def __init__(self, node):
        """
        @param node: The MobilIVRNode instance that is executing this application;
                     this provides a mechanism for accessing resources, publishing
                     events, acessing the P2P overlay network, etc
        @type node: mobilIVR.MobilIVRNode
        """
    
    def __del__(self):
        """ Make sure resources are released when this object is destroyed """
        self.releaseResource()

    def getResource(self):
        """ Find and retrieve an instance of this resource; blocking operation """
    
    def getResourceIfExists(self):
        """ Find and retrieve an instance of this resource; non-blocking operation """
    
    def releaseResource(self):
        """ Release this resource (call this when done with it) """
