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
Provides a call-back communication model.

@author: Bryan McAlister <bmcalister@csir.co.za>, 
"""
import os
import twisted.internet.reactor
from time import sleep, time

import mobilIVR.application
from mobilIVR.ivr import IVRDialer
from mobilIVR.utils.Session import setupNode, cleanup
from mobilIVR.ivr.dialogScripting.dialog import Dialog, DialogError

class CallBackHandlerError(Exception):
    """ Raised if an error occurs during initialisation of an CallBackHandler
    """

class CallBackHandler:
    """ Acts as a dispatcher. Takes a Dialog Class as input, which is instatiated into an object by the   
        IncomingCallerIDQueue class, when making an outgoing call to a queued caller-ID. The dialog is executed via  
        its run method, which receives a mobilIVR.ivr.fastagi.IVRInterface parameter for call interaction.
    """
    def __init__(self, dialogClass=None):
        """ Takes a Dialog Class and passes it to a mobilIVR.node, for eventual use by an IncomingCallerIDQueue class when 
            making outgoing calls to a queued caller-ID. 
            @param dialogClass: A class that has a run method with one parameter to receive a 
            mobilIVR.ivr.fastagi.IVRInterface for call interaction.
            @raises CallBackHandlerError: If the dialog class doesn't have a run method
        """
        
        if hasattr(dialogClass, "run"):
            self._dialogClass = dialogClass
            node = setupNode()
            node.runApplication(IncomingCallerIDQueue(self._dialogClass))
            twisted.internet.reactor.run()
            cleanup()
        else:
            raise CallBackHandlerError("dialog class doesn't have a run method")


class IncomingCallerIDQueue(mobilIVR.application.IVRHandler, mobilIVR.application.Application):
    """
    Takes incoming calls, captures the caller-id and places it into a queue without answering the call. Queued caller-id's are popped by a call-back thread responsible for doing an outgoing call to the caller-id and running a dialog to service the call.
    """
    
    def __init__(self, _dialogClass):
        """
        IVR constructor.
        """
        
        self.DialogClass = _dialogClass
         
        self._callerIDQueue = {}
        
        self._serviceQueue = True
        
        # service Wait time defines how long to wait before servicing a call request
        # This gives enough time for the user to hang-up after making a missed call, and
        # to wait for the call-back
        self.serviceWaitTime = 10 # seconds
    
     
    def handleIVR(self, ivr, node):
        """
        Incoming call handler used for making call-back requests. Once an incoming call is received, the 
        caller-ID is queued. The queue is serviced by a separate thread which invokes outgoing calls to the queued caller-IDs. See IncomingCallerIDQueue.run method for details.
            
        @param ivr: Asterisk interface
        @type ivr: mobilIVR.ivr.fastagi.IVRInterface
        @param node: MobilIVR resource node
        @type node: mobilIVR.node.MobilIVRNode
        """
        try:
            # indicate a ringing tone to the caller
            uniqueID = ivr.getVariable("UNIQUEID")
            
            #ivr.callerID = uniqueID
            
            node._log.info('Got call-back request from Caller ID: ' + str(ivr.callerID))
                                   
            # Add this caller-ID to the queue
            if ivr.callerID != None:
                # queue the call based on its unique id and the time of the request
                self._callerIDQueue[uniqueID] = (ivr.callerID, time(), ivr.dialedNumber)
                node._log.info('Call received on %s ' % (ivr.dialedNumber))
                node._log.info('Queued call-back request from Caller ID: ' + str(ivr.callerID))
                node._log.info('Queue Length ' + str(len(self._callerIDQueue)))

            # indicate a ringing tone to the caller
            ivr.execute('Ringing')
            ivr.execute('Wait 1')

        except Exception, e:
            node._log.error(e)

        finally:
            try:
                ivr.hangup()
            except Exception, e:
                pass

    def run(self, node):
        """
           Call-back thread: Run is invoked as soon as the node is started (by mobilIVR.node). In this case it is used to service the call queue by creating outgoing calls to the queued caller-IDs. Queued caller-ids are only 
           serviced if they have been in the queue for a duration longer than C{self.serviceWaitTime}. 
           
           @param node: MobilIVR resource node
           @type node: mobilIVR.node.MobilIVRNode
        """
        while self._serviceQueue:
            
            if (len(self._callerIDQueue) > 0):
                
                # remove duplicate/multiple queued requests from same caller-id
                self._removeDuplicateQueuedCallerIDs()
                
                uniqueIDs = self._callerIDQueue.keys()
                # node._log.info("Queue length " + str(len(uniqueIDs)))
                for uniqueID in uniqueIDs:
                    callerID = str(self._callerIDQueue[uniqueID][0])
                    timeStamp = self._callerIDQueue[uniqueID][1]
                    dialedNumber = str(self._callerIDQueue[uniqueID][2])
                    currentTime = time()
                    
                    if (currentTime - timeStamp > self.serviceWaitTime):
                        node._log.info("Servicing call to " + callerID)
                        try:
                            dialer = IVRDialer(node) # defined in mobilIVR.ivr.__init__
                            node._log.info('finding an available outgoing IVR resource')
                            # find an ivr resource - this is a blocking call handled by the node, returning the address/port of 
                            # an Asterisk Manager API server
                            dialer.getResource()
                            node._log.info('resource found, establishing call with ivr script')
                            # Creates/dials an outbound call, and returns an AGI IVR interface which we can use for interaction 
                            # with the end user
                            ivr = dialer.dial(callerID)
                            ivr.callerID = callerID
                            # set the dialedNumber to the one used to place the missed call
                            ivr.dialedNumber = dialedNumber
                            
                            # create and start the dialog to service the call
                            dialog = self.DialogClass(ivr)
                                                      
                            dialog.run()
                            # ...and hang up the call
                        except Exception, e:
                            node._log.error(e)
                        finally:
                            try:
                                ivr.hangup()
                            except Exception, e:
                                pass
                        
                        
                        node._log.info("Service completed for " + callerID)
                        # remove this request caller-id from the queue
                        del self._callerIDQueue[uniqueID]
            else:
                sleep(0.1)
    
    def _removeDuplicateQueuedCallerIDs(self):
        """ Removes duplicate queued callerIDs
        """
        uniqueIDs_i = self._callerIDQueue.keys()
        deletedUniqueIDs = []
        for uniqueID_i in uniqueIDs_i:
            multipleCount = 0
            if uniqueID_i not in deletedUniqueIDs:
               currentCallerID_i = self._callerIDQueue[uniqueID_i][0]
                
               # do a separate iteration to remove the duplicates
               uniqueIDs_j = self._callerIDQueue.keys()
               for uniqueID_j in uniqueIDs_j:
                   currentCallerID_j = self._callerIDQueue[uniqueID_j][0]
                   if (currentCallerID_j == currentCallerID_i):
                       multipleCount += 1
                       if multipleCount > 1:
                           del self._callerIDQueue[uniqueID_j]
                           deletedUniqueIDs.append(uniqueID_j)


if __name__ == '__main__':
    node = setupNode()
    node.runApplication(IncomingCallerIDQueue())
    twisted.internet.reactor.run()
    cleanup()
