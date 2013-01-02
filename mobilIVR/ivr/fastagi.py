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
Provides an Asterisk FastAGI server to handle network-based Asterisk AGI client requests, and
dispatches requests to their corresponding handlers (aka MobilIVR applications).
Also provides an AGI request handler; this provides a friendly synchronous API to the Asterisk FastAGI protocol.

@author: Francois Aucamp
"""

#! /usr/bin/env python

import socket
import errno
import SocketServer
import re
import time
import random
import os.path
import twisted.internet.reactor
import base64
import datetime

from mobilIVR.ivr import IVRDialer
import fastagi_constants

class InvalidCommand(Exception):
    """ Raised when an invalid (unknown) AGI command is issued to Asterisk """
    
class SendAGICommandError(Exception):
    """ Raised when an fault occurs while attempting to send an AGI command """

class ExecuteCommandError(Exception):
    """
    Raised when an error occurs while executing a successfully sent AGI command.
    """

class FastAGIServer(SocketServer.ThreadingTCPServer):
    """ Asterisk FastAGI server
    
    This server handles network-based Asterisk AGI client requests, and
    dispatches requests to their corresponding handlers (aka MobilIVR
    applications).
    """
    allow_reuse_address = True
    
    def __init__(self, server_address, speechServerAddress,defaultTTS, node):
        SocketServer.ThreadingTCPServer.__init__(self, server_address, IVRInterface)
        self.ivrHandlers = {}
        self.tts = defaultTTS
        self.speechServerAddress = speechServerAddress
        self.localNode = node
        
    def process_request_thread(self, request, client_address):
        """Same as in BaseServer but as a thread.

        In addition, exception handling is done here.

        """
        try:
            self.finish_request(request, client_address)
#            self.close_request(request)
        except:
            self.handle_error(request, client_address)
            self.close_request(request)

    def setIVRHandler(self, handlerID, handlerInstance):
        self.ivrHandlers[handlerID] = handlerInstance


class AGIRequestHandler(SocketServer.StreamRequestHandler):
    """
    Initial AGI request handler; this class sets up the connection and dispatches it to
    the relevant waiting IVR handler (i.e. dialplan)
    """
    def __init__(self, request, client_address, server):
        self._connHandedOverToHandler = False
        self._ivrHandlerID = None
        self.channel = None
        self.callerID = None
        self.tts = server.tts
        self.speechServerAddress = server.speechServerAddress
        SocketServer.StreamRequestHandler.__init__(self, request, client_address, server)
    
    def send(self, Command, FullResult=False):
        """ Sends a command to Asterisk.
        
        @param Command: the command to send to Asterisk
        @type Command: str
        
        @return: the result of the command, or -3 if there was an error
        """
        Command = Command.strip() #IGNORE:C0103
        if Command[-1] != '\n':
            Command += '\n'
        try:
            self.wfile.write(Command.encode( 'utf-8' ))
        except Exception, e:
            errorMessage = 'Error while trying to send AGI command! ' + str(e)
            raise SendAGICommandError(errorMessage)
        return self.getResult(FullResult)
    
    def finish(self):
        if self._connHandedOverToHandler == False:
            self.close()
            
    def close(self):
        # Only close the connections if no other handler is responsible for them
        if not self.wfile.closed:
            self.wfile.flush()
            self.wfile.close()
        if not self.rfile.closed:
            self.rfile.close()
        self.connection.close()
        if self._ivrHandlerID != None and self._ivrHandlerID in self.server.ivrHandlers:
            # Remove the IVR handler ID since we're done with this specific IVR session
            del self.server.ivrHandlers[self._ivrHandlerID]
    __del__ = close
    
    #TODO: improve documentation; get clarity on return type
    def getResult(self, FullResult=False):
        """ Reads a response from Asterisk, checking the result

        @raise InvalidCommand: An unknown/invalid AGI command was issued
    
        @return: the result read (if the return code is 200=success), or -3 on error
                 If <FullResult> is True, return a tuple containing the result read
                 and the rest of the result message as a string
        """
        badResult = -3
        if FullResult == True:
            badResult = (-3, '')
        
        line = self.rfile.readline().strip()
        self.rfile.flush()
        regExp = re.compile(r"(^\d+)\s+(.*)")
        match = regExp.search(line)
        returnCode = 0
        if match != None:
            returnCode, response = match.groups()
            try:
                returnCode = int(returnCode)
            except ValueError:
#                self.message("AGI Debug: Result interpretation failed: %s" % line)
                return badResult
        else:
            # Check for a syntax error
            if line.startswith('520'):
                # Read the usage message and discard it (we're returning an error code anyway)
                line = self.rfile.readline()
                while not line.startswith('520'):
                    line = self.rfile.readline()
            return badResult

        if returnCode == 200:
            regExp = re.compile(r"result=-?[\d]+")
            match = regExp.search(response)
            result = 0
            if match != None:
                try:
                    result, data = match.groups()
                except:
                    result = response
                result = result[7:]
                try:
                    result = int(result)
                except ValueError:
                    # This usually happens if we have a compound return code (e.g. 0 endpos=23423)
                    result = str(result)
                    pos = result.find('endpos=')
                    if pos != -1:
                        # Filter for "endpos=" statements; this is our only clue that an STREAM command succeeded/failed,
                        # as Asterisk returns 200 for this command even if the file was not found
                        endposValue = int(result[pos+7:])
                        try:
                            result = int(result[:pos-1])
                        except ValueError:
                            # Ok, there's still some other text in here; try to get _any_ int value at this point
                            for textValue in result[:pos-1].split(' '):
                                try:
                                    result = int(textValue)
                                except ValueError:
                                    continue
                                else:
                                    break
                        # if endpos == 0 and result == 0, it is *reasonably* safe to assume the playback failed
                        if result == 0 and endposValue == 0:
 #                           self.message("AGI Error: "+response)
                            result = badResult
                    else:
                        pos = result.find(" ")
                        if pos != -1:
                            resultInt = result[:pos]
                            resultInt = int(resultInt)
                            if FullResult == True:
                                result = (resultInt, result[pos+1:])
                            else:
                                result = resultInt
                        else:
                            if FullResult == True:
                                result = (0, '')
                            else:
                                result = 0
            return result
        elif returnCode == 510:
            # Invalid command; let the CLI console know
            raise InvalidCommand, response
        else:
            # Error (could be unknown command, incorrect usage, etc)
            # no detailed checks done here - we are only interested whether or not our commands succeed
            return badResult
    
    def handle(self):
        """
        Handles the AGI socket request; finds the correlating IVR handler, and lets it take over from there.
        This basically gets AGI environment data from Asterisk.     
        """
        # Read AGI environment (read until blank line)
        env = ''
        callerID = None
        ivrHandlerID = None
        channel = None
        dialedNumberID = None
        while(env != '\n'):
            #print env
            env = self.rfile.readline()
            if ':' in env:
                (key, value) = env.split(':', 1)
                if key == 'agi_callerid':
                    callerID = value.strip()
                    if callerID == 'unknown':
                        callerID = None
                elif key == 'agi_channel':
                    channel = value.strip()
                elif key == 'agi_dnid':
                    dialedNumberID = value.strip()
                    if dialedNumberID == 'unknown':
                        dialedNumberID = None
                elif key == 'agi_uniqueid':
                    uniqueID = value.strip()
        self.callerID = callerID
        self.channel = channel

        self.dialedNumber = None
        self.divertedNumber = None
        # read the dialed number variable, first checking if a divesion occurred 
        dialedNumber = self.getVariable("CALLERID(rdnis)")
        if dialedNumber:
            self.dialedNumber = dialedNumber
            # the diverted Number 
            self.divertedNumber = self.getVariable("CALLERID(dnid)")
        else:
            self.dialedNumber = self.getVariable("CALLERID(dnid)")
        
        #print '============== INCOMING CALL ==============='
        #print 'callerID:', self.callerID
        #print 'channel:', self.channel
        
        # Get the ivr handler ID, if there is any
        result = self.send('GET VARIABLE ivrhandlerid', True)
        if type(result) == tuple:
            self._ivrHandlerID = result[1][1:-1]

        if self._ivrHandlerID != None:
            # This request is a response to a manAPI request that we sent; send it to the correct handler app
            if self._ivrHandlerID in self.server.ivrHandlers:
                self.server.localNode._log.info('Received connection on local FastAGI server, starting the handler for this call | SESSION ID: ' + uniqueID)
                
                # Pass this instance to the handler
                handler = self.server.ivrHandlers[self._ivrHandlerID]

                #handler.agiRequestHandler = self
                #self._connHandedOverToHandler = True
                if isinstance(handler, IVRDialer):
                    self.server.localNode._log.info('Attempting to set request handler.')
                    if not handler._rogueHandler:
                        handler.agiRequestHandler = self
                        self._connHandedOverToHandler = True
                    else:
                        self.server.localNode._log.error('Rogue handler detected, hanging up call %s !' %(self.callerID))
                        self.hangup()
                        #del handler
                else:
                    handler.agiRequestHandler = self
                    self._connHandedOverToHandler = True
            #TODO: handle the (unlikely) case where we have no handler....
        else:
            # No "local" handler was waiting for this AGI request; it must be an incoming call then
            # - let the MobilIVR network handle this
            self.server.localNode._log.info('Received incoming call on local FastAGI server, | SESSION ID: ' + uniqueID)
            remoteAGIAddress = []
            def remoteAGIHandlerFound(address):
                remoteAGIAddress.append(address)
            
            resourceTuple = ('resource', 'ivr', self.server.localNode.id)
            
            tupleFound = [0]
            
            def resourceTupleFound(returnedTuple):
                # We needed to remove the tuple from the tuple space
                if returnedTuple != None:
                    # Take the resource from the tuple space (as it is occupied)
                    self.server.localNode.claimedResources += 1
                    self._ivrHandlerID = returnedTuple[2]
                    self.server.setIVRHandler(self._ivrHandlerID, None)
                tupleFound[0] = returnedTuple
            
            #TODO: This won't work; cause the function searches for a resource TYPE (aka string), not a tuple...
            twisted.internet.reactor.callFromThread(self.server.localNode.getTupleCallback, resourceTuple, resourceTupleFound, blocking=False, removeTuple=True)
            #twisted.internet.reactor.callFromThread(self.server.localNode.getResource, resourceTuple, resourceTupleFound, blocking=False, removeResource=True)
            
            while tupleFound[0] == 0:
                time.sleep(0.1)

            ivrHandlerID = 'incoming:'+channel+str(random.randint(0, 999))
            self.send('SET VARIABLE ivrhandlerid %s' % ivrHandlerID)
            event = {'type' : 'ivr',
                     'ivrHandlerID' : ivrHandlerID,
                     'channel' : channel,
                     'callerID' : callerID,
                     'uniqueID' : uniqueID}
            twisted.internet.reactor.callFromThread(self.server.localNode.notifyEvent, event, remoteAGIHandlerFound) #IGNORE:E1101
            # Wait for the node to find us something (or inform us that there is nothing available)
            while len(remoteAGIAddress) == 0:
                time.sleep(0.1)
            if remoteAGIAddress[0] != None:
                # Re-route the current AGI connection to the remote AGI handler's address/port
                remoteAddr, remotePort = remoteAGIAddress[0]
                self.server.localNode._log.info('Re-routing call to remote fastAGI server: ' + str((remoteAddr, remotePort)) \
                                                + ' | SESSION ID: ' + event['uniqueID'])
                #print 're-routing call to: %:%d' % (remoteAddr, remotePort)
                command = 'EXEC AGI agi://%s:%d' % (remoteAddr, remotePort)
                self.send(command)
                self.close()
                # The call has ended; put the IVR resource back in the tuple space
                if tupleFound[0] != None:
                    resourceReleased = [False]
                    def releaseCompleted():
                        self.server.localNode.claimedResources -= 1
                        resourceReleased[0] = True
                    twisted.internet.reactor.callFromThread(self.server.localNode.publishResource, 'ivr', originalPublisherID=tupleFound[0][2], returnCallbackFunc=releaseCompleted) #IGNORE:E1101
                    while resourceReleased[0] == False:
                        time.sleep(0.1)


class IVRInterface(AGIRequestHandler):
    """
    AGI request handler; this provides a friendly synchronous API to the Asterisk FastAGI protocol
    """
    def __init__(self, request, client_address, server):
        self._hungup = False
        AGIRequestHandler.__init__(self, request, client_address, server)
        
    def answer(self):
        """ Answers the Asterisk channel (i.e. phone line) """
        self._hungup = False
        return self.send('ANSWER')
    
    def hangup(self, status='HANGUP'):
        """ Ends the AGI IVR session. This normally hangs up the call.
        
        @note: No other methods in this class should be called after this
               is called.
        
        @param status: The status code to return to Asterisk; this may be
                       'HANGUP', 'SUCCESS' or 'FAILURE', depending on how
                       Asterisk should respond to this (note that your
                       Asterisk dialplan should be set up to accommodate
                       these responses).
        @type status: str
        """
        if self._hungup == True:
            # We have already hung up this call; maybe raise an exception?
            return
        else:
            self.setVariable('AGISTATUS', status)
            self._hungup = True
            self.close()
    
    def execute(self, command):
        """ Invokes the asterisk EXEC AGI command, used to execute non-agi commands
        
            @param command: contains the non-agi command to exectute
             
        """
        return self.send('EXEC ' + command)    
    
    def say(self, text):
        """ Instructs Asterisk to say <Text> using a text-to-speech engine.
        
        This command cannot be interrupted by the user.
        """
        #log("agiWrapper.say() called")
        return self.send(self._formatTextForTTS(text))
    
    def sayControl(self, Text, IntKeys):
        """ Same as say(), but with interrupt keys <IntKeys> defined.
        
        This function returns the dtmf digit that was pressed, or 0 if none was pressed
        """
        #log("agiWrapper.sayControl() called")
        return self.send(self._formatTextForTTS(Text)+'|'+IntKeys)

    def _formatTextForTTS(self, text):
        """ 
        Formats the specified text into the correct AGI command string for
        rendering with the configured text-to-speech (TTS) engine in Asterisk.
        Can be interrupted by a particular DTMF key if specified in the
        interrupt string. 
        
        @param text: The text to say using TTS.
        @type text: C{str}
        @return: The formatted AGI command.
        @rtype: C{str}
        """
        return 'EXEC ' + self.tts + ' "' + text.replace('\n',' ').replace('"','') + '"'
    
    def _convertDTMF(self, dtmf):
        """
        Removes the offset from the DTMF result returned by Asterisk.
        
        @param dtmf: Asterisk DTMF result
        @type dtmf: int
        @return: the proper DTMF digit
        @rtype: str
        """
        if dtmf == 42:  # asterisk (*)
            return '*'
        elif dtmf == 35:  # hash (#)
            return '#'
        elif dtmf == 0:
            return '0'
        else:
            return str(dtmf - 48)

    def sayDTMF(self, text, valid, maxTimeout):
        """
        Prompts the user via TTS to enter DTMF input. Can be interrupted.
        
        @param text: the prompt text to be spoken via TTS
        @type text: str
        @param valid: valid DTMF options to take as input
        @type valid: String
        @param maxTimeout: the number of milliseconds to wait for DTMF input,
        zero for no input
        @type maxTimeout: int
        @return: the DTMF result
        @rtype: int or str
        """
        # TTS with DTMF interrupt
               
        # TODO: Once current TTS supports DTMF interrupts, call it directly
        # For now first do TTS in buffer only mode, and use normal audio playback
        # on the rendered audio file 

        audioPrompt = self.renderText(text)
        
        result = self.playAudioControl(audioPrompt, valid)
        
        if result < 0:
            raise IOError, 'Failed to retrieve DTMF input (possible hangup)'
        
        # use maxTimeout as indicator if DTMF input is required
        if maxTimeout > 0: # require input
            if result > 0:
                return self._convertDTMF(result)
            else:
                # wait for DTMF after prompt
                result = self.getInput(Timeout=maxTimeout)
                #debug('AutosecIVR._sayDTMF: IVRInterface.getInput returned %s' % result)
                if result < 0:
                    raise IOError, 'Failed to retrieve DTMF input (possible hangup)'
                
                if result > 0:
                    return self._convertDTMF(result)
                else:
                    result = -1 # so that Dialog.run can select TIMEOUT
        else: # skip input
            
            if result > 0:
                result = self._convertDTMF(result)
            else:
                result = 0
            #result = 0 # so that Dialog.run can select GOTO
        
        return result # in Dialog.run format
    
    def playDTMF(self, filename, valid, maxTimeout, delayAfterInput=0):
        """
        Prompts the user via audio file playbaintKeysck to enter DTMF input. Can be
        interrupted. Falls back on saying the filename via TTS if the audio
        file does not exist.
        
        @param filename: the name of the audio file to be played back, including
        .gsm extension
        @type filename: str
        @param valid: valid DTMF options to take as input
        @type valid: String
        @param maxTimeout: the number of milliseconds to wait for DTMF input,
        zero for no input
        @type maxTimeout: int
        @param delayAfterInput: amount of time in seconds to wait after dtmf input
        @type delayAfterInput: int
        @return: the DTMF result as required for
        dialogScripting.dialog.Dialog.run:229-238 to work - less than zero for
        TIMEOUT, zero for GOTO and greater than zero (text) for the DTMF digit
        @rtype: int or str
        """
        # TODO: remove customized ivr interface methods (play_dtmf, say_dtmf, play_asr, say_asr)
        # once mobilIVR.ivr.fastagi.IVRInterface has been standardized
        text = filename.replace('_', ' ').partition('.')[0]
        
        # audio playback (with TTS fallback) with DTMF interrupt
        result = self.playAudioControl(filename=filename, intKeys=valid)
        playback_stop_time = datetime.datetime.now()
        #debug('AutosecIVR._playDTMF: IVRInterface.playAudioTTSControl returned %s' % result)
        if result < 0:
            raise IOError, 'Failed to retrieve DTMF input (possible hangup)'
        bargeIn = False
        # use maxTimeout as indicator if DTMF input is required
        if result > 0:
            inputTime = playback_stop_time
            time.sleep(delayAfterInput)
            bargeIn =  True
            return (self._convertDTMF(result),inputTime, bargeIn, playback_stop_time)
        elif maxTimeout > 0: # require input
            #if result > 0:
            #    return self._convertDTMF(result)
            #else:
                # wait for DTMF after prompt
                result = self.getInput(Timeout=maxTimeout)
                #debug('AutosecIVR._sayDTMF: IVRInterface.getInput returned %s' % result)
                if result < 0:
                    raise IOError, 'Failed to retrieve DTMF input (possible hangup)'
                
                if result > 0:
                    inputTime = datetime.datetime.now()
                    # default delay after input 
                    time.sleep(delayAfterInput)
                    return (self._convertDTMF(result),inputTime,bargeIn, playback_stop_time)
                else:
                    result = -1 # so that Dialog.run can select TIMEOUT
        else: # skip input
            result = 0 # so that Dialog.run can select GOTO
        
        return result # in Dialog.run format

    def playAudio(self, filename):
        """ Instructs Asterisk to play an audio file
        
        This command cannot be interrupted by the user.
        
        @param filename: The filename of the audio clip.
        
                         This should NOT contain the filename extension, and if it
                         is a relative filename, Asterisk will look for it
                         in /var/lib/asterisk/sounds (or wherever the system's
                         Asterisk installation places its own default sound files)
        @type filename: str
        
        @return: The result of the command (from Asterisk)
        """
        return self.playAudioControl(filename, '""')
    
    def playAudioControl(self, filename, intKeys):
        """ Same as playAudio(), but with interrupt keys <intkeys> defined
        
        @param intKeys: the keys (DTMF digits) that can be entered by the
                        user to interrupt audio playback, e.g. "123"
        @type intKeys: str
        
        @return: This function returns the dtmf digit that was pressed,
                 0 if none was pressed, and -1 if an error occurred
        """
        # This check requires asterisk-agi-audiotx to be installed on the Asterisk server
        #try:
        #    result = self.send(r'ISEXISTING SOUNDFILE '+filename)
        #except InvalidCommand:
            # asterisk-agi-audiotx is not installed on the remote Asterisk server
            # Note that we'll still attempt to play the file anyway, but we'll print a warning
            #print 'Error communicating with remote Asterisk'
            #print 'Check that AGI Audio File Transfer Addons (asterisk-agi-audiotx) is installed on the Asterisk host.'
            #print 'Reverting to local calls; thus all audio files must already be present on the Asterisk host.'
        #    pass
        #else:
        #    if result == -1:
                # The file does not exist on the remote Asterisk server; send it
        #        result = self.sendAudioFile(filename)
        #        if result != 0:
                    # Something went wrong
        #            print 'sendAudioFile FAILED, result:', result
        #            return result
        
        
        # check if the filename includes the extension, if so then strip the extension
        if filename.__contains__('.'):
            if len(intKeys) > 0:
                return self.send(r'STREAM FILE '+filename[:filename.rfind('.')]+' '+intKeys)
            else:
                return self.send(r'STREAM FILE '+filename[:filename.rfind('.')]+' '+'\"\"')
        else:
            if len(intKeys) > 0:
                return self.send(r'STREAM FILE ' + filename + ' ' +intKeys)
            else:
                return self.send(r'STREAM FILE ' + filename + ' ' + '\"\"')
    
    def sendAudioFile(self, filename):
        """ Uses asterisk-agi-audiotx to send a soundfile to a remote Asterisk box """
        result = self.send(r'PUT SOUNDFILE %s %d' % (filename, os.path.getsize(filename)))
        if result != 0:
            # Something went wrong;
            #  result==-11: Could not create directory 
            #  result==-10: Could not create file
            return result
        
        f = open(filename, 'rb')
        buff = f.read(57) # 57 bytes == 76 characters when base64-encoded
        while buff != '':
            data = base64.b64encode(buff)+'\n'
            self.wfile.write(data)
            print 'data (length: %d): "%s"' % (len(data), data)
            buff = f.read(57)
        f.close()
        return self.getResult()

    def getAudioFile(self, filename):
        """ Uses asterisk-agi-audiotx to get a soundfile from a remote Asterisk box """
        try:
            result, msg = self.send(r'GET SOUNDFILE %s' % filename, FullResult=True)
        except InvalidCommand:
            print 'Error communicating with remote Asterisk'
            print 'Check that AGI Audio File Transfer Addons (asterisk-agi-audiotx) is installed on the Asterisk host.'
            print 'Reverting to local calls; thus all audio files must already be present on the Asterisk host.'
            result = -3
        if result != 0:
            # Something went wrong;
            return result
        fileSize = int(msg[msg.find('size=')+5:])
        buff = ''
        while len(buff) < fileSize:
            data = self.rfile.readline()
            print 'read length:',len(data)
            if data.startswith('200'):
                # Failed - Asterisk sent an error result
                return int(data[data.find('result=')+7:])
            elif data != '':
                buff += base64.decodestring(data[:-1])
            else:
                # Failed - connection closed
                return -1
        f = open(filename, 'w')
        f.write(buff)
        f.close()
        return 0

    def playAudioTTS(self, filename, text):
        """ Same as playAudio(), but falling back on TTS if there is an error 
        
        @param text: The text string to say using TTS if audio playback fails
        @type text: str
        
        @return: The result of the command (from Asterisk)
        """
        result = self.playAudio(filename)
        if result < 0:
            return self.say(text)


    def playAudioTTSControl(self, filename, text, intKeys):
        """ Same as playAudioControl(), but falling back on TTS if there is an error 
        
        @param text: The text string to say using TTS if audio playback fails
        @type text: str
        
        @return: Returns the DTMF digit that was pressed, 0 if none was pressed, and -1 
                 if an error occurred
        @rtype: int
        """
        result = self.playAudioControl(filename, intKeys)
        if result < 0:
            return self.sayControl(text, intKeys)
        else:
            return result
    
    def playASR(self,audioFile,grammarName,recogTimeout=5000,bargeInDuration=100,consecutiveSpeechDuration=5000,\
                  silenceTimeout=1000):
        
        """
        Prompts a user for ASR input. A recorded audio file is played to prompt
        a user to provide speech input. Voice barge-in is also enabled to interrupt prompt playback.
        The recognised result is returned.

        @param audioFile: A recorded Audio file to be played
        @type audioFile:C{str}
        
        @param grammarName: The name of the grammar to be used by the
                            ASR server for this recognition session, check the server configuration for
                            the grammar name.
                                
        @type grammarName: C{str}
        @param recogTimeout: The amount of time in I{milliseconds} to wait
                                   for speech after the prompt has finished
                                   playing.
        @type recogTimeout: C{int}
        @param bargeInDuration: The duration of speech detected in the audio
                                stream in I{milliseconds} which will stop the
                                prompt playback.
        @type bargeInDuration: C{int}
        @param consecutiveSpeechDuration: The duration of consecutive speech in
                                          I{milliseconds} to capture once the
                                          user starts speaking.
        @type consecutiveSpeechDuration: C{int}
        @param silenceTimeout: The duration of silence in I{milliseconds} that will stop the recognizer  
                               waiting for speech after prompt playback.
        @type silenceTimeout: C{int}
        @return: see L{fastagi.IVRInterface.recognizeSpeech}
        """
        host = self.speechServerAddress[0]
        port = self.speechServerAddress[1]
        hyp = self.recognizeSpeech(host,port,audioFile,grammarName,recogTimeout,bargeInDuration,consecutiveSpeechDuration,
                                   silenceTimeout)

        return hyp


    def sayASR(self,text,grammarName,recogTimeout=5000,bargeInDuration=100,consecutiveSpeechDuration=5000,\
                  silenceTimeout=1000):
        
        """
        Prompts a user for ASR input. Text is rendered into an audio file which is played to prompt
        a user to provide speech input. Voice barge-in is also enabled to interrupt prompt playback.
        The recognised result is returned.

        @param text: A recorded Audio file to be played
        @type text:C{str}
        
        @param grammarName: The name of the grammar to be used by the
                            ASR server for this recognition session, check the server configuration for
                            the grammar name.
        @type grammarName: C{str}
        @param recogTimeout: The amount of time in I{milliseconds} to wait
                                   for speech after the prompt has finished
                                   playing.
        @type recogTimeout: C{int}
        @param bargeInDuration: The duration of speech detected in the audio
                                stream in I{milliseconds} which will stop the
                                prompt playback.
        @type bargeInDuration: C{int}
        @param consecutiveSpeechDuration: The duration of consecutive speech in
                                          I{milliseconds} to capture once the
                                          user starts speaking.
        @type consecutiveSpeechDuration: C{int}

        @param silenceTimeout: The duration of silence in I{milliseconds} that will stop the recognizer  
                               waiting for speech after prompt playback.
        @type silenceTimeout: C{int}
        @return: see L{fastagi.IVRInterface.recognizeSpeech}
        """
        
        promtAudio = self.renderText(text)
        host = self.speechServerAddress[0]
        port = self.speechServerAddress[1]
        hyp= self.recognizeSpeech(host,port,promtAudio,grammarName,recogTimeout,bargeInDuration,consecutiveSpeechDuration,
                                   silenceTimeout)
        
        return hyp

    def recognizeSpeech(self, host, port, promptFilename, grammarName, recognitionTimeout=5000, \
                        bargeInDuration=100, consecutiveSpeechDuration=5000, silenceTimeout=1000):       
        """
        Performs automatic speech recognition (ASR) on the incoming audio stream
        while playing an audio prompt in the background. If speech is detected
        during the playback, the prompt will stop playing after a certain amount
        of speech has been captured.
        
        @param host: The IP address of the ASR server.
        @type host: C{str}
        @param port: The port of the ASR server.
        @type port: C{str}    
        @param promptFilename: The name of the audio file to be played,
                               I{including} its extension. The file must reside
                               locally in C{.../lib/asterisk/sounds}.
        @type promptFilename: C{str}
        @param grammarName: The name of the grammar to be used by the
                            ASR server for this recognition session, check the server configuration for
                            the grammar name.
        @type grammarName: C{str}
        @param recognitionTimeout: The amount of time in I{milliseconds} to wait
                                   for speech after the prompt has finished
                                   playing.
        @type recognitionTimeout: C{int}
        @param bargeInDuration: The duration of speech detected in the audio
                                stream in I{milliseconds} which will stop the
                                prompt playback.
        @type bargeInDuration: C{int}
        @param consecutiveSpeechDuration: The duration of consecutive speech in
                                          I{milliseconds} to capture once the
                                          user starts speaking.

        @param silenceTimeout: The duration of silence in I{milliseconds} that will stop the recognizer  
                               waiting for speech after prompt playback.
        @type silenceTimeout: C{int}
        @type consecutiveSpeechDuration: C{int}
        @return: Either (1) The ASR hypothesis tuple (recognized utterance, confidence level, confidence score); or
                        (2) -1 if nothing was recognized (e.g. silence)
        @rtype: Either (1) C{tuple} of (C{str}, c{fastAGIConstants.ASR_HIGH_CONFIDENCE} OR 
                           C{fastAGIConstants.ASR_LOW_CONFIDENCE}, c{float}); or
                       (2) c{int}
        """     
        rv = self.send('EXEC recognizer %s|%s|%s:%s|%s|%s|%s|%s' % 
                       (os.path.splitext(promptFilename)[0], bargeInDuration, host, port, \
                        grammarName, recognitionTimeout, consecutiveSpeechDuration, silenceTimeout))
        
        if rv < 0:
             # The recognizeSpeech application failed,the asterisk application - 
             # is either not installed or asterisk command failed.
            raise ExecuteCommandError, 'Asterisk ASR command failed. Check inter alia that the ASR server is running' + \
                                       ' and that you have provided a valid audio file and grammar name.'
        else:
            recognitionResult = self.getVariable('RECOGNITION_RESULTS')
            # NOTE: the parsing below assumes ATK return syntax
            # the rstrip is for the whitespace left after the last word
            recognitionResult = re.sub(r'(SILN|_SILN)\s?','', str(recognitionResult)).rstrip()
            recognitionResult = re.sub(r'(SIL|SENT-START|SENT-END|SIL-ENCE)\s?','', \
                                       str(recognitionResult)).rstrip() 
            recognitionResult = re.sub(r'(-ENCE)\s?','', str(recognitionResult)).rstrip()
            confidenceScore = float(self.getVariable('RECOGNITION_CONFIDENCE'))
            bargedIn = self.getVariable('RECOGNITION_BARGIN')
            bargeInFrame = self.getVariable('RECOGNITION_BARGINFRAME')

            # determine the confidence level based on the confidence score
            if confidenceScore > fastagi_constants.ASR_CONFIDENCE_THRESHOLD:
                confidenceLevel = fastagi_constants.ASR_HIGH_CONFIDENCE
            else:
                confidenceLevel = fastagi_constants.ASR_LOW_CONFIDENCE

            hyp = (recognitionResult, confidenceLevel, confidenceScore, bargedIn, bargeInFrame)            
                                     
            if hyp[0] == '':
                return -1
            else:
                return hyp
            

    def renderText(self, text):
        """
        Renders the specified text to an audio file using a text-to-speech (TTS)
        engine. The audio file I{is not played back}.
        
        @param text: The text to be rendered.
        @type text: C{str}
        @return: The name of the rendered audio file, I{including} its extension.
                 It will reside locally in C{.../lib/asterisk/sounds}.
        @rtype: C{str}
        """
        if self.tts.lower() != 'tts':
            #The application does not work for tts.
            raise InvalidCommand, 'IVRInterface.renderText only works for the ' + \
                  '"tts" application. The current application is: "%s".' % self.tts
        
        rv = self.send(self._formatTextForTTS(text) +'|bufferonly')
        if rv < 0:
              # The renedrText application failed,the asterisk application - 
             # is either not installed or asterisk command failed.
            raise ExecuteCommandError, 'Asterisk TTS command failed'
        
        # get the location of the rendered audio file on the Asterisk host
        filename = self.getVariable('TTS_FILENAME') # without extension
        if not filename:
              # TTS did not set the variable TTS_FILENAME,the asterisk application  might not been installed.
            raise ExecuteCommandError, 'TTS did not set the variable TTS_FILENAME'
        
        return filename + '.ulaw' # lwazi tts app for asterisk generates .ulaw files


    def recordAudio(self, filename, maxTime=-1, intKeys='#', playBeep=True, silenceTimeout=None,
                    custom_silence_detection=False):
        """ Record an audio clip, and store it on disk
        
        @note: The recorded file format is determined from the filename's
               extension, and defaults to "wav". Consult the Asterisk
               documentation for a list of supported file formats.
        
        @param filename: the name of the file in which to store the recorder audio clip
        @type filename: str
        @param maxTime: the maximum allowed length of the clip in milliseconds, -1 == infinite
        @type maxTime: int
        @param intKeys: a string containing all DTMF digits that would end the recording
        @type intKeys: str
        @param playBeep: if true, will cause a audible beep to be played just before recording starts
        @type playBeep: bool
        @param silenceTimeout: Duration of silence in seconds that will stop the recorder 
        @param custom_silence_detection: should custom silence detection be used or not
        @type custom_silence_detection: C{bool}           
        @return: The result from Asterisk
        @rtype: int
        """
        name, format = os.path.splitext(filename)
        if format == '':
            format = 'wav'
        else:
            format = format[1:] # exclude dot
        
        if len(intKeys) == 0:
            intKeys = '""'
        # Record the file
        playBeepField = ""
        if playBeep:
            playBeepField = " beep"
        
        silenceField = ""
        if silenceTimeout:
            silenceField = " s=" + str(silenceTimeout)
        
        final_res = None
        if not custom_silence_detection:
            result = self.send("RECORD FILE "+name+" "+format+" "+intKeys+" "+\
                                str(maxTime) + playBeepField + silenceField)
            final_res = (self.getAudioFile(filename), None, None)
        else:
            playBeepField = ''
            if not playBeep:
                playBeepField = '|q'
            result = self.send("EXEC RecordSD %s.%s|%s|%s%s" % 
                               (name, format, str(silenceTimeout), str(maxTime), playBeepField)) 
            silence_percentage = self.getVariable('SILENCE_PERCENTAGE') # without extension
            hash_termination = self.getVariable('HASH_TERMINATION')
            final_res = (self.getAudioFile(filename), silence_percentage, hash_termination)
        if result != 0:
            # Something went wrong
            return result
        # The recorderded file is located on the same (remote) host as the Asterisk server; get it
        return final_res
    
    def transfer(self, number, dialTimeout=None, announcementFilename=None, ringing=True):
        """
        Transfers the caller to this IVR to the callee at the specified number.
        The caller will hear music-on-hold while the transfer is in progress.
        
        @param number: The telephone number.
        @type number: C{str}
        @param dialTimeout: The amount of time to wait in I{milliseconds} before
                            the dial attempt times out.
        @type dialTimeout: C{int}
        @param announcementFilename: The name of the audio file, I{including}
                                     extension, to be played back as an
                                     announcement to the callee when he picks up.
        @type announcementFilename: C{str}
        @param ringing: Indicate a ringing tone to the calling party, defaults to C{True}
        @type ringing: C{bool}
        @return: A tuple of the dial status and duration in I{milliseconds} of
                 the bridged call. The duration is set to C{-1} if the call was
                 not bridged.
        @rtype: C{tuple} of (C{str}, C{int})
        """
        if dialTimeout:
            dialTimeout = '|%s' % (dialTimeout / 1000)
        else:
            dialTimeout = ''
        
        if announcementFilename:
            announcementFilename = 'A(%s)' % announcementFilename
        else:
            announcementFilename = ''
        
        ringopt = ''
        if ringing:
            ringopt = '|r'

        rv = self.send('EXEC Dial %s%s%s|m()%s' % (number, dialTimeout, ringopt, announcementFilename))
        
        status = self.getVariable('DIALSTATUS')
        time = self.getVariable('ANSWEREDTIME')
        if time == None:
            time = -1
        else:
            time = int(time) * 1000
        
        return (status, time)

    
    def channelIsActive(self):
        """ Queries Asterisk to find out if the channel is active 
        
        @return: True if the channel is active, or False if not
        @rtype: bool
        """
        
        status = self.send("CHANNEL STATUS")
        if status == 6:
            return True
        else:
            return False
        
    def getInput(self, Timeout = 50):
        """ Waits up to <Timeout> milliseconds for channel to receive a DTMF digit.
        
        @return: The digit pressed (as a character), or 0 if none was pressed, or <0 on failure 
        @rtype: int
        """
        return self.send(('WAIT FOR DIGIT '+str(Timeout)))
    
    def getInputString(self, MaxDigits = 0, Timeout = 50, delayAfterInput=0, audioFileName=''):
        """ 
        Prompts the user for input with an audio file and reads a string of DTMF digits from
        the channel. The string is terminated when hash (#) is pressed, or when <MaxDigits> is 
        reached.
        
        This is a wrapper for the Asterisk dialplan command:
        Read(variable[|filename][|maxdigits][|option][|attempts][|timeout])
        
        @param audioFilename: Audio file to prompt the user for input
        @type audioFilename: C{str}
        @param MaxDigits: Maximum amount of digits to read (0 == no limit)
        @type MaxDigits: int
        @param Timeout: Maximum time (in seconds) to wait for input
        @type Timeout: int
        @param delayAfterInput: Amount of time to wait after input of (maxDigits)
        
        @return: The DTMF digit string that was read (as a string),
                 or None if it failed
        @rtype: str
        """
        result = self.send('EXEC Read "InputString|%s|%d|||%d"' % (audioFileName, MaxDigits, Timeout))
        if result != -3:
            result, value = self.send('GET VARIABLE InputString', True)
            if result == -3:
                value = None
            else:
                value = value[1:-1]
            # Default delay after input
            time.sleep(delayAfterInput)
            return value
    
    def message(self, Text):
        """ Prints a message to the Asterisk CLI console
        
        @param Text: The text to print
        @type Text: str 
            
        @return: The result from Asterisk
        """
        return self.send('EXEC NOOP %s' % Text.encode('utf-8'))
        
    def setVariable(self, name, value):
        """ Sets an Asterisk internal variable
        
        @param name: The name of the variable to set
        @type name: str
        @param value: The value to which to set the variable
        @type value: str
        
        @return: The result from Asterisk
        """
        return self.send('SET VARIABLE %s %s' % (name, value))
    
    def getVariable(self, name):
        """ Gets an Asterisk internal (channel) variable
        
        @param name: The name of the variable to get, e.g. "myVar". This may
                     also be in the form of an Asterisk dialplan expression,
                     e.g. $[some expression] or ${myVar}
        @type name: str
        
        @return: The value of the variable (as returned by Asterisk), or None
                 if it was not found
        @rtype: str or None
        """
        if name[0] == '$':
            cmd = 'GET FULL VARIABLE'
        else:
            cmd = 'GET VARIABLE'
        result = self.send('%s %s' % (cmd, name), True)
        if type(result) == tuple:
            # Remove the brackets from either side of the result
            value = result[1][1:-1]
        else:
            value = None
        return value
        
    def runLocalSystemCommand(self, command):
        """ runs a system command on the local Asterisk machine
            @param command: the system command, eg, scp 
        """
        return self.send('EXEC System ' + command)
