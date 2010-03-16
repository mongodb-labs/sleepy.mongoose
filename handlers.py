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

from pymongo import Connection, json_util, ASCENDING, DESCENDING
from pymongo.son import SON
from pymongo.errors import ConnectionFailure, OperationFailure

import re
import json

class MongoHandler:

    _cursor_id = 0

    def _get_connection(self, name = None, host = None, port = None):
        if name == None:
            name = "default"

        connection = getattr(self, name, None)
        if connection != None or host == None:
            return connection

        if port == None:
            port = 27107

        try:
            connection = Connection(host, port)
        except ConnectionFailure:
            return None

        setattr(self, name, connection)
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


    def _get_son(self, str, out):
        try:
            obj = json.loads(str)
        except (ValueError, TypeError):
            out('{"ok" : 0, "errmsg" : "couldn\'t parse json: %s"}' % str)
            return None

        if getattr(obj, '__iter__', False) == False:
            out('{"ok" : 0, "errmsg" : "type is not iterable: %s"}' % str)
            return None
            
        # can't deserialize to an ordered dict!
        if '$pyhint' in obj:
            temp = SON()
            for pair in obj['$pyhint']:
                temp[pair['key']] = pair['value']
            obj = temp

        return obj


    def _cmd(self, db, collection, args, out):
        conn = self._get_connection()
        if conn == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongo"}')
            return

        cmd = self._get_son(args.getvalue('cmd'), out)
        if cmd == None:
            return

        result = conn[db].command(cmd, check=False)

        # debugging
        if result['ok'] == 0:
            result['cmd'] = args.getvalue('cmd')

        out(json.dumps(result, default=json_util.default))
        

    def _dbs(self, db, collection, args, out):
        """Get a list of databases for a shard.

        This is a GET request, so args is just a dict.
        """

        connection = self._get_connection('mongos')
        if connection == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongos"}')
            return

        cursor = connection.config.databases.find({"primary" : args['server'][0]})
        result = {"ok" : 1, "dbs" : list(cursor)}

        out(json.dumps(result, default=json_util.default))


    def _status(self, db, collection, args, out):
        """ Get the status of a shard server.
        This command operated on an individual mongod instance, as opposed to
        the commands above, which generally operate on the mongos instance.

        This is a GET request, so args is just a dict.
        """
        connection = getattr(self, args['server'][0], None)

        if connection == None:
            (host, port) = self._get_host_and_port(args['server'][0])
            self._get_connection(args['server'][0], host, port)

        if connection == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongos"}')
            return

        result = connection[db].command({"serverStatus" : 1}, check=False)
        if result != None:
            out(json.dumps(result, default=json_util.default))

    def _hello(self, db, collection, args, out):
        out('{"ok" : 1, "msg" : "Uh, we had a slight weapons malfunction, but ' + 
            'uh... everything\'s perfectly all right now. We\'re fine. We\'re ' +
            'all fine here now, thank you. How are you?"}')
        return
        

    def _connect(self, db, collection, args, out):
        """
        connect to a mongod
        """

        if "server" in args:
            (host, port) = self._get_host_and_port(args.getvalue('server'))
        else:
            host = "localhost"
            port = 27017

        name = "default"
        if "name" in args:
            name = args.getvalue("name")

        conn = self._get_connection(name, host, port)
        if conn != None:
            out('{"ok" : 1, "host" : "%s", "port" : %d}' % (host, port))
        else:
            out('{"ok" : 0, "errmsg" : "could not connect", "host" : "%s", "port" : %d}' % (host, port))


    def _find(self, db, collection, args, out):
        """
        query the database.
        """

        if db == None or collection == None:
            out('{"ok" : 0, "errmsg" : "db and collection must be defined"}')
            return            

        conn = self._get_connection()
        if conn == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongo"}')
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

        skip = 0
        if 'limit' in args:
            limit = int(args['limit'][0])

        limit = 0
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


    def _more(self, db, collection, args, out):
        """
        Get more results from a cursor
        """

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
        except StopIteration:
            # this is so stupid, there's no has_next?
            pass
        
        out(json.dumps({"results" : batch, "id" : cursor.id, "ok" : 1}, default=json_util.default))


    def _insert(self, db, collection, args, out):
        """
        insert a doc
        """

        conn = self._get_connection()
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
            safe = bool(args.getvalue("safe"));

        result = {}
        result['oids'] = conn[db][collection].insert(docs)
        if safe:
            result['status'] = conn[db].last_status()

        out(json.dumps(result, default=json_util.default))

    def _update(self, db, collection, args, out):
        """
        update a doc
        """

        if db == None or collection == None:
            out('{"ok" : 0, "errmsg" : "db and collection must be defined"}')
            return            

        conn = self._get_connection()
        if conn == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongo"}')
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
        
        conn[db][collection].update(criteria, newobj)
        out('{"ok" : 1}')

    def _remove(self, db, collection, args, out):
        """
        remove docs
        """

        if db == None or collection == None:
            out('{"ok" : 0, "errmsg" : "db and collection must be defined"}')
            return            

        conn = self._get_connection()
        if conn == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongo"}')
            return
        
        criteria = {}
        if "criteria" in args:
            criteria = self._get_son(args.getvalue('criteria'), out)
            if criteria == None:
                return
        
        conn[db][collection].remove(criteria)
        out('{"ok" : 1}')

