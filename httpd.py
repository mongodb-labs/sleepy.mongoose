from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from handlers import MongoHandler

import os.path
import urlparse
import json
import cgi

class MongoServer(BaseHTTPRequestHandler):

    mh = None

    mimetypes = { "html" : "text/html",
                  "htm" : "text/html",
                  "gif" : "image/gif",
                  "jpg" : "image/jpeg",
                  "png" : "image/png",
                  "json" : "text/json",
                  "css" : "text/css",
                  "js" : "text/js" }

    def call_handler(self, uri, args):
        # execute something
        func = getattr(MongoServer.mh, uri, None)
        if callable(func):
            self.send_response(200, 'OK')
            self.send_header('Content-type', MongoServer.mimetypes['json'])
            self.end_headers()

            func(args, self.wfile.write)

            return
        else:
            self.send_error(404, 'Script Not Found: '+uri)
            return            
        

    # TODO: check for ..s
    def process_uri(self, method):
        if method == "GET":
            (uri, q, args) = self.path.partition('?')
        else:
            uri = self.path

        uri = uri.strip('/')

        # default "/" to "/index.html"
        if len(uri) == 0:
            uri = "index.html"

        (temp, dot, type) = uri.rpartition('.')
        if len(dot) == 0:
            type = ""

        args = cgi.FieldStorage(fp=self.rfile, headers=self.headers)

        return (uri, args, type)


    def do_GET(self):        
        (uri, args, type) = self.process_uri("GET")

 
        # serve up a plain file
        if len(type) != 0:
            if type in MongoServer.mimetypes and os.path.exists(uri):

                fh = open(uri, 'r')

                self.send_response(200, 'OK')
                self.send_header('Content-type', MongoServer.mimetypes[type])
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
        self.call_handler(uri, args)


    @staticmethod
    def serve_forever(port):
        print "\n================================="
        print "| MongoDB Sharding Admin Server |"
        print "=================================\n"
        print "point your browser to http://localhost:27080\n"

        MongoServer.mh = MongoHandler()

        server = HTTPServer(('', port), MongoServer)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print "\nShutting down the server..."
            server.socket.close()
            print "\nGood bye!\n"


if __name__ == "__main__":
    MongoServer.serve_forever(27080)

