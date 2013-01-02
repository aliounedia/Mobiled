#!/usr/bin/env python

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
@author: Bryan McAlister <bmcalister@csir.co.za>, 
    
Provides an incoming call IVR handler
"""

import time
import random
import twisted.internet.reactor
import traceback

import mobilIVR.application
from mobilIVR.utils.Session import setupNode, cleanup

from mobilIVR.ivr.dialogScripting.dialog import Dialog, DialogError

class IncomingCallHandlerError(Exception):
    """ Raised if an error occurs during initialisation of an incoming call
    """

class IncomingCallHandler:
    """ Acts as a dispatcher. Takes a Dialog Class as input, which is instatiated into an object by the IVRHandler class 
        when an incoming call is received. The dialog is executed via its run 
        method, which receives a mobilIVR.ivr.fastagi.IVRInterface parameter for call interaction.
    """
    def __init__(self, dialogClass=None):
        """ Takes a Dialog Class and passes it to a mobilIVR.node for eventual use by an IVRHandler class once an incoming 
            call is received. 
            @param dialogClass: A class that has a run method with one parameter to receive a 
            mobilIVR.ivr.fastagi.IVRInterface for call interaction.
            @raises IncomingCallHandlerException: If the dialog class doesn't have a run method
        """
        
        if hasattr(dialogClass, "run"):
            self._dialogClass = dialogClass
            node = setupNode()
            node.runApplication(IVRHandler, [self._dialogClass])
            twisted.internet.reactor.run()
            cleanup()
        else:
            raise IncomingCallHandlerError("dialog class doesn't have a run method")

class IVRHandler(mobilIVR.application.IVRHandler):
    """
    IVR handler class, created every time an incoming call is received. It takes a Dialog Class as input, which it 
    instantiates into an object. It runs the Dialog object by calling it's run method, and passes it an 
    mobilIVR.ivr.fastagi.IVRInterface for call interaction.
    """
    
    def __init__(self, args):
        """
        IVRhandler constructor.
        @param args: A list containing a Dialog class as the first element
        @type args: list
        """
        self._id = None
        self._dialog = None
        self.DialogClass = args[0]
            
    def handleIVR(self, ivr, node):
        """
        IVR call handler, invoked by a MobilIVRNode when an incoming call is received.
            
        @param ivr: Asterisk call interaction interface
        @type ivr: mobilIVR.ivr.fastagi.IVRInterface
        @param node: MobilIVR resource node
        @type node: mobilIVR.node.MobilIVRNode
        """
        try:
            # get the calls unique id
            self._id = ivr.getVariable("UNIQUEID")
            self._ivr = ivr
            self._dialog = self.DialogClass(self._ivr)
            
            node._log.info('Answering call from Asterisk...')
            self._ivr.answer()
                              
            self._dialog.run()
            
        except DialogError, e:
            traceback.print_exc()
            node._log.error(e.message)
            
        except Exception, e:
            traceback.print_exc()
            node._log.error(e)

        finally:
            try:
                self._ivr.hangup()
            except Exception, e:
                pass
            # force cleanup of the dialog instance
            self._dialog.__del__()
            node._log.info('Call completed.')
            self._id = None


if __name__ == '__main__':
    node = setupNode()
    node.runApplication(AutosecIVR)
    twisted.internet.reactor.run()
    cleanup()

