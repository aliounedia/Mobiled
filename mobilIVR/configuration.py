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

Provides a method to Parse a Kannel SMS gateway configuration file, and returns a dict with its values, and a
method to parse an Asterisk IVR gateway configuration file, and returns a dict with its values
"""

from ConfigParser import SafeConfigParser

def parseSMSConfig(filename):
    """ Parses Kannel SMS gateway configuration file, and returns a dict with its values """
    config = SafeConfigParser()
    settings = {}
    try:
        config.readfp( open(filename) )
    except IOError:
        print 'No such configuration file: %s' % filename
    
    # Checks whether this node should be able to receive incoming SMSs from Kannel
    if config.has_option('receive', 'enabled'):
        rxEnabled = config.getboolean('receive', 'enabled')
    else:
        rxEnabled = False 
    if rxEnabled:
        settings['rx'] = {}
        if config.has_option('receive', 'port'):
            settings['rx']['port'] = config.getint('receive', 'port')
        else:
            settings['rx']['port'] = 4500
             
    if config.has_option('sendsms', 'enabled'):
        txEnabled = config.getboolean('sendsms', 'enabled')
    else:
        txEnabled = False
    if txEnabled:
        settings['tx'] = {}
        if config.has_option( 'sendsms', 'username' ):
            settings['tx']['username'] = config.get( 'sendsms', 'username' )
        else:
            settings['tx']['username'] = 'mobilIVR'
        if config.has_option( 'sendsms', 'password' ):
            settings['tx']['password'] = config.get( 'sendsms', 'password' )
        else:
            settings['tx']['password'] = 'mobilIVR'
        if config.has_option( 'sendsms', 'host' ):
            settings['tx']['host'] = config.get( 'sendsms', 'host' )
        else:
            settings['tx']['host'] = '127.0.0.1'
        if config.has_option( 'sendsms', 'port' ):
            settings['tx']['port'] = config.getint( 'sendsms', 'port' )
        else:
            settings['tx']['port'] = 13013
    return settings

def parseIVRConfig(filename):
    """ Parses Asterisk IVR gateway configuration file, and returns a dict with its values """
    config = SafeConfigParser()
    settings = {}
    try:
        config.readfp( open(filename) )
    except IOError:
        print 'No such configuration file: %s' % filename
    
    if config.has_option('general', 'fastagi_port'):
        settings['fastagi_port'] = config.getint('general', 'fastagi_port')
    else:
        settings['fastagi_port'] = 6500
    if config.has_option('general', 'default_tts'):
        settings['default_tts'] = config.get('general', 'default_tts')
    else:
        settings['default_tts'] = 'flite'
    
    # Checks whether this node should be able to receive incoming (and reroute) calls from Asterisk
    if config.has_option('incoming', 'enabled'):
        rxEnabled = config.getboolean('incoming', 'enabled')
    else:
        rxEnabled = False
    if rxEnabled:
        settings['rx'] = {}
    # Checks whether this node should advertise any locally-configured telephone lines capable of dialling out
    if config.has_option('outgoing', 'enabled'):
        txEnabled = config.getboolean('outgoing', 'enabled')
    else:
        txEnabled = False
    if txEnabled:
        settings['tx'] = {}
        if config.has_option( 'outgoing', 'channels' ):
            channels = config.get( 'outgoing', 'channels' ).split(',')
            settings['tx']['channels'] = channels
        else:
            settings['tx']['channels'] = ['Console/dsp']
        if config.has_option( 'outgoing', 'gateway_address' ):
            gateway_address = config.get( 'outgoing', 'gateway_address' )
            settings['tx']['gateway_address'] = gateway_address
        else:
            settings['tx']['gateway_address'] = None
        if config.has_option( 'outgoing', 'local_int_code' ):
            settings['tx']['localIntCode'] = config.get( 'outgoing', 'local_int_code' )
        else:
            settings['tx']['localIntCode'] = None
        if config.has_option( 'outgoing', 'int_dialout' ):
            settings['tx']['intDialout'] = config.get( 'outgoing', 'int_dialout' )
        else:
            settings['tx']['intDialout'] = None
        if config.has_option( 'outgoing', 'prefix' ):
            settings['tx']['prefix'] = config.get( 'outgoing', 'prefix' )
        else:
            settings['tx']['prefix'] = None
        if config.has_option( 'outgoing', 'internal_extension_length' ):
            settings['tx']['internal_extension_length'] = config.get( 'outgoing', 'internal_extension_length' )
        else:
            settings['tx']['internal_extension_length'] = None    
        if config.has_option( 'outgoing', 'host' ):
            settings['tx']['host'] = config.get( 'outgoing', 'host' )
        else:
            settings['tx']['host'] = 'localhost'
        if config.has_option( 'outgoing', 'port' ):
            settings['tx']['port'] = config.getint( 'outgoing', 'port' )
        else:
            settings['tx']['port'] = 5038
        if config.has_option( 'outgoing', 'username' ):
            settings['tx']['username'] = config.get( 'outgoing', 'username' )
        else:
            settings['tx']['username'] = 'mobilIVR'
        if config.has_option( 'outgoing', 'secret' ):
            settings['tx']['secret'] = config.get( 'outgoing', 'secret' )
        else:
            settings['tx']['secret'] = 'mobilIVR'
        if config.has_option('speech-server', 'speech_server_address'):
            settings['tx']['speech_server_address'] = config.get('speech-server', 'speech_server_address')
        else:
            settings['tx']['speech_server_address'] = '127.0.0.1'
        if config.has_option('speech-server', 'speech_server_port'):
            settings['tx']['speech_server_port'] = config.get('speech-server', 'speech_server_port')
        else:
            settings['tx']['speech_server_port'] = '9000'


    return settings
