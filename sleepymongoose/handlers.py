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

from bson.son import SON
from pymongo import Connection, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ConfigurationError, OperationFailure, AutoReconnect
from bson import json_util

import re
try:
    import json
except ImportError:
    import simplejson as json

class MongoHandler:
    mh = None

    _cursor_id = 0

    def __init__(self, mongos):
        self.connections = {}

        for host in mongos:
            args = MongoFakeFieldStorage({"server" : host})

            out = MongoFakeStream()
            if len(mongos) == 1:
                name = "default"
            else:
                name = host.replace(".", "") 
                name = name.replace(":", "")

            self._connect(args, out.ostream, name = name)
        
    def _get_connection(self, name = None, uri='mongodb://localhost:27017'):
        if name == None:
            name = "default"

        if name in self.connections:
            return self.connections[name]
        
        try:
            connection = Connection(uri, network_timeout = 2)
        except (ConnectionFailure, ConfigurationError):
            return None

        self.connections[name] = connection
        return connection

    def _get_host_and_port(self, server):
        host = "localhost"
        port = 27017

        if len(server) == 0:
            return (host, port)

        m = re.search('([^:]+):([0-9]+)?', server)
        if m == None:
            return (host, port)

        handp = m.groups()

        if len(handp) >= 1:
            host = handp[0]
        if len(handp) == 2 and handp[1] != None:
            port = int(handp[1])

        return (host, port)

    def sm_object_hook(obj):
        if "$pyhint" in obj:
            temp = SON()
            for pair in obj['$pyhint']:
                temp[pair['key']] = pair['value']
            return temp
        else:
            return json_util.object_hook(obj)


    def _get_son(self, str, out):
        try:
            obj = json.loads(str, object_hook=json_util.object_hook)
        except (ValueError, TypeError):
            out('{"ok" : 0, "errmsg" : "couldn\'t parse json: %s"}' % str)
            return None

        if getattr(obj, '__iter__', False) == False:
            out('{"ok" : 0, "errmsg" : "type is not iterable: %s"}' % str)
            return None
 
        return obj


    def _cmd(self, args, out, name = None, db = None, collection = None):
        if name == None:
            name = "default"

        conn = self._get_connection(name)
        if conn == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongo"}')
            return

        cmd = self._get_son(args.getvalue('cmd'), out)
        if cmd == None:
            return

        try:
            result = conn[db].command(cmd, check=False)
        except AutoReconnect:
            out('{"ok" : 0, "errmsg" : "wasn\'t connected to the db and '+
                'couldn\'t reconnect", "name" : "%s"}' % name)
            return
        except (OperationFailure, error):
            out('{"ok" : 0, "errmsg" : "%s"}' % error)
            return

        # debugging
        if result['ok'] == 0:
            result['cmd'] = args.getvalue('cmd')

        out(json.dumps(result, default=json_util.default))
        
    def _hello(self, args, out, name = None, db = None, collection = None):
        out('{"ok" : 1, "msg" : "Uh, we had a slight weapons malfunction, but ' + 
            'uh... everything\'s perfectly all right now. We\'re fine. We\'re ' +
            'all fine here now, thank you. How are you?"}')
        return
        
    def _status(self, args, out, name = None, db = None, collection = None):
        result = {"ok" : 1, "connections" : {}}

        for name, conn in self.connections.iteritems():
            result['connections'][name] = "%s:%d" % (conn.host, conn.port)

        out(json.dumps(result))
    
    def _connect(self, args, out, name = None, db = None, collection = None):
        """
        connect to a mongod
        """

        if type(args).__name__ == 'dict':
            out('{"ok" : 0, "errmsg" : "_connect must be a POST request"}')
            return

        if "server" in args:
            try:
                uri = args.getvalue('server')
            except Exception, e:
                print uri
                print e
                out('{"ok" : 0, "errmsg" : "invalid server uri given", "server" : "%s"}' % uri)
                return
        else:
            uri = 'mongodb://localhost:27017'

        if name == None:
            name = "default"

        conn = self._get_connection(name, uri)
        if conn != None:
            out('{"ok" : 1, "server" : "%s", "name" : "%s"}' % (uri, name))
        else:
            out('{"ok" : 0, "errmsg" : "could not connect", "server" : "%s", "name" : "%s"}' % (uri, name))

    def _authenticate(self, args, out, name = None, db = None, collection = None):
        """
        authenticate to the database.
        """

        if type(args).__name__ == 'dict':
            out('{"ok" : 0, "errmsg" : "_find must be a POST request"}')
            return

        conn = self._get_connection(name)
        if conn == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongo"}')
            return

        if db == None:
            out('{"ok" : 0, "errmsg" : "db must be defined"}')
            return

        if not 'username' in args:
            out('{"ok" : 0, "errmsg" : "username must be defined"}')

        if not 'password' in args:
            out('{"ok" : 0, "errmsg" : "password must be defined"}')
        
        if not conn[db].authenticate(args.getvalue('username'), args.getvalue('password')):
            out('{"ok" : 0, "errmsg" : "authentication failed"}')
        else:
            out('{"ok" : 1}')
        
    def _find(self, args, out, name = None, db = None, collection = None):
        """
        query the database.
        """

        if type(args).__name__ != 'dict':
            out('{"ok" : 0, "errmsg" : "_find must be a GET request"}')
            return

        conn = self._get_connection(name)
        if conn == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongo"}')
            return

        if db == None or collection == None:
            out('{"ok" : 0, "errmsg" : "db and collection must be defined"}')
            return            

        criteria = {}
        if 'criteria' in args:
            criteria = self._get_son(args['criteria'][0], out)
            if criteria == None:
                return

        fields = None
        if 'fields' in args:
            fields = self._get_son(args['fields'][0], out)
            if fields == None:
                return

        limit = 0
        if 'limit' in args:
            limit = int(args['limit'][0])

        skip = 0
        if 'skip' in args:
            skip = int(args['skip'][0])

        cursor = conn[db][collection].find(spec=criteria, fields=fields, limit=limit, skip=skip)

        sort = None
        if 'sort' in args:
            sort = self._get_son(args['sort'][0], out)
            if sort == None:
                return

            stupid_sort = []

            for field in sort:
                if sort[field] == -1:
                    stupid_sort.append([field, DESCENDING])
                else:
                    stupid_sort.append([field, ASCENDING])

            cursor.sort(stupid_sort)

        if 'explain' in args and bool(args['explain'][0]):
            out(json.dumps({"results" : [cursor.explain()], "ok" : 1}, default=json_util.default))


        if not hasattr(self, "cursors"):
            setattr(self, "cursors", {})

        id = MongoHandler._cursor_id
        MongoHandler._cursor_id = MongoHandler._cursor_id + 1

        cursors = getattr(self, "cursors")
        cursors[id] = cursor
        setattr(cursor, "id", id)

        batch_size = 15
        if 'batch_size' in args:
            batch_size = int(args['batch_size'][0])
            
        self.__output_results(cursor, out, batch_size)


    def _more(self, args, out, name = None, db = None, collection = None):
        """
        Get more results from a cursor
        """

        if type(args).__name__ != 'dict':
            out('{"ok" : 0, "errmsg" : "_more must be a GET request"}')
            return

        if 'id' not in args:
            out('{"ok" : 0, "errmsg" : "no cursor id given"}')
            return


        id = int(args["id"][0])
        cursors = getattr(self, "cursors")

        if id not in cursors:
            out('{"ok" : 0, "errmsg" : "couldn\'t find the cursor with id %d"}' % id)
            return

        cursor = cursors[id]

        batch_size = 15
        if 'batch_size' in args:
            batch_size = int(args['batch_size'][0])

        self.__output_results(cursor, out, batch_size)


    def __output_results(self, cursor, out, batch_size=15):
        """
        Iterate through the next batch
        """
        batch = []

        try:
            while len(batch) < batch_size:
                batch.append(cursor.next())
        except AutoReconnect:
            out(json.dumps({"ok" : 0, "errmsg" : "auto reconnecting, please try again"}))
            return
        except OperationFailure, of:
            out(json.dumps({"ok" : 0, "errmsg" : "%s" % of}))
            return
        except StopIteration:
            # this is so stupid, there's no has_next?
            pass
        
        out(json.dumps({"results" : batch, "id" : cursor.id, "ok" : 1}, default=json_util.default))


    def _insert(self, args, out, name = None, db = None, collection = None):
        """
        insert a doc
        """

        if type(args).__name__ == 'dict':
            out('{"ok" : 0, "errmsg" : "_insert must be a POST request"}')
            return

        conn = self._get_connection(name)
        if conn == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongo"}')
            return

        if db == None or collection == None:
            out('{"ok" : 0, "errmsg" : "db and collection must be defined"}')
            return

        if "docs" not in args: 
            out('{"ok" : 0, "errmsg" : "missing docs"}')
            return

        docs = self._get_son(args.getvalue('docs'), out)
        if docs == None:
            return

        safe = False
        if "safe" in args:
            safe = bool(args.getvalue("safe"))

        result = {}
        result['oids'] = conn[db][collection].insert(docs)
        if safe:
            result['status'] = conn[db].last_status()

        out(json.dumps(result, default=json_util.default))


    def __safety_check(self, args, out, db):
        safe = False
        if "safe" in args:
            safe = bool(args.getvalue("safe"))

        if safe:
            result = db.last_status()
            out(json.dumps(result, default=json_util.default))
        else:
            out('{"ok" : 1}')


    def _update(self, args, out, name = None, db = None, collection = None):
        """
        update a doc
        """

        if type(args).__name__ == 'dict':
            out('{"ok" : 0, "errmsg" : "_update must be a POST request"}')
            return

        conn = self._get_connection(name)
        if conn == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongo"}')
            return

        if db == None or collection == None:
            out('{"ok" : 0, "errmsg" : "db and collection must be defined"}')
            return
        
        if "criteria" not in args: 
            out('{"ok" : 0, "errmsg" : "missing criteria"}')
            return
        criteria = self._get_son(args.getvalue('criteria'), out)
        if criteria == None:
            return

        if "newobj" not in args:
            out('{"ok" : 0, "errmsg" : "missing newobj"}')
            return
        newobj = self._get_son(args.getvalue('newobj'), out)
        if newobj == None:
            return
        
        upsert = False
        if "upsert" in args:
            upsert = bool(args.getvalue('upsert'))

        multi = False
        if "multi" in args:
            multi = bool(args.getvalue('multi'))

        conn[db][collection].update(criteria, newobj, upsert=upsert, multi=multi)

        self.__safety_check(args, out, conn[db])

    def _remove(self, args, out, name = None, db = None, collection = None):
        """
        remove docs
        """

        if type(args).__name__ == 'dict':
            out('{"ok" : 0, "errmsg" : "_remove must be a POST request"}')
            return

        conn = self._get_connection(name)
        if conn == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongo"}')
            return

        if db == None or collection == None:
            out('{"ok" : 0, "errmsg" : "db and collection must be defined"}')
            return
        
        criteria = {}
        if "criteria" in args:
            criteria = self._get_son(args.getvalue('criteria'), out)
            if criteria == None:
                return
        
        result = conn[db][collection].remove(criteria)

        self.__safety_check(args, out, conn[db])

    def _batch(self, args, out, name = None, db = None, collection = None):
        """
        batch process commands
        """

        if type(args).__name__ == 'dict':
            out('{"ok" : 0, "errmsg" : "_batch must be a POST request"}')
            return

        requests = self._get_son(args.getvalue('requests'), out)
        if requests == None:
            return

        out("[")

        first = True
        for request in requests:
            if "cmd" not in request:
                continue

            cmd = request['cmd']
            method = "GET"
            if 'method' in request:
                method = request['method']
            
            db = None
            if 'db' in request:
                db = request['db']

            collection = None
            if 'collection' in request:
                collection = request['collection']

            args = {}
            name = None
            if 'args' in request:
                args = request['args']
                if 'name' in args:
                    name = args['name']

            if method == "POST":
                args = MongoFakeFieldStorage(args)

            func = getattr(MongoHandler.mh, cmd, None)
            if callable(func):
                output = MongoFakeStream()
                func(args, output.ostream, name = name, db = db, collection = collection)
                if not first:
                    out(",")
                first = False

                out(output.get_ostream())
            else:
                continue

        out("]")

        
class MongoFakeStream:
    def __init__(self):
        self.str = ""

    def ostream(self, content):
        self.str = self.str + content

    def get_ostream(self):
        return self.str

class MongoFakeFieldStorage:
    def __init__(self, args):
        self.args = args

    def getvalue(self, key):
        return self.args[key]

    def __contains__(self, key):
        return key in self.args
