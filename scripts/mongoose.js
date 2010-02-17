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

/*
 * This is the JavaScript sharding API
 *
 * It can be used by web interfaces to easily interact with the sharding 
 * backend.
 */

/*
 * Creates a new instance connected to a mongos.
 * @constructor
 * @param {String} host the hostname and optionally port number of the mongos.
 * If none is given, it will default to 
 * <i>mongoose.host</i>:<i>mongoose.port</i>.
 */
var Mongoose = function(host) {
    this.mongos = host ? host : (Mongoose.mongos.host + ":" + Mongoose.mongos.port);
    this.httpd = Mongoose.httpd.host + ":" + Mongoose.httpd.port;

    /*
     * Number of seconds/time unit
     * [sec/year, sec/month, sec/day, sec/hour, sec/minute]
     */
    var time_vals = [31104000, 2592000, 86400, 3600, 60];

    /*
     * Pretty names for time units
     */
    var time_units = ['year', 'month', 'day', 'hour', 'minute'];

    /*
     * Pretty names for byte units
     */
    var byte_units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'];

    /*
     * Turn number of seconds into a "pretty" time representation: years, 
     * months, days, etc.
     *
     * @param {Number} time number of seconds
     * @return the prettified time
     * @type String
     */
    get_time_format = function(time) {
        str = "";

        remaining = time;
        for (var i in time_vals) {
            if ((num = Math.floor(remaining/time_vals[i])) > 0) {
                str += num + " " + time_units[i] + (num == 1 ? "" : "s") + " ";
                remaining = remaining - (time_vals[i] * num);
            }
        }

        if (remaining > 0) {
            str += remaining + " seconds";
        }

        return str;
    };

    /*
     * Get the "pretty' size.
     * Uses the fact that sizes are measured base-10 as a hack.
     *
     * @param {Number} bytes size in bytes
     * @returns prettified size
     * @type String
     */
    var get_byte_format = function(bytes) {
        var size = Math.floor(((bytes+"").length-1)/3);
        bytes = bytes/Math.pow(1000, size);
        return bytes + " " + byte_units[size];
    }


    /*
     * This creates an AJAX request.  It sends an asynchronous request to
     * the server and calls an optional callback when a response is received, if
     * no error occured.
     *
     * @param {String} uri the address to send the request
     * @param {String} data key/value pairs to send
     * @param {callback} function a function to call when the response is 
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this._ajax = function(action, uri, data, callback) {
        if (callback === undefined) {
            callback = Mongoose.defaultCallback;
        }
        else if (typeof callback != "function") {
            throw "callback is not a function";
        }

        $.ajax({
                "type" : action,
                "url" : this.httpd+uri,
                "data" : data,
                "dataType" : "json",
                "success" : function(msg) {
                    var result = Mongoose.handleError(msg);
                    if (result.ok == 0) {
                        return;
                    }

                    callback(msg);
                },
                // TODO: better error handling
                "error" : function(request, status, err) {
                    Mongoose.handleError(err);
                }
            });
    }

    /*
     * This creates a POST AJAX request.  It sends an asynchronous request to
     * the server and calls an optional callback when a response is received, if
     * no error occured.
     *
     * @param {String} uri the address to send the request
     * @param {String} data key/value pairs to send
     * @param {callback} function a function to call when the response is 
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.post = function(uri, data, callback) {
        this._ajax("POST", uri, data, callback);
    };

    /*
     * This creates a GET AJAX request.  It sends an asynchronous request to
     * the server and calls an optional callback when a response is received, if
     * no error occured.
     *
     * @param {String} uri the address to send the request
     * @param {String} data key/value pairs to send
     * @param {callback} function a function to call when the response is 
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.get = function(uri, data, callback) {
        this._ajax("GET", uri, data, callback);
    };

    /*
     * Execute a database command.
     *
     * @param {object} obj the command to execute
     * @param {function} callback optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.command = function(obj, callback) {
        this.post("/_cmd", "obj="+escape($.toJSON(obj)), callback);
    }

    /*
     * Sets the mongos to use.
     *
     * @param {String} server the mongos server to use
     * @param {function} callback optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.setMongos = function(callback) {
        this.post("/_mongos", "server="+this.mongos, callback);
    };

    /*
     * Get the configuration server.
     *
     * @param {function} callback optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.getConfig = function(callback) {
        this.command({"netstat" : 1}, callback);
    };

    /*
     * Get a list of shards.
     *
     * @param {function} callback optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.getShards = function(callback) {
        this.command({"listshards" : 1}, callback);
    };
}


/*
 * A MongooseShard is an individual shard in the cluster.  It must be added to 
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
 */
Mongoose.Shard = function(mongoose, server) {

    this.connection = mongoose;
    this.server = server;

    /*
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
        this.connection.command({'$pyhint' : [{"key" : "addshard", "value" : this.server}, 
                                              {"key" : "allowLocal", "value" : local}]}, callback);
    };

    /*
     * Not yet implemented (in the db).
     */
    this.remove = function() {
        // TODO
    }

    /*
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

    /*
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

Mongoose.Database = function(mongoose, db) {
    this.connection = mongoose;
    this.db = db + "";
    
    /*
     * Enables sharding on a database.
     *
     * @param {String} db the database to enable sharding on
     * @param {function} callback optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.shard = function(callback) {
        this.connection.command({"enablesharding" : this.db}, callback);
    };

    /*
     * Move the database to a different shard.
     *
     * @param {String} to the server to move the database to
     * @param {function} callback optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.move = function(to, callback) {
        this.connection.command({'$pyhint' : [{"key" : "moveprimary", "value" : this.db},
                                              {"key" : "to", "value" : to}]}, callback);
    }
};

Mongoose.Collection = function(db, collection) {
    this.connection = db.connection;
    this.ns = db.db + "." + collection;

    /*
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
        this.connection.command({'$pyhint' : [{"key" : "shardcollection", "value" : this.ns},
                                              {"key" : "key", "value" : key}, 
                                              {"key" : "unique", "value" : unique}]}, callback);
    };

    /*
     * Split this collection into two chunks on a single shard.  Use 
     * MongooseCollection.move to move one of the chunks to a new shard.
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

        var cmd = {'$pyhint' : [{"key" : "shard", "value" : this.ns}]};

        if (criteria.find != null) {
            cmd.$pyhint[1] = {"key" : "find", "value" : criteria.find};
        }
        else if (criteria.middle != null) {
            cmd.$pyhint[1] = {"key" : "middle", "value" : criteria.middle};
        }
        else {
            throw "no find or middle object given";
        }

        this.connection.command(cmd, callback);
    };

    /*
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
     * @throws Exception if criteria doesn't contain "find" or "middle" fields 
     * or callback is not a function
     */
    this.move = function(criteria, to, callback) {
        var cmd = {'$pyhint' : [{"movechunk" : this.ns}]};

        if (criteria.find != null) {
            cmd.$pyhint.push({"key" : "find", "value" : criteria.find});
        }
        else {
            throw "no find object given";
        }
        cmd.$pyhint.push({"key" : "to", "value" : to + ""});

        this.connection.command(cmd, callback);
    };

    /*
     * Get the version of sharding being used.
     *
     * @param {function} callback optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.version = function(callback) {
        this.connection.command({"getShardVersion" : this.ns}, callback);
    };
}


Mongoose.mongos = { host : "localhost", port : 27017 };
Mongoose.httpd = { host : "http://localhost", port : 27080 };
Mongoose.defaultCallback = function(msg) { return; }

/*
 * Handles errors in database responses.
 * 
 * @returns an object.  If the "ok" field is 0, there will be a "msg" field 
 * that will describe the error that occured.  If the command succeeded (or
 * appeared to) the "ok" field will be 1.
 * @type Object
 */
Mongoose.handleError = function(msg) {
    if (!msg) {
        return {"ok" : 0, "msg" : "Something went very wrong. You'll probably need to restart the server."};
    }
    else if (!msg['ok']) {
        return {"ok" : 0, "msg" : msg['msg'] ? msg['msg'] : msg['errmsg']};
    }
    return {"ok" : 1};
};
