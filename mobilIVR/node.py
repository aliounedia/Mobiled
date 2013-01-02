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

Provides class that encapsultes a MobilIVR Node. A node can be set up to provide resources (e.g. Asterisk IVR, 
Kannel SMS), and/or can be set up to provide the applications that use the resources 
"""

import sys, os, random
import threading
from ConfigParser import SafeConfigParser

from network.staticTupleSpace import StaticTupleSpacePeer

from network.rpc.protocol import TimeoutError

import twisted.internet.reactor

from twisted.internet.defer import inlineCallbacks, returnValue, Deferred

from network.staticTupleSpace import rpcmethod

#TODO: remove this
if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath(sys.path[0])+'/../')


import mobilIVR.application
import mobilIVR.configuration
import mobilIVR.sms
from mobilIVR.ivr.fastagi import FastAGIServer
import mobilIVR.ivr
from mobilIVR.logger import setupLogger

class MobilIVRNode(StaticTupleSpacePeer):
    """ Node in a MobilIVR network """
    def __init__(self, udpPort=4000):
        StaticTupleSpacePeer.__init__(self, udpPort=udpPort)

        self._localSMSHandlers = []
        self._localIVRHandlers = []
        self.resourceConfig = {'ivr': {}, 'sms': {}}
        self.fastAGIServer = None
        self._joinedNetwork = False
        self._callQueue = []
        self.claimedResources = 0 # Counter to keep track of how many consumable resources we are using
        self._log = setupLogger(debug=True, name='mobilIVR')
        

    def setupSMSReceive(self, port):
        """ Set the incoming SMS handler parameters (used for receiving SMSs)"""
        self.resourceConfig['sms']['rx'] = {}
        self.resourceConfig['sms']['rx']['port'] = port
        
    def setupSMSSend(self, kannelHost, kannelPort, kannelUsername, kannelPassword):
        """ Set the Kannel SendSMS service parameters (used for sending SMS
        messages) """
        settings = {}
        settings['host'] = kannelHost
        settings['port'] = kannelPort
        settings['username'] = kannelUsername
        settings['password'] = kannelPassword
        self.resourceConfig['sms']['tx'] = settings

    def setupIVROutgoing(self, asteriskManAPIHost, asteriskManAPIPort, asteriskManAPIChannels, asteriskManAPIUsername, asteriskManAPIPassword):
        """ Set the Asterisk Manager API settings (used for establishing
        outgoing calls)
        
        @type asteriskManAPIPort: int
        @param asteriskManAPIChannels: A list of Asterisk channels that this
                                       MobilIVR node should publish
        @type asteriskManAPIChannels: list
        """
        settings = {}
        settings['host'] = asteriskManAPIHost
        settings['port'] = int(asteriskManAPIPort)
        if type(asteriskManAPIChannels) == str:
            asteriskManAPIChannels = [asteriskManAPIChannels]
        settings['channels'] = asteriskManAPIChannels
        settings['username'] = asteriskManAPIUsername
        settings['secret'] = asteriskManAPIPassword
        
    def setupIVRGeneral(self, fastAGIPort, defaultTTS):
        """ Set general IVR settings
        
        @param fastAGIPort: TCP port number on which the Asterisk FastAGI
                            server should be run
        @type fastAGIPort: int
        @param defaultTTS: The name of the default text-to-speech engine, e.g.
                           "flite", "espeak" or "festival"
        @type defaultTTS: str
        """
        self.resourceConfig['ivr']['fastagi_port'] = int(fastAGIPort)
        self.resourceConfig['ivr']['default_tts'] = defaultTTS

    def loadConfigIVR(self, filename):
        """ Load IVR (i.e. Asterisk) configuration from a file """
        self.resourceConfig['ivr'] = mobilIVR.configuration.parseIVRConfig(filename)
    
    def loadConfigSMS(self, filename):
        """ Load SMS (i.e. Kannel) configuration from a file """
        self.resourceConfig['sms'] = mobilIVR.configuration.parseSMSConfig(filename)

    def startServices(self, *args):
        """ Starts all required servers and publishes all resources, as per
        the node's configuration """
        resourcesToPublish = []
        outerDf = Deferred()
        def publishNextResource(result=None):
            if len(resourcesToPublish) > 0:
                resType = resourcesToPublish.pop()
                df = self.publishResource(resType)
                df.addCallback(publishNextResource)
            else:
                outerDf.callback(None)
        
        if 'sms' in self.resourceConfig:
            if 'tx' in self.resourceConfig['sms']:
                #print '  ...should publish sms resource'
                resourcesToPublish.append('sms')
            if 'rx' in self.resourceConfig['sms']:
                #print 'creating incoming SMS handling-server...'
                incomingSMSHandler = mobilIVR.sms.SMSReceiver(self,self.resourceConfig['sms']['rx']['port'])
                incomingSMSHandler.start()
                #print '  ...done'
        if 'ivr' in self.resourceConfig:
            #print 'creating incoming IVR handling-server...'
            speechServerAddress = (self.resourceConfig['ivr']['tx']['speech_server_address'], \
                self.resourceConfig['ivr']['tx']['speech_server_port'])
            self.fastAGIServer = FastAGIServer( ('127.0.0.1', self.resourceConfig['ivr']['fastagi_port']), \
                speechServerAddress, self.resourceConfig['ivr']['default_tts'],self )
            #print 'server created'
            t = threading.Thread(target=self.fastAGIServer.serve_forever)
            t.start()
            #print '  ...done'
            self._log.info('Created local FastAGI server')
            if 'rx' in self.resourceConfig['ivr']:
                manAPIClient = mobilIVR.ivr.manager_api.ManAPIClient(self.resourceConfig['ivr']['tx']['host'], self.resourceConfig['ivr']['tx']['port'], self.resourceConfig['ivr']['tx']['username'], self.resourceConfig['ivr']['tx']['secret'])
                try:
                    manAPIClient.setVar('agihost', manAPIClient.socket.getsockname()[0])
                    manAPIClient.setVar('agiport', self.resourceConfig['ivr']['fastagi_port'])
                except Exception, e:
                    # print >> sys.stderr, 'Error preparing Asterisk for incoming calls: %s: %s' % (e.__class__.__name__, e)
                    # print >> sys.stderr, 'Depending on your Asterisk dialplan, incoming calls may not work.'
                    self._log.error('Error preparing Asterisk for incoming calls: %s: %s' % (e.__class__.__name__, e))
                    self._log.error('Depending on your Asterisk dialplan, incoming calls may not work.')
            if 'tx' in self.resourceConfig['ivr']:
                #print '  ...should publish ivr resource'
                resourcesToPublish.append('ivr')
            
                
                
        publishNextResource()
        #print 'returning from startServices'
        return outerDf

    @inlineCallbacks
    def publishResource(self, resType, originalPublisherID=None, returnCallbackFunc=None):
        """ stub for publishing resources """
        if originalPublisherID == None:
            resourceOwnerID = self.id
        else:
            resourceOwnerID = originalPublisherID
        resourceTuple = ('resource', resType, resourceOwnerID)
        #print 'publishing resource:', resType
        self._log.info('Publishing resource: ' + resType)
        yield self.put(resourceTuple, originalPublisherID=originalPublisherID)
        if callable(returnCallbackFunc):
            returnCallbackFunc()
        
    @inlineCallbacks
    def notifyEvent(self, event, callbackFunc=None):
        """ Notify the MobilIVR network of a new event """
                                             
        #NOTE: these checks are "hardcoded" on purpose, since the handler tuple templates may change
        if event['type'] == 'sms':
            handlerTemplate = ('handler', 'sms', str)
            def removeSMSHandler(result=None):
                self.getIfExists(handlerTemplate, getListenerTuple=True)    
            handlerTuple = yield self.readIfExists(handlerTemplate)
            #print '====>handlerTuple:', handlerTuple
            if handlerTuple != None:
                remoteNodeID = handlerTuple[2]
                if remoteNodeID == self.id:
                    self.handleEvent(event)
                    return
                remoteContact = yield self.findContact(remoteNodeID)
                if remoteContact != None:
                    df = remoteContact.handleEvent(event)
                    df.addErrback(removeSMSHandler)
                else:
                    removeSMSHandler(None)
        elif event['type'] == 'ivr':
            callbackResult = None
            # IVR handler template format: ('handler', 'ivr', nodeID, channelID, callerID)
            handlerTemplate = ('handler', 'ivr', str, None, None)
            # Find any application handlers that exist - set <numberOfResults> to 0 to get all results
            returnTuples = yield self.readIfExists(handlerTemplate, numberOfResults=0)
            
            handlerTupleList = []
            #Check for a single tuple, if so place it into a list
            if isinstance(returnTuples, tuple):
                handlerTupleList.append(returnTuples)
            
            #print '====>handlerTupleList:', handlerTupleList
            self._log.info('Finding IVR Handler | SESSION ID: ' + event['uniqueID'])
            # In the case of IVR, only one handler can handle the call
            if handlerTupleList != None:
                # Some possibly suitable handlers were found
                filteredGenericHandlers = [] # will contain applications that didn't specify callerID/channelID
                filteredChannelIDHandlers = [] # specified the dnid/channel ID
                filteredCallerIDHandlers = [] # specified the caller ID
                filteredSpecificHandlers = [] # specified both callerID and dnid
                for handlerTuple in handlerTupleList:
                    callerIDMatched = False
                    channelIDMatched = False
                    # check the application's callerID specification (handlerTuple[4])
                    if handlerTuple[4] != '':
                        # The app specified a callerID/range of callerIDs to handle
                        #TODO: implement callerID range matching - for now we only match specific ones
                        if handlerTuple[4] == event['callerID']:
                            callerIDMatched = True
                        else:
                            # This application should not handle this call
                            continue
                    # check the application's DNID (Dialed Number ID)/channel ID specification
                    #TODO: dnid range matching
                    if handlerTuple[3] != '':
                        if handlerTuple[3] == event['channel']:
                            channelIDMatched = True
                        else:
                            # This application should not handle this call
                            continue
                    
                    # Now filter anything that is waiting for something specific
                    if callerIDMatched and channelIDMatched:
                        filteredSpecificHandlers.append(handlerTuple)
                    elif channelIDMatched:
                        filteredCallerIDHandlers.append(handlerTuple)
                    elif callerIDMatched:
                        filteredCallerIDHandlers.append(handlerTuple)
                    else:
                        filteredGenericHandlers.append(handlerTuple)
                
                callHandled = False
                # This loop provides provides priority to apps that were more specific in their requirements than others
                for appHandlerGroup in (filteredSpecificHandlers, filteredChannelIDHandlers, filteredCallerIDHandlers, filteredGenericHandlers):
                    #print 'trying new group'        
                    groupLen = len(appHandlerGroup)
                    while groupLen > 0 and callHandled == False:
                        #print '  trying tuple in group'         
                        # Pick a random application from this group (intra-group priorities are not supported)
                        handlerTuple = appHandlerGroup[random.randint(0,groupLen-1)]
                        remoteNodeID = handlerTuple[2]
                        if remoteNodeID == self.id:
                            self._log.info('Local IVR Handler found | SESSION ID: ' + event['uniqueID'])
                            fastAGIPort = self.handleEvent(event)
                            callbackFunc( ('127.0.0.1', fastAGIPort) )
                            return
                        remoteContact = yield self.findContact(remoteNodeID)
                        if remoteContact != None:
                            try:
                                remoteFastAGIPort = yield remoteContact.handleEvent(event)
                                self._log.info('Remote IVR Handler found at ' + remoteContact.address + ' ' + str(remoteFastAGIPort) \
                                                       + ' | SESSION ID: ' + event['uniqueID'])
                                callHandled = True
                            except TimeoutError:
                                self._log.error('RPC Timeout! Unable to locate Remote IVR Handler, no response obtained | SESSION ID: ' \
                                                + event['uniqueID'])
                                # Remote node is dead/unreachable - remove this handler from the tuple space
                                #print '========Warning: Removing application handler from tuple space due to dead node (remote node not responding to handle RPC)'
                                #hmm = yield self.getIfExists(handlerTuple, getListenerTuple=False)
                                hmm = yield self.readIfExists(handlerTemplate, numberOfResults=0)
                                #print '========mobilIVRNode:  removed:', hmm
                                appHandlerGroup.remove(handlerTuple)
                                groupLen -= 1
                            else:
                                callbackResult = (remoteContact.address, remoteFastAGIPort)
                        else:
                            # Remote node is dead/unreachable - remove this handler from the tuple space
                            #print '=========Warning: Removing application handler from tuple space due to dead node (remote node unknown)'
                            hmm = yield self.getIfExists(handlerTuple, getListenerTuple=False)
                            #print '=========mobilIVRNode: removed:', hmm
                            appHandlerGroup.remove(handlerTuple)
                            groupLen -= 1
                    if callHandled:
                        #print '--breaking out of for loop'
                        break # out of for loop
            else:
                self._log.warning('No IVR Handler could be found, ensure handler published locally, or provide location of remote Handler at startup' \
                                  + ' | SESSION ID: ' + event['uniqueID'])
                print >> sys.stderr, 'Warning: dropping call on channel %s from caller ID %s - no suitable handler found' % (event['channel'], event['callerID'])
            if callbackFunc != None:
                # TODO: check if callbackResult = None and log this
                callbackFunc(callbackResult)
        #didn't notify anyone - we should probably log this...

    @inlineCallbacks
    def getTupleCallback(self, dTuple, returnCallbackFunc, blocking=True, removeTuple=True):
        """
        Convenience method to get a tuple from the tuple space, and return
        the value to a specific callback function (used for getting tuples from
        other threads (which thus can't used Twisted's C{Deferred} mechanism)
        because of the use of C{twisted.internet.reactor.callFromThread()})
        
        @param returnCallbackFunc: A callable object (e.g. a function), which
                                   takes one parameter: the returned tuple,
                                   or None (if not found and not blocking)
        @type returnCallbackFunc: function
        """
        if removeTuple:
            if blocking:
                resourceTuple = yield self.get(dTuple)
            else:
                resourceTuple = yield self.getIfExists(dTuple)
        else:
            if blocking:
                resourceTuple = yield self.read(dTuple)
            else:
                resourceTuple = yield self.readIfExists(dTuple)
        
        if callable(returnCallbackFunc):
            returnCallbackFunc(resourceTuple)
        returnValue(resourceTuple)

    @inlineCallbacks
    def getResource(self, resType, returnCallbackFunc, blocking=True, removeResource=True):
        """ 
        Retrieves an IVR or SMS resource from the MobilIVR tuple space
        
        @param resType: The type of resource to get (e.g. "ivr" or "sms)
        @type resType: str
        @param returnCallbackFunc: A reference to a callback function that
                                   should be called when this asynchronous
                                   operation is complete
        @type returnCallbackFunc: function
        @param blocking: If set to C{True}, this operation will block until the
                         requested resource is found. If C{False}, it will
                         return immediately (even when no resource was found)
        @type blocking: bool
        @removeResource: If set to C{True}, this operation will remove the
                         resource from the tuple space (so other nodes cannot
                         obtain the same resource). If C{False}, it will only
                         read the resource information, leaving it in the tuple
                         space
        @type removeResource: bool
        """
        
        resourceTemplate = ('resource', resType, str)
        found = [0]

        while 1:
            #print '...loop getResource'
            if removeResource:
                if blocking:
                    resourceTuple = yield self.get(resourceTemplate)
                else:
                    resourceTuple = yield self.getIfExists(resourceTemplate)
            else:
                if blocking:
                    resourceTuple = yield self.read(resourceTemplate)
                else:
                    resourceTuple = yield self.readIfExists(resourceTemplate)

            #print '-- resource tuple found ---'
            #print resourceTuple
            #print '---------------------------'
            if resourceTuple != None:
                remoteNodeID = resourceTuple[2]
                if remoteNodeID ==  self.id:
                    self._log.info('Local resource found')
                    returnCallbackFunc(None, self.invokeResource(resType), resourceTuple)
                    return
                contact = yield self.findContact(remoteNodeID)
                if contact == None:
                    # The resource entry was found on the DHT, but the remote node responsible for it no longer exists
                    if not removeResource:
                        # Since this resource is useless now (and we haven't removed it with a get) delete the resource entry by simply issueing a "get"
                        yield self.getIfExists(resourceTemplate)
                else:
                    #print '-- contact found ---'
                    #print contact
                    #print '---------------------------'
                    try:
                        resourceInfo = yield contact.invokeResource(resType)
                        self._log.info('Remote resource found: ' + str(resourceInfo))
                    except TimeoutError:
                        self._log.error('RPC Timeout error, no response from remote contact!')
                        resourceInfo = None
                    #print '--- resource info ---'
                    #print resourceInfo
                    #print
                    returnCallbackFunc(contact, resourceInfo, resourceTuple)
                    return
            else:
                returnCallbackFunc(None, None, None)
                return
    
    @rpcmethod
    def invokeResource(self, resType):
        """ Called by a remote peer node to indicate that it wants to use a
        resource published by this node; what is returned is dependant on the
        actual resource, but is usually direct-access information for the relevant
        physical resource (e.g. the address/port of a Kannel SMS gateway)
        """
        if resType not in self.resourceConfig:
            return None
        
        if resType == 'sms':
            if 'tx' not in self.resourceConfig['sms']:
                return None
            settings = self.resourceConfig['sms']['tx']
            return (settings['host'], settings['port'], settings['username'], settings['password'])
        elif resType == 'ivr':
            if 'tx' not in self.resourceConfig['ivr']:
                return None
            settings = self.resourceConfig['ivr']['tx']
            #TODO: Have more than one channel - tuple would need updating as well
            useChan = settings['channels'][0]
            self._log.info('Handing over location information of the local outgoing IVR resource')
            return settings['host'], settings['port'], useChan, settings['username'], settings['secret'],             settings['gateway_address'], settings['prefix'], settings['internal_extension_length']
        
    @rpcmethod
    def handleEvent(self, event):
        """ Called by a remote peer node let this node handle the specified event """
        if event['type'] == 'sms':
            if len(self._localSMSHandlers) > 0:
                #TODO: we really need to add some filtering capability to this whole thing...
                # Set up the application's thread of execution
                handlerApp = self._localSMSHandlers[0]
                handlerAppThread = mobilIVR.application.SMSHandlerThread(handlerApp, event['callerID'], event['message'], self)
                # run the app...
                handlerAppThread.start()
                return 'OK'
        elif event['type'] == 'ivr':
            if len(self._localIVRHandlers) > 0:
                # Prepare the IVR handler
                handlerApp = self._localIVRHandlers[0][0]
                handlerAppArgs = self._localIVRHandlers[0][1]
                handlerAppThread = mobilIVR.application.IVRHandlerThread(handlerApp, self, applicationArgs=handlerAppArgs)
                # Prime the local AGI server for the incoming call
                self.fastAGIServer.setIVRHandler(event['ivrHandlerID'], handlerAppThread)
                # run the app...
                handlerAppThread.start()
                # ...and return the port for our local AGI server
                self._log.info('Handing over location information of the local IVR Handler')
                return self.resourceConfig['ivr']['fastagi_port']
        elif event['type'] == 'shutdown':
            # A node has been shut down; remove it from our routing table
            #TODO: The following code should be moved into Entangled, by means of a "purgeContact" or similar (or simply a "force" parameter to RoutingTable.removeContact())
            contactBucketIndex = self._routingTable._kbucketIndex(event['nodeID'])
            try:
                self._routingTable._buckets[contactBucketIndex].removeContact(event['nodeID'])
            except ValueError:
                pass
            return 'OK'

    def _doRunApplication(self, app):
        appThread = mobilIVR.application.AppThread(app, self)
        appThread.start()
        df = Deferred()
        df.callback(None)
        return df

    def publishHandler(self, handlerType, args={}):
        """ stub for publishing applications """
        if handlerType == 'ivr':
            handlerTuple = ('handler', 'ivr', self.id, args.get('channel', ''), args.get('callerID', ''))
            #print 'putting handler:',handlerTuple
        #elif handlerType == 'sms':
        #    handlerTuple = ('handler', 'sms', args.get('callerID'))
        else:
            handlerTuple = ('handler', handlerType, self.id)
            #print 'putting handler:',handlerTuple
        #print 'publishing handler:', handlerType
        self._log.info('Publishing handler: ' + handlerType)
        df = self.put(handlerTuple)
        return df

    def runApplication(self, app, args={}):
        """ Schedule a call for this application in the reactor
        
        This registers IVR & SMS event handlers ("reactive" applications). It
        also runs "proactive" applications C{mobilIVR.application.Application}
        as soon as possible (i.e. as soon as the node has joined the network).
        
        @param app: The application to run. This should be anything inheriting
                    from the following interfaces::
                        C{mobilIVR.application.Application}
                        C{mobilIVR.application.IVRHandler}
                        C{mobilIVR.application.SMSHandler}
                    It can be an instance of such a class, B{or the class itself}.
        @type app: object or class
        
        @note: If an instance of an application is passed as the C{app} parameter,
               only one instance of that application will exist in the MobilIVR
               node; in other words, B{all instance variables will be shared
               among "sessions"/threads using the application}. This is useful
               for implementing e.g. counters (or handling custom C{__init__()}
               methods, and is fairly safe for SMS-based applications, but care
               should be taken when implementing IVR services in this fashion,
               as for instance saving the IVR session as an instance variable
               will cause disruptive behaviour when handling multiple
               simultaneous calls.
        """
        claimed = False
        # These basic checks just make sure the object/class passed to this method
        # exposes an appropriate API - the thread starting wrappers will perform more checks
        if hasattr(app, 'handleSMS'):
            if callable(app.handleSMS):
                if self._joinedNetwork == False:
                    self._callQueue.append((self.publishHandler, 'sms'))
                else:
                    self.publishHandler('sms')
                self._localSMSHandlers.append(app)
                claimed = True
        if hasattr(app, 'handleIVR'):
            if callable(app.handleIVR):
                if self._joinedNetwork == False:
                    self._callQueue.append((self.publishHandler, 'ivr', args))
                else:
                    self.publishHandler('ivr')
                self._localIVRHandlers.append((app, args))
                claimed = True
        if hasattr(app, 'run'):
            if callable(app.run):
                if self._joinedNetwork == False:
                    self._callQueue.append((self._doRunApplication, app))
                else:
                    self._doRunApplication(app)
                claimed = True
        if not claimed:
            raise ValueError, '%s is not a class or instance of a valid application type' % type(app)

    @inlineCallbacks
    def shutdown(self):
        # Inform our closest neighbours on the DHT that we are leaving the network
        #TODO: this might have to be moved into the EntangledNode class in the future
        if self.claimedResources > 0:
            # This node is still needs to release some resources; wait until this is done 
            twisted.internet.reactor.callLater(0.5, self.shutdown)
            return
        closestNodes = yield self._iterativeFind(self.id)
        shutdownEvent = {'type': 'shutdown', 'nodeID': self.id}
        for contact in closestNodes:
            try:
                yield contact.handleEvent(shutdownEvent)
            except:
                pass
        #TODO: ...and the twisted reactor should NEVER be stopped by us (what if the client app uses twisted for something else as well?)
        twisted.internet.reactor.callLater(0.5, twisted.internet.reactor.stop)

    def joinNetwork(self, knownNodeAddresses=None):
        self._log.info('Joining network')
        StaticTupleSpacePeer.joinNetwork(self, knownNodeAddresses)
        self._joinDeferred.addCallback(self.startServices)
        self._joinDeferred.addCallback(self._execCallQueue)
        self._joinDeferred.addErrback(self._joinFailed)
        
    def _joinFailed(self, error):
        error.trap(Exception)
        msg = error.getErrorMessage()
        self._log.error('Join failed! ' + str(msg))
        #print 'Join failed!\n' + str(msg)
        
    def _execCallQueue(self, result):
        #self._joinDeferred = None
        if len(self._callQueue) > 0:
            queuedCall = self._callQueue.pop()
            func = queuedCall[0]
            args = queuedCall[1:]
            df = func(*args)
            df.addCallback(self._execCallQueue)
            return df
        else:
            self._joinedNetwork = True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage:\n%s UDP_PORT  [KNOWN_NODE_IP  KNOWN_NODE_PORT]' % sys.argv[0]
        print 'or:\n%s UDP_PORT  [FILE_WITH_KNOWN_NODES]' % sys.argv[0]
        print '\nIf a file is specified, it should containg one IP address and UDP port\nper line, seperated by a space.'
        sys.exit(1)
    try:
        int(sys.argv[1])
    except ValueError:
        print '\nUDP_PORT must be an integer value.\n'
        print 'Usage:\n%s UDP_PORT  [KNOWN_NODE_IP  KNOWN_NODE_PORT]' % sys.argv[0]
        print 'or:\n%s UDP_PORT  [FILE_WITH_KNOWN_NODES]' % sys.argv[0]
        print '\nIf a file is specified, it should contain one IP address and UDP port\nper line, seperated by a space.'
        sys.exit(1)

    
    if len(sys.argv) == 4:
        knownNodes = [(sys.argv[2], int(sys.argv[3]))]
    elif len(sys.argv) == 3:
        knownNodes = []
        f = open(sys.argv[2], 'r')
        lines = f.readlines()
        f.close()
        for line in lines:
            ipAddress, udpPort = line.split()
            knownNodes.append((ipAddress, int(udpPort)))
    else:
        knownNodes = None
    



    node = MobilIVRNode(int(sys.argv[1]), )

    # Set up the node to publish some resources
    configDir = os.path.abspath(sys.path[0])+'/etc'
    node.loadConfigIVR(configDir+'/ivr.conf')
    node.loadConfigSMS(configDir+'/sms.conf')
    
    node.joinNetwork(knownNodes)
    
    print 'node running on UDP port %d...' % node.port
    
    twisted.internet.reactor.run() #IGNORE:E1101
    
    if len(threading.enumerate()) > 1:
        os._exit(0)
