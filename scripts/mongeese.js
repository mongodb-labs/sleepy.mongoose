/*
 * Copyright 2010 10gen, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */


/**
 * This is the JavaScript sharding API
 *
 * It can be used by web interfaces to easily interact with the sharding 
 * backend.
 * @name Mongeese 
 * @class 
 */
Mongeese = {};

Mongeese.prototype = new Sleepy.Mongoose();

/**
 * Sets the mongos to use.
 *
 * @param {String} server the mongos server to use
 * @param {function} [callback] optional function to call when a response is
 * received.
 * @return undefined
 * @throws Exception if callback is not a function
 */
Mongeese.prototype.setMongos = function(callback) {
    this.connect("mongos", callback);
};

/**
 * Get the configuration server.
 *
 * @param {function} callback optional function to call when a response is
 * received.
 * @return undefined
 * @throws Exception if callback is not a function
 */
Mongeese.prototype.getConfig = function(callback) {
    this.command("admin", {"netstat" : 1}, callback);
};

/**
 * Get a list of shards.
 *
 * @param {function} callback optional function to call when a response is
 * received.
 * @return undefined
 * @throws Exception if callback is not a function
 */
Mongeese.prototype.getShards = function(callback) {
    this.command("admin", {"listshards" : 1}, callback);
};


/**
 * A Mongeese.Shard is an individual shard in the cluster.  It must be added to 
 * the cluster manually by calling "add".
 *
 * So, here's the workflow:
 * <ol>
 *  <li>
 *   You have an existing shard server (mongos) and config server, plus zero or
 *   more existing shards.  You have an instance of Mongoose associated with the
 *   mongos running.
 *  </li>
 *  <li>
 *   You start up a new shard.  No one knows that this shard even exists yet.
 *   Say it is listening for connections at localhost:12345.
 *  </li>
 *  <li>
 *   You create a Mongoose.Shard instance for this shard, passing it the 
 *   Mongoose instance and the address of the shard ("localhost:12345").
 *  </li>
 *  <li>
 *   Finally, we let mongos and the config server know about this new shard by 
 *   calling the add method on this shard.
 *  </li>
 * </ol>
 *
 * @constructor
 */
Mongeese.Shard = function(mongeese, server) {

    this.connection = mongeese;
    this.server = server;

    /**
     * Add this shard.
     *
     * The callback will receive a response of the form:
     * <pre>
     * { "added" : "localhost:10000", "ok" : 1 }
     * </pre>
     *
     * If you do not specify local and the shard is on localhost, you will get:
     * <pre>
     * {
     *     "ok" : 0,
     *     "errmsg" : "can't use localhost as a shard since all shards need to communicate.  allowLocal to override for testing"
     * }
     * </pre>
     *
     * @param {boolean} [local] optional parameter specifying if the shard is on localhost
     * @param {function} [callback] optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.add = function(local, callback) {
        local = local ? true : false;
        this.connection.command("admin", {"addshard" : this.server, "allowLocal" : local}, callback);
    };

    /**
     * Not yet implemented (in the db).
     */
    this.remove = function() {
        // TODO
    }

    /**
     * Checks the status of this server, including uptime, memory usage, and 
     * activity.
     *
     * The callback will receive a response of the form:
     * <pre>
     * {
     *     "uptime" : 52358,
     *     "globalLock" : {
     *          "totalTime" : 52358205700,
     *          "lockTime" : 1455600,
     *          "ratio" : 0.000027800799904034907
     *     },
     *     "mem" : {
     *          "resident" : 22,
     *          "virtual" : 145,
     *          "supported" : true,
     *          "mapped" : 80
     *     },
     *     "connections" : {
     *          "current" : 2,
     *          "available" : 19998
     *     },
     *     "extra_info" : {
     *          "note" : "fields vary by platform",
     *          "heap_usage_bytes" : 1874632,
     *          "page_faults" : 1
     *     },
     *     "indexCounters" : {
     *          "btree" : {
     *              "accesses" : 1,
     *              "hits" : 1,
     *              "misses" : 0,
     *              "resets" : 0,
     *              "missRatio" : 0
     *          }
     *     },
     *     "opcounters" : {
     *          "insert" : 3,
     *          "query" : 15,
     *          "update" : 0,
     *          "delete" : 0,
     *          "getmore" : 0
     *     },
     *     "ok" : 1
     * }
     * </pre>
     *
     * @param {function} callback optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.status = function(callback) {
        this.connection.get("/_status", "server="+this.server, callback);
    };

    /**
     * Get a list of databases on this shard.
     *
     * @param {function} callback optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.getDatabases = function(callback) {
        this.connection.get("/_dbs", "server="+this.server, callback);
    };

}

/**
 * A sharded database.
 *
 * @constructor
 */
Mongeese.Database = function(mongeese, db) {
    this.connection = mongeese;
    this.db = db + "";
    
    /**
     * Enables sharding on a database.
     *
     * @param {String} db the database to enable sharding on
     * @param {function} callback optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.shard = function(callback) {
        this.connection.command("admin", {"enablesharding" : this.db}, callback);
    };

    /**
     * Move the database to a different shard.
     *
     * @param {String} to the server to move the database to
     * @param {function} callback optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.move = function(to, callback) {
        this.connection.command("admin", {"moveprimary" : this.db, "to" : to}, callback);
    }
};

/**
 * A sharded collection.  Used to manipulate individual chunks (pieces of a 
 * collection).
 *
 * @constructor
 */
Mongeese.Collection = function(db, collection) {
    this.connection = db.connection;
    this.ns = db.db + "." + collection;

    /**
     * Enables sharding on this collection.  The collection's database must have 
     * sharding enabled before it can be enabled on the collection.
     *
     * @param {object} key the field or fields on which to shard, e.g., {"x" : 1}
     * @param {boolean} [unique] if the shard key should be unique
     * @param {function} [callback] optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.shard = function(key, unique, callback) {
        unique = unique ? true : false;
        this.connection.command("admin", {"shardcollection" : this.ns, "key" : key, "unique" : unique}, callback);
    };

    /**
     * Split this collection into two chunks on a single shard.  Use 
     * Mongeese.Collection.move to move one of the chunks to a new shard.
     *
     * @param {object} criteria must contain "find" OR "middle" field which 
     * gives the split criteria.
     * @param {function} [callback] optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if criteria doesn't contain "find" or "middle" fields 
     * or callback is not a function
     */
    this.split = function(criteria, callback) {

        var cmd = {"shard" : this.ns};

        if (criteria.find != null) {
            cmd.find = criteria.find;
        }
        else if (criteria.middle != null) {
            cmd.middle = criteria.middle;
        }
        else {
            throw "no find or middle object given";
        }

        this.connection.command("admin", cmd, callback);
    };

    /**
     * Move a chunk of this collection to a new shard.  Use the criteria 
     * parameter to find the chunk to move.
     *
     * @param {object} criteria must contain "find" field which matches at least
     * one document in the chunk to move.
     * @param {string} to the shard to which to move the chunk, e.g., 
     * "localhost:27019"
     * @param {function} [callback] optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if criteria doesn't contain a "find" field
     * or callback is not a function
     */
    this.move = function(criteria, to, callback) {
        var cmd = {"movechunk" : this.ns};

        if (criteria.find != null) {
            cmd.find = criteria.find;
        }
        else {
            throw "no find object given";
        }
        cmd.to = to;

        this.connection.command("admin", cmd, callback);
    };

    /**
     * Get the version of sharding being used.
     *
     * @param {function} callback optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.version = function(callback) {
        this.connection.command("admin", {"getShardVersion" : this.ns}, callback);
    };
}


