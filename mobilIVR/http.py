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

Provides Web-related utility functions for doing POST/GET requests
"""

import httplib, mimetypes
from urllib import urlencode

class HTTPPost:
    """ HTTP POST request wrapper """
    def __init__(self, Host, Port=80, Path=''):
        """ @param Host: the host to which to send the request
        @type Host: str
        @param Port: the port number on which the server is listening
        @type Port: int
        @param Path: The request, or pathname, on the host
        @type Path: str
        """
        self.host = Host
        self.port = Port
        self.path = Path
        # Data added. Format: {<field name> : <field data>}
        self.fields = {}
        # Files added. Format: {<field name> : (<file name>, <file data>)}
        self.files = {}
        

    def addFile(self, Field, Filename):
        """ Add a file to the HTTP POST transaction
        
        @param Field: The name of the field to use for the file's contents
        @type Field: str
        @param Filename: The name of the file to add
        @type Filename: str
        """
        fileEncoding = 'iso-8859-1'
        f = open(Filename, 'rb')
        self.files[Field] = (Filename, f.read().decode(fileEncoding))
        f.close()
    
    def addField(self, Field, Data):
        """ Add a field with specified data to the HTTP POST
        
        @param Field: Name of the field
        @type Field: str
        @param Data: The data to add to this field
        @type Data: str
        """
        self.fields[Field] = Data


    def post(self):
        """ Perform the POST request transaction """
        return self.postMultipart(self.host, self.port, self.path, self.fields, self.files, {})


    @staticmethod
    def postMultipart(Host, Port, Request, Fields, Files, AddHeaders={}): 
        """ Post fields and files to an HTTP host as multipart/form-data.
    
        @param Host: the host to which to send the request
        @type Host: str
        @param Port: the port number on which the server is listening
        @type Port: int
        @param Request: The request, or pathname, on the host
        @type Request: str
        @param Fields: a sequence of (name, value) tuples for regular form fields.
        @param Files: a sequence of (name, filename, value) tuples for data to be
                      uploaded as files
        @param AddHeaders: (optional) dictionary containing any additional HTTP
                           headers to include besides 'User-Agent' and 'Content-Type'
                            
        @return: the remote server's response code, and its response HTML page
        @rtype: tuple
        """
        contentType, body = HTTPPost.encodeMultipartFormData(Fields, Files)
        print contentType
        print body
        conn = httplib.HTTPConnection(Host, Port)  
        headers = {'User-Agent': 'Mozilla/5.0',
                   'Content-Type': contentType}
        headers.update(AddHeaders)
        conn.request('POST', Request, body.encode("iso-8859-1"), headers)
        response = conn.getresponse()
        conn.close()
        return response.status, response.read()
    
    
    @staticmethod
    def encodeMultipartFormData(Fields, Files):
        """ Encodes the specified data into HTTP mulipart/form-data

        @param Fields: a sequence of (name, value) tuples for regular form fields
        @type Fields: tuple
        @param Files: a sequence of (name, filename) tuples for data to be
                      uploaded as files
        @type Files: tuple
        
        @return: (content_type, body), ready for httplib.HTTP instance
        @rtype: tuple
        """
        BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$' #IGNORE:C0103
        CRLF = '\r\n' #IGNORE:C0103
        L = [] #IGNORE:C0103
        for (key, value) in Fields.items():
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        for (key, (filename, value)) in Files.items():
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % HTTPPost.getContentType(filename))
            L.append('')
            L.append(value)
        
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        contentType = 'multipart/form-data; boundary=%s' % BOUNDARY
        return contentType, body


    @staticmethod
    def getContentType(Filename):
        return mimetypes.guess_type(Filename)[0] or 'application/octet-stream'


class HTTPGet:
    """ HTTP GET wrapper """
    def __init__(self):
        pass

    @staticmethod
    def get(Host, Port, Request, Variables={}, AddHeaders={}):
        """ Does a HTTP GET request to the specified host/port
    
        @param Host : Host to connect to
        @type Host: str
        @param Port: Port to connect to
        @type Port: int
        @param Request: The request, or pathname, on the host
                        (should not contain url-encoded variables, etc)
        @type Request: str
        @param Variables: Variable names, and their values, to pass.
        
                          Format: {<name>: <value>}
        @type Variables: dict
        @param AddHeaders: Any additional HTTP headers to pass

                           Format: {<header name>: <value>}
        @type AddHeaders: dict
        """
        http = httplib.HTTPConnection(Host, Port)  
        headers = {'User-Agent': 'Mozilla/5.0'}
        headers.update(AddHeaders)
        varStr = urlencode(Variables)
        reqStr = Request + '?' + varStr
        http.request('GET', reqStr, '', headers)
        response = http.getresponse()
        msg = response.read()
        return response

