
/* logging */
QUnit.log = function(result, message)
{
    if (window.console && window.console.log)
        {
            window.console.log(result +' :: '+ message);
        }
}


module("Mongoose Tests");

var m = new Mongoose();

test("instance variables", function() {
        expect(4);

        equals(m.mongos, Mongoose.mongos.host+":"+Mongoose.mongos.port, "this.mongos");
        equals(m.httpd, Mongoose.httpd.host+":"+Mongoose.httpd.port, "this.mongos");

        var host2 = "example.com:123";
        var m2 = new Mongoose(host2);
        equals(m2.mongos, host2, "example host");

        Mongoose.mongos = {"host" : "example.net", "port" : 456};
        var m3 = new Mongoose();
        equals(m3.mongos, Mongoose.mongos.host+":"+Mongoose.mongos.port, "set default host & port");
    });

test("error handling", function() {
        expect(14);

        var result = Mongoose.handleError();
        ok(result != null, "result exists");
        equals(result.ok, 0);
        equals(result.msg, "Something went very wrong. You'll probably need to restart the server.");

        result = Mongoose.handleError({'ok' : 0});
        ok(result != null, "result exists");
        equals(result.ok, 0);
        equals(result.msg, null);

        result = Mongoose.handleError({'ok' : 0, 'msg' : 'whoops'});
        ok(result != null, "result exists");
        equals(result.ok, 0);
        equals(result.msg, 'whoops');

        result = Mongoose.handleError({'ok' : 0, 'errmsg' : 'whoops'});
        ok(result != null, "result exists");
        equals(result.ok, 0);
        equals(result.msg, 'whoops');

        result = Mongoose.handleError({'ok' : 1});
        ok(result != null, "result exists");
        equals(result.ok, 1);
    });


var testSetMongos = function(msg) {
    test("set mongos", function() {
            expect(3);

            equals(msg.ok, 1, "add mongos succeeded");
            equals(msg.host, "localhost", "host");
            equals(msg.port, 27017, "port");
        });
};
m.setMongos(testSetMongos);


var testGetConfig = function(msg) {
    test("get config", function() {
            expect(2);

            equals(msg.configserver, "localhost:20000");
            equals(msg.isdbgrid, 1);
        });
};
m.getConfig(testGetConfig);

var addShards = true;

var testGetShards0 = function(msg) {
    test("get shards 0", function() {
            expect(1);

            // no shards yet
            ok(msg.shards.constructor == Array);
            if (msg.shards.length == 2) {
                addShards = false;
            }
        });
};
m.getShards(testGetShards0);

module("Mongoose Shards");

shard0 = new Mongoose.Shard(m, "localhost:10000");

test("shard instance vars", function() {
        expect(2);

        equals(shard0.server, "localhost:10000");
        equals(shard0.connection.httpd, "http://localhost:27080");
    });

var testAddShard = function(msg) {
    test("add shard", function() {
            expect(1);

            equals(msg.added, "localhost:10000");
        });
};

if (addShards) {
    shard0.add(true, testAddShard);
}

var testGetShards1 = function(msg) {
    test("get shards 1", function() {
            expect(2);

            // no shards yet
            ok(msg.shards.constructor == Array);
            equals(msg.shards[0].host, "localhost:10000");
        });
};
m.getShards(testGetShards1);

shard1 = new Mongoose.Shard(m, "localhost:10001");

if (addShards) {
    shard1.add(true);
}

var testGetShards2 = function(msg) {
    test("get shards 2", function() {
            expect(4);

            // no shards yet
            ok(msg.shards.constructor == Array);
            equals(msg.shards.length, 2);
            equals(msg.shards[0].host, "localhost:10000");
            equals(msg.shards[1].host, "localhost:10001");
        });
};
m.getShards(testGetShards2);

var testStatus = function(msg) {
    test("get status", function() {
            expect(4);

            equals(typeof msg.uptime, "number");
            equals(typeof msg.globalLock.totalTime, "number");
            equals(typeof msg.globalLock.lockTime, "number");
            equals(typeof msg.globalLock.ratio, "number");
            // and so on
        });
};
shard0.status(testStatus);
shard1.status(testStatus);

var testGetDBs = function(msg) {
    test("get dbs", function() {
            expect(2);

            ok(msg.dbs.constructor == Array);
            equals(msg.dbs.length, 0);
        });
};
shard0.getDatabases(testGetDBs);
shard1.getDatabases(testGetDBs);





module("Mongoose Databases");

db = new Mongoose.Database(m, "foo");

var testDBShard = function(msg) {
    test("enable db sharding", function() {
            expect(1);

            equals(msg.ok, 1);
        });
}
db.shard(testDBShard);

var testMoveDB = function(msg) {
    test("move db", function() {
            expect(1);

            ok(/localhost:1000[01]/.test(msg.primary));
        });
}

var testGetDBs2 = function(msg) {
    test("get dbs", function() {
            expect(2);

            equals(msg.dbs.constructor, Array);
            equals(msg.dbs.length, 1);

            if (!msg.dbs[0].partitioned) {
                return;
            }

            var sdb = new Mongoose.Database(m, msg.dbs[0].name);

            var primary = msg.dbs[0].primary;
            var to = (shard0.server == primary) ? shard1.server : shard0.server;

            sdb.move(to, testMoveDB);
        });
};
shard0.getDatabases(testGetDBs2);
shard1.getDatabases(testGetDBs2);




module("Mongoose Collections");

c = new Mongoose.Collection(db, "bar");

test("instance vars", function() {
        expect(1);
        equals(c.ns, "foo.bar");
    });


