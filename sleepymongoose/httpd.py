# Copyright 2009-2010 10gen, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from SocketServer import BaseServer
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from handlers import MongoHandler

try:
    from OpenSSL import SSL
except ImportError:
    pass

import os.path, socket
import urlparse
import cgi
import getopt
import sys

try:
    import json
except ImportError:
    import simplejson as json

# support python 2.5 (parse_qs was moved from cgi to urlparse in python 2.6)
try:
    urlparse.parse_qs
except AttributeError:
    urlparse.parse_qs = cgi.parse_qs



class MongoServer(HTTPServer):

    pem = None

    def __init__(self, server_address, HandlerClass):
        BaseServer.__init__(self, server_address, HandlerClass)
        ctx = SSL.Context(SSL.SSLv23_METHOD)

        fpem = MongoServer.pem
        ctx.use_privatekey_file(fpem)
        ctx.use_certificate_file(fpem)
        
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                        self.socket_type))
        self.server_bind()
        self.server_activate()


class MongoHTTPRequest(BaseHTTPRequestHandler):

    mimetypes = { "html" : "text/html",
                  "htm" : "text/html",
                  "gif" : "image/gif",
                  "jpg" : "image/jpeg",
                  "png" : "image/png",
                  "json" : "application/json",
                  "css" : "text/css",
                  "js" : "text/javascript",
                  "ico" : "image/vnd.microsoft.icon" }

    docroot = "."
    mongos = []
    response_headers = []
    jsonp_callback = None;

    def _parse_call(self, uri):
        """ 
        this turns a uri like: /foo/bar/_query into properties: using the db 
        foo, the collection bar, executing a query.

        returns the database, collection, and action
        """
        parts = uri.split('/')

        # operations always start with _
        if parts[-1][0] != '_':
            return (None, None, None)

        if len(parts) == 1:
            return ("admin", None, parts[0])
        elif len(parts) == 2:
            return (parts[0], None, parts[1])
        else:
            return (parts[0], ".".join(parts[1:-1]), parts[-1])


    def call_handler(self, uri, args):
        """ execute something """

        (db, collection, func_name) = self._parse_call(uri)
        if db == None or func_name == None:
            self.send_error(404, 'Script Not Found: '+uri)
            return

        name = None
        if "name" in args:
            if type(args).__name__ == "dict":
                name = args["name"][0]
            else:
                name = args.getvalue("name")

        self.jsonp_callback = None
        if "callback" in args:
            if type(args).__name__ == "dict":
                self.jsonp_callback = args["callback"][0]
            else:
                self.jsonp_callback = args.getvalue("callback")
                
        func = getattr(MongoHandler.mh, func_name, None)
        if callable(func):
            self.send_response(200, 'OK')
            self.send_header('Content-type', MongoHTTPRequest.mimetypes['json'])
            for header in self.response_headers:
                self.send_header(header[0], header[1])
            self.end_headers()

            if self.jsonp_callback:
                func(args, self.prependJSONPCallback, name = name, db = db, collection = collection)
            else:
                func(args, self.wfile.write, name = name, db = db, collection = collection)

            return
        else:
            self.send_error(404, 'Script Not Found: '+uri)
            return            
        
    def prependJSONPCallback(self, str):
        jsonp_output = '%s(' % self.jsonp_callback + str + ')'
        self.wfile.write( jsonp_output )
        
    # TODO: check for ..s
    def process_uri(self, method):
        if method == "GET":
            (uri, q, args) = self.path.partition('?')
        else:
            uri = self.path
            if 'Content-Type' in self.headers:
                args = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                                        environ={'REQUEST_METHOD':'POST',
                                                 'CONTENT_TYPE':self.headers['Content-Type']})
            else:
                self.send_response(100, "Continue")
                self.send_header('Content-type', MongoHTTPRequest.mimetypes['json'])
                for header in self.response_headers:
                    self.send_header(header[0], header[1])
                self.end_headers()
                self.wfile.write('{"ok" : 0, "errmsg" : "100-continue msgs not handled yet"}')

                return (None, None, None)


        uri = uri.strip('/')

        # default "/" to "/index.html"
        if len(uri) == 0:
            uri = "index.html"

        (temp, dot, type) = uri.rpartition('.')
        # if we have a collection name with a dot, don't use that dot for type
        if len(dot) == 0 or uri.find('/') != -1:
            type = ""

        return (uri, args, type)


    def do_GET(self):        
        (uri, args, type) = self.process_uri("GET")

 
        # serve up a plain file
        if len(type) != 0:
            if type in MongoHTTPRequest.mimetypes and os.path.exists(MongoHTTPRequest.docroot+uri):

                fh = open(MongoHTTPRequest.docroot+uri, 'r')

                self.send_response(200, 'OK')
                self.send_header('Content-type', MongoHTTPRequest.mimetypes[type])
                for header in self.response_headers:
                    self.send_header(header[0], header[1])
                self.end_headers()
                self.wfile.write(fh.read())

                fh.close()

                return

            else:
                self.send_error(404, 'File Not Found: '+uri)

                return

        # make sure args is an array of tuples
        if len(args) != 0:
            args = urlparse.parse_qs(args)
        else:
            args = {}

        self.call_handler(uri, args)
        #self.wfile.write( self.path )

    def do_POST(self):
        (uri, args, type) = self.process_uri("POST")
        if uri == None:
            return
        self.call_handler(uri, args)

    @staticmethod
    def serve_forever(port):
        print "\n================================="
        print "|      MongoDB REST Server      |"
        print "=================================\n"

        if MongoServer.pem == None:
            try:
                server = HTTPServer(('', port), MongoHTTPRequest)
            except socket.error, (value, message):
                if value == 98:
                    print "could not bind to localhost:%d... is sleepy.mongoose already running?\n" % port
                else:
                    print message
                return
        else:
            print "--------Secure Connection--------\n"
            server = MongoServer(('', port), MongoHTTPSRequest)

        MongoHandler.mh = MongoHandler(MongoHTTPRequest.mongos)
        
        print "listening for connections on http://localhost:27080\n"
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print "\nShutting down the server..."
            server.socket.close()
            print "\nGood bye!\n"


class MongoHTTPSRequest(MongoHTTPRequest):
    def setup(self):
        self.connection = self.request
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)


def usage():
    print "python httpd.py [-x] [-d docroot/dir] [-s certificate.pem] [-m list,of,mongods]"
    print "\t-x|--xorigin\tAllow cross-origin http requests"
    print "\t-d|--docroot\tlocation from which to load files"
    print "\t-s|--secure\tlocation of .pem file if ssl is desired"
    print "\t-m|--mongos\tcomma-separated list of mongo servers to connect to"


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "xd:s:m:", ["xorigin", "docroot=",
            "secure=", "mongos="])

        for o, a in opts:
            if o == "-d" or o == "--docroot":
                if not a.endswith('/'):
                    a = a+'/'
                MongoHTTPRequest.docroot = a
            if o == "-s" or o == "--secure":
                MongoServer.pem = a
            if o == "-m" or o == "--mongos":
                MongoHTTPRequest.mongos = a.split(',')
            if o == "-x" or o == "--xorigin":
                MongoHTTPRequest.response_headers.append(("Access-Control-Allow-Origin","*"))

    except getopt.GetoptError:
        print "error parsing cmd line args."
        usage()
        sys.exit(2)

    MongoHTTPRequest.serve_forever(27080)
if __name__ == "__main__":
    main()

