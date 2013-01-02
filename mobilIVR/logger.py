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

Provides a logging setup class
"""

import logging

def setupLogger(LoggerName="MobilIVR Logger", name="output.log", debug=True,
                     level = logging.DEBUG):
    """ Setup logger for the test driver. """
    #global mobilIVRLog
    try:
        fmt = "%(asctime)s [%(levelname)s] %(message)s"
        mobilIVRLog = logging.getLogger(name)
        formatter = logging.Formatter(fmt)
        # File output.
        ofstream = logging.FileHandler(name + ".log", "a")
        ofstream.setFormatter(formatter)
        mobilIVRLog.addHandler(ofstream)
        # Console output.
        console = logging.StreamHandler()
        mobilIVRLog.setLevel(level)
        console.setFormatter(formatter)
        mobilIVRLog.addHandler(console)
    except Exception, e:
        print "ERROR: Could not create logging instance.\n\tReason: %s" %e
        sys.exit(1)
    return mobilIVRLog


def closeLogFileHandler(mobilIVRLog):
    """
    Clean up the logger file handler. This should be called once logging to a file is completed in order 
    to prevent running out of file descriptors.
    """
    # get the handler, currently logging has no access method for this
    ofstream = mobilIVRLog.handlers[0]
    ofstream.flush()
    ofstream.close()
    mobilIVRLog.removeHandler(ofstream)
    

