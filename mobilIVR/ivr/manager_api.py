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

MobilIVR Asterisk channel: Asterisk Manager API Interface

Contains classes related to interfacing with the network-based
Asterisk Manager API; the primary function is to provide a mechanism
for originating an outgoing call from the PBX.
"""

import socket 
import time
import re

# "Soft" exceptions
class OriginateFailed(Exception):
    """ The Asterisk 'Originate' command failed - unable to start an
    outbound voice call """

class LoginFailed(Exception):
    """ Could not log into the Asterisk Manager API """

class ManagerConnectFailed(Exception):
    """ Could not connect ot the Asterisk Manger API """
    
class SetVarFailed(Exception):
    """ The Asterisk 'SetVar' command failed """

class ManAPIClient:
    """ Limited client implementation for the Asterisk Manager API

        Used for initiating an outgoing call from the Asterisk PBX
    """
    endCmdString = "\r\n\r\n"
    loginCommand = ['Action: Login', 'Username: %s', 'Secret: %s', 'ActionID: 1']
    logoutCommand = ['Action: Logoff', 'ActionID: 3']
    callCommand = ['Action: Originate', 'Channel: %s/%s', 'Priority: 1', 'Exten: s', 'Context: default', 'CallerID: %s', 'Variable: keyword=%s|agihost=%s|agiport=%d|ivrhandlerid=%s', 'ActionID: 2']    
    setVarCommand = ['Action: Setvar', 'Variable: %s', 'Value: %s']
    
    responseRegexp = re.compile(r'^Response:[\s]+([^\s]+)[\s]*$', re.MULTILINE)
    
    def __init__(self, managerApiAddress, managerApiPort, managerApiUserName, managerApiSecret):
        # Configuration setup
        self.host = managerApiAddress
        self.port = managerApiPort
        self.username = managerApiUserName
        self.secret = managerApiSecret
        self.socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self._connected = False
    
    def _connect(self):
        if not self._connected:
            try:
                self.socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
                self.socket.connect( ( self.host, self.port ) )
            except socket.error, (errNum, errMsg): #IGNORE:W0612
                raise ManagerConnectFailed, errMsg
            else:
                self._connected = True

    def _login(self):
        """ Logs into the Asterisk Manager API, and returns the active
        socket object on success """
        self._connect()
        loginMsg = "\r\n".join(self.loginCommand) % (self.username, self.secret)
        
        response = self.socket.recv(1024)
        self.socket.send(loginMsg)
        self.socket.send(self.endCmdString)
        time.sleep(0.1)
        response = self.socket.recv(1024)
        if 'Success' not in self.responseRegexp.findall(response):
            raise LoginFailed

    def _logout(self):
        if self._connected:
            logoutMsg = "\r\n".join(self.logoutCommand)
            self.socket.send(logoutMsg)
            self.socket.send(self.endCmdString)
            time.sleep(0.1)
            self.socket.shutdown(2)
            self.socket.close()
            self._connected = False

    def dial(self, Number, AstChannel, AGIServerAddress, ivrHandlerID):
        """ Initiates a outgoing call from the pre-configured Asterisk PBX.
        
        Connects to the Asterisk Manager API using the configured host/port.
        
        @param Number: Destination caller ID
        @type Number: str
        @param AstChannel: The name of the Asterisk channel to use for this call
        @type AstChannel: str
        @param AGIServerAddress: the FastAGI server's server_adress variable (hostname, port)
        @type AGIServerAddress: tuple
        
        @raise LoginFailed: Login failed, usually due to incorrect username/password
        @raise OriginateFailed: The call could not be initiated
        @raise ManagerConnectFailed: A network error occurred. Check that the Manager API
                                     is running in Asterisk
        """
        self._login() 
        # For debugging
        if AstChannel.startswith('Console'):
            AstChannel = 'Console' #IGNORE:C0103
            Number = 'dsp' #IGNORE:C0103

        callMsg = "\r\n".join(self.callCommand) % ( AstChannel, Number, Number, 'keywords', self.socket.getsockname()[0], AGIServerAddress[1], ivrHandlerID )
        #actionID_re = re.compile(r'^ActionID:[\s]+([\d]+)[\s]*$', re.MULTILINE)
        # Initiate call
        self.socket.send(callMsg)
        self.socket.send(self.endCmdString)
        time.sleep(0.1)
        response = self.socket.recv(1024)
        if 'Success' not in self.responseRegexp.findall(response):
            raise OriginateFailed('Asterisk manager call originate failed!')
        self._logout()

    def setVar(self, name, value):
        """ Sets a (global) Asterisk variable
        
        @param name: The name of the variable to set
        @type name: str
        @param value: The value to assign to the variable
        @type value: str
        """
        setVarMsg = "\r\n".join(self.setVarCommand) % (name, value)
        self._login()
        self.socket.send(setVarMsg)
        self.socket.send(self.endCmdString)
        time.sleep(0.1)
        response = self.socket.recv(1024)
        if 'Success' not in self.responseRegexp.findall(response):
            raise SetVarFailed
        self._logout()
