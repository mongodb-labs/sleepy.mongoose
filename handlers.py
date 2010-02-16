from pymongo import Connection, json_util
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


    def _run_command(self, server, cmd, out):
        connection = self._get_connection(server)
        if connection == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to %s"}' % server)
            return None 

        return connection.admin._command(cmd)
        

    def set_mongos(self, args, out):
        (host, port) = self._get_host_and_port(args['server'][0])

        conn = self._get_connection('mongos', host, port)
        if conn != None:
            out('{"ok" : 1, "host" : "%s", "port" : %d}' % (host, port))
        else:
            out('{"error" : "could not connect", "host" : "%s", "port" : %d}' % (host, port))

    def get_config(self, args, out):
        netstat = self._run_command('mongos', {'netstat' : 1}, out)

        # sharding versions prior to ~12/15 didn't have an ok field
        if netstat == None:
            return
        elif ('ok' in netstat and netstat['ok'] == 1) or 'configserver' in netstat:
            out('{"ok" : 1, "configserver" : "%s"}' % netstat['configserver'])
        else:
            out('{"ok" : 0, "errmsg" : "%s"}' % netstat['errmsg'])


    def get_shards(self, args, out):
        """ Gets a list of shards for this mongos config.
        Returns {"ok" : 1, "shards" : ["host1", "host2", ...]}
        """
        shardlist = self._run_command('mongos', {'listshards' : 1}, out)
        if shardlist == None:
            return
        if shardlist['ok'] != 1:
            out(json.dumps(shardlist))
            return

        shards = []
        for shard in shardlist['shards']:
            shards.append(shard['host'])

        out('{"ok" : 1, "shards" : %s}' % json.dumps(shards))


    def add_shard(self, args, out):
        """ Adds a shard.
        First, it tries just adding the shard.  If it comes back with "use allow
        local", it tries again, using allowLocal.  Returns the result of the 
        database command.
        """
        cmd = SON({"addshard" : args['server'][0]})
        add_shard = self._run_command('mongos', cmd, out)

        # if fail...
        if add_shard['ok'] != 1:
            # if the error message is complaining about localhost
            if add_shard['errmsg'].find('allowLocal') != -1:
                cmd['allowLocal'] = True
                add_shard2 = MongoHandler._run_command(self, 'mongos', cmd, out)

                # still failed
                if add_shard2['ok'] != 1:
                    out('{"ok" : 1, "error1" : %s, "error2" : %s}' % (json.dumps(add_shard), json.dumps(add_shard2)))
                    return
                
                add_shard = add_shard2

        out(json.dumps(add_shard))
        
    def remove_shard(self, args, out):
        """ Removes a shard.
        This isn't implemented in the database yet, so it'll just return an
        error message.
        """
        
        remove_shard = self._run_command('mongos', {'removeshard' : args['server'][0]}, out)
        out(json.dumps(remove_shard))

    def get_dbs(self, args, out):
        """Get a list of databases for a shard.
        """

        connection = self._get_connection('mongos')
        if connection == None:
            out('{"ok" : 0, "errmsg" : "couldn\'t get connection to mongos"}')
            return

        cursor = connection.config.databases.find({"primary" : args['host'][0]})
        result = {"ok" : 1, "dbs" : list(cursor)}

        out(json.dumps(result, default=json_util.default))


    def shard_db(self, args, out):
        """ Makes a database sharded.
        """
        
        enable_db = self._run_command('mongos', {'enablesharding' : args['db'][0]}, out)
        out(json.dumps(enable_db))

    def shard_collection(self, args, out):
        """ Makes a collection sharded.
        """
        
        enable_c = self._run_command('mongos', {'shardcollection' : args['ns'][0]}, out)
        out(json.dumps(enable_c))

    def move_chunk(self, args, out):
        """ This will move a chunk from one shard to another.  Requires from, 
        to, and find.
        """
        pass

    def get_status(self, args, out):
        """ Get the status of a shard server.
        This command operated on an individual mongod instance, as opposed to
        the commands above, which generally operate on the mongos instance.
        """
        connection = getattr(self, args['server'][0], None)

        if connection == None:
            (host, port) = self._get_host_and_port(args['server'][0])
            self._get_connection(args['server'][0], host, port)

        status = self._run_command(args['server'][0], {'serverStatus' : 1}, out)

        if status != None:
            out(json.dumps(status))

