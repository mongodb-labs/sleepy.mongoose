from pymongo import Connection, json_util
from pymongo.son import SON
from pymongo.errors import ConnectionFailure

import re
import json

class MongoHandler:

    def _get_connection(self, name, host = None, port = None):
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


    def _cmd(self, args, out):
        connection = self._get_connection('mongos')
        if connection == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongos"}')
            return

        cmd = json.loads(args.getvalue('obj'))

        # can't deserialize to an ordered dict!
        if '$pyhint' in cmd:
            temp = SON()
            for pair in cmd['$pyhint']:
                temp[pair['key']] = pair['value']
            cmd = temp

        result = connection.admin._command(cmd)
        out(json.dumps(result, default=json_util.default))
        

    def _mongos(self, args, out):
        (host, port) = self._get_host_and_port(args.getvalue('server'))

        conn = self._get_connection('mongos', host, port)
        if conn != None:
            out('{"ok" : 1, "host" : "%s", "port" : %d}' % (host, port))
        else:
            out('{"errmsg" : "could not connect", "host" : "%s", "port" : %d}' % (host, port))

    def _dbs(self, args, out):
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


    def _status(self, args, out):
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

        result = connection.admin._command({"serverStatus" : 1})
        if result != None:
            out(json.dumps(result))

