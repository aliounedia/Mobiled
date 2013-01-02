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

Provides a request handlers to send and receive SMS messages using Kannel
"""

import time
import mobilIVR.resources
import socket

import twisted.internet.reactor

import http
import threading
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urllib import unquote_plus

class KannelRequestHandler(BaseHTTPRequestHandler):
    """ Simple web request handler to receive the incoming SMS from Kannel """
    def do_GET(self):
        # Find the variables passed by this request
        varStr = self.path[self.path.find('?')+1:]
        varPairs = varStr.split('&')
        GETvars = dict()

        self.send_response(200)
        self.end_headers()
        try:
            for keyValue in varPairs:
                sep = keyValue.split('=')
                GETvars[unquote_plus(sep[0]).lower()] = unquote_plus(sep[1])

            if not GETvars.has_key('callerid'):
                self.wfile.write("HTTP/1.0 400 Bad Request\nContent-Type: text/plain; charset=UTF-8\n\nInvalid request; missing \"callerid\" variable.\n")
                return
            elif not GETvars.has_key('message'):
                self.wfile.write("HTTP/1.0 400 Bad Request\nContent-Type: text/plain; charset=UTF-8\n\nInvalid request; missing \"message\" variable.\n")
                return
        except (IndexError, KeyError):
            self.wfile.write("HTTP/1.0 400 Bad Request\nContent-Type: text/plain; charset=UTF-8\n\nInvalid request.\n")
            return            
        event = {'type': 'sms',
                 'callerID': GETvars['callerid'],
                 'message': GETvars['message']}
        twisted.internet.reactor.callFromThread(self.server.localNode.notifyEvent, event) #IGNORE:E1101
        self.wfile.write("HTTP/1.0 200 OK\nContent-Type: text/plain; charset=UTF-8\n\nMessage received OK.\n")


class SMSReceiver(threading.Thread):
    def __init__(self, node, Port):
        threading.Thread.__init__(self)
        self._localNode = node
        self.port = Port
        
    def run(self):
        server = HTTPServer(('', self.port), KannelRequestHandler)
        server.localNode = self._localNode
        server.failure = None
        server.serve_forever()
        #server.handle_request()
        #if server.failure != None:
        #    self.failMsg = server.failure


class SMSSender(mobilIVR.resources.Resource):
    """ Class used for sending SMS messages (and finding resources capable of
    sending SMS messages)
    """
    def __init__(self, node):
        self._gotResource = False
        self._localNode = node
        self.kannelAddress = None
        self.kannelPort = None
        self.kannelUsername = None
        self.kannelPassword = None

    def getResource(self):
        def gotResourceDetails(remoteContact, resourceInfo, resourceTuple):
            self._gotResource = True
            if resourceInfo != None:
                self.kannelAddress, self.kannelPort, self.kannelUsername, self.kannelPassword = resourceInfo
                if self.kannelAddress in ('127.0.0.1', 'localhost') and remoteContact != None:
                    self.kannelAddress = remoteContact.address
        twisted.internet.reactor.callFromThread(self._localNode.getResource, 'sms', gotResourceDetails, removeResource=False) #IGNORE:E1101
        while self._gotResource == False:
            time.sleep(0.1)

    def getResourceIfExists(self):
        def gotResourceDetails(remoteContact, resourceInfo, resourceTuple):
            self._gotResource = True
            if resourceInfo != None:
                self.kannelAddress, self.kannelPort, self.kannelUsername, self.kannelPassword = resourceInfo
                if self.kannelAddress in ('127.0.0.1', 'localhost') and remoteContact != None:
                    self.kannelAddress = remoteContact.address
        twisted.internet.reactor.callFromThread(self._localNode.getResource, 'sms', gotResourceDetails, blocking=False, removeResource=False) #IGNORE:E1101
        while self._gotResource == False:
            time.sleep(0.1)
        return self.kannelAddress != None

    def sendMessage(self, message, destination, origin='MobilIVR'):
        """ Sends an SMS to one or many numbers
        
        @param message: the message to send.
        @type message: str
        @param destination: the destination number(s) to send the SMS to. This
                            can be a single number (as a string) or a list of
                            strings, each containing a seperate destination
                            number.
        @type destination: str or list
        @return: per destination, True if the send was successful, False otherwise.
        @rtype: list of bool
        """
        if type(destination) == str:
            destinations = [destination]
        else:
            destinations = destination
    
        hmm = [0]
        def onMsgSent(result):
            hmm[0] -= 1
        
        rv = []
        for dest in destinations:
            reqVars = {'username' : self.kannelUsername,
                       'password' : self.kannelPassword,
                       'from'     : origin,
                       'to'       : dest,
                       'text'     : message}
            try:
                response = http.HTTPGet.get(self.kannelAddress, self.kannelPort, '/cgi-bin/sendsms', reqVars)

                # check response.status in the 200 -> OK, 400 _> error and 500 ->error range

                # TODO: Check for HTTP response codes in the above response
                # TODO: Also check if kannel returns more detailed information, eg. amount of sms messages sent for this message

                #print 'response status: %s\nresponse message:\n%s' % (response.status, response.msg)
                if response.status >= 200 and response.status < 300:
                    rv.append(True)
                else:
                    rv.append(False)
            except socket.error, (value, ErrorMessage):
                #print "Unable to create socket:\n%s" % ErrorMessage
                rv.append(False)
        
        return rv
