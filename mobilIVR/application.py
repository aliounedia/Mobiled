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

Provides an Thread class for SMS/IVR applications and handlers.
"""

import threading, time

class AppThread(threading.Thread):
    """ Used by the host node to start "proactive" applications """
    def __init__(self, application, node, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        """
        @param application: The application to run
        @type application: object or class
        @param node: The host node
        @type node: mobilIVR.node.MobilIVRNode
        """
        if isinstance(application, Application) or (type(application) != type and hasattr(application, 'run')):
            # it's an existing application instance
            self.application = application
        else:
            # it's a class
            self.application = application()
        self.node = node        
        threading.Thread.__init__(self, group, target, name, args, kwargs, verbose)

    def run(self):
        self.application.run(self.node)

class IVRHandlerThread(threading.Thread):
    """ Used by the host node to start applications in reaction to IVR events """
    def __init__(self, application, node, applicationArgs = [], group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        """
        @param application: The application to run
        @type application: object or class
        @param node: The host node
        @type node: mobilIVR.node.MobilIVRNode
        """
        if isinstance(application, IVRHandler) or (type(application) != type and hasattr(application, 'handleIVR')):
            # it's an existing application instance
            self.application = application
        else:
            # it's a class
            if len(applicationArgs) > 0:
                self.application = application(applicationArgs)
            else:
                self.application = application()
                
        self.node = node
        self.agiRequestHandler = None
        threading.Thread.__init__(self, group, target, name, args, kwargs, verbose)
    
    def run(self):
        while self.agiRequestHandler == None:
            time.sleep(0.1)
        self.application.handleIVR(self.agiRequestHandler, self.node)

class SMSHandlerThread(threading.Thread):
    """ Used by the host node to start applications in reaction to SMS events """
    def __init__(self, application, callerID, message, node, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        """
        @param application: The application to run
        @type application: object or class
        @param node: The host node
        @type node: mobilIVR.node.MobilIVRNode
        """
        if isinstance(application, SMSHandler) or (type(application) != type and hasattr(application, 'handleSMS')):
            # it's an existing application instance
            self.application = application
        else:
            # it's a class
            self.application = application()
        self.callerID = callerID
        self.message = message
        self.node = node
        threading.Thread.__init__(self, group, target, name, args, kwargs, verbose)
    
    def run(self):
        self.application.handleSMS(self.callerID, self.message, self.node)

class Application(object):
    """ Interface of a generic "proactive" MobilIVR application """
    def run(self, node):
        """ Entry point into the application
        @param node: The MobilIVRNode instance that is executing this application;
                     this provides a mechanism for accessing resources, publishing
                     events, acessing the P2P overlay network, etc
        @type node: mobilIVR.node.MobilIVRNode
        """

class SMSHandler(object):
    """ Stub for the interface of a MobilIVR "reactive" application (i.e. event handler) for SMSs """
    def handleSMS(self, callerID, message, node):
        """ Entry point into the application; this method is passed the callerID and
        message contents of the SMS that triggered the execution of this
        application """

class IVRHandler(object):
    """ Interface of a MobilIVR IVR-handler application """
    #def __init__(self, channel=None, callerID=None):
    #    """
    #    @param channel: The Asterisk channel the application should respond to.
    #                    If this is None (default), respond to incoming calls
    #                    on all channels.
    #    @param callerID: The caller ID the application should respond to.
    #                     If this is None (default), respond to all callers.
    #    """
    #    self.__responseChannel = channel
    #    self.__responseCallerID = callerID
    
    def handleIVR(self, ivr, node):
        """
        Entry point into the application; this method is passed the
        IVRInterface instance of the incoming call that triggered the
        execution of this application.
        """