from pymongo import Connection, json_util
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
        handp = m.groups()

        if len(handp) >= 1:
            host = handp[0]
        if len(handp) == 2 and handp[1] != None:
            port = int(handp[1])

        return (host, port)


    def _get_son(self, str):
        obj = json.loads(str)

        # can't deserialize to an ordered dict!
        if '$pyhint' in obj:
            temp = SON()
            for pair in obj['$pyhint']:
                temp[pair['key']] = pair['value']
            obj = temp

        return obj


    def _cmd(self, db, collection, args, out):
        connection = self._get_connection('mongos')
        if connection == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongos"}')
            return

        cmd = self._get_son(args.getvalue('obj'))

        result = connection[db].command(cmd, check=False)
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
            out(json.dumps(result))

        
    def _connect(self, db, collection, args, out):
        """
        connect to a mongod
        """

        (host, port) = self._get_host_and_port(args.getvalue('server'))

        name = "default"
        if "name" in args:
            name = args.getvalue("name")

        conn = self._get_connection(name, host, port)
        if conn != None:
            out('{"ok" : 1, "host" : "%s", "port" : %d}' % (host, port))
        else:
            out('{"ok" : 0, "errmsg" : "could not connect", "host" : "%s", "port" : %d}' % (host, port))


    def _query(self, db, collection, args, out):
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
            criteria = self.get_son(args['criteria'][0])

        fields = None
        if 'fields' in args:
            fields = self.get_son(args['fields'][0])

        skip = 0
        if 'limit' in args:
            limit = int(args['limit'][0])

        limit = 0
        if 'skip' in args:
            skip = int(args['skip'][0])

        cursor = conn[db][collection].find(spec=criteria, fields=fields, limit=limit, skip=skip)

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

        cursors = getattr(self, "cursors")

        if not (id in args):
            out('{"ok" : 0, "errmsg" : "no cursor id given"}' % id)
            return

        id = args.getvalue("id")
        if not (id in cursors):
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

        if db == None or collection == None:
            out('{"ok" : 0, "errmsg" : "db and collection must be defined"}')
            return            

        conn = self._get_connection()
        if conn == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongo"}')
            return

        if "docs" not in args: 
            out('{"ok" : 0, "errmsg" : "missing docs"}')
            return
        docs = self._get_son(args.getvalue('docs'))

        conn[db][collection].insert(docs)

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
        criteria = self._get_son(args.getvalue('criteria'))

        if "newobj" not in args:
            out('{"ok" : 0, "errmsg" : "missing newobj"}')
            return
        newobj = self._get_son(args.getvalue('newobj'))
        
        conn[db][collection].update(criteria, newobj)

    def _delete(self, db, collection, args, out):
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
            criteria = self._get_son(args.getvalue('criteria'))
        
        conn[db][collection].remove(criteria)

