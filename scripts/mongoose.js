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

Sleepy.Mongoose.prototype = new Sleepy();

Sleepy.Mongoose.prototype.constructor = function(host) {
    this.server = host ? host : (Mongoose.server.host + ":" + Mongoose.server.port);

    if (connect !== false) {
        this.connect();
    }

    /**
     * Connects to a db server.
     *
     * @param {String} [name] name to give connection
     * @param {function} [callback] optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.connect = function(name, callback) {
        var args = "server="+this.server;
        if (name && typeof name == "string") {
            args += "&name="+name;
        }

        this.post("/_connect", args, callback);
    }

    this._doOp = function(op, action, db, collection, fields, callback) {
        args = [];

        for (var key in fields) {
            if (typeof fields[key] == "object") {
                args.push(key+"="+escape($.toJSON(this._pyhint(fields[key]))));
            }
            else {
                args.push(key+"="+fields[key]);
            }
        }

        this[action]("/"+db+"/"+collection+"/"+op, args.join("&"), callback);
    }

    /**
     * Query the database.
     * Options can include:
     * <dl>
     *  <dt>criteria : <em>object</em></dt>
     *  <dd>criteria for which to search</dd>
     *  <dt>fields : <em>object</em></dt>
     *  <dd>fields of results to return (_id is always returned)</dd>
     *  <dt>limit : <em>N</em></dt>
     *  <dd>number of results to return</dd>
     *  <dt>skip : <em>N</em></dt>
     *  <dd>number of results to skip</dd>
     *  <dt>batch_size : N</dt>
     *  <dd>number of results returned in the fields batch (defaults to 15)</dd>
     * </dl>
     *
     * The callback receives an object of the form:
     * <pre>
     * {"results" : [], "id" : N, "ok" : 1}
     * </pre>
     * You must keep track of the id returned if you want to get more 
     * results from this query. 
     *
     * @param {string} db database name
     * @param {string} collection collection name
     * @param {object} [options] optional options for query
     * @param {function} [callback] callback to execute
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.find(db, collection, options, callback) {
        this._doOp("_find", "get", db, collection, options, callback);
    }

    /**
     * Get more results from a cursor.
     * Options must include:
     * <dl>
     *  <dt>id : <em>N</em></dt>
     *  <dd>the id for this query (from the find)</dd>
     * </dl>
     *
     * Options may include:
     * <dl>
     *  <dt>batch_size : <em>N</em></dt>
     *  <dd>number of results returned in the fields batch (defaults to 15)</dd>
     * </dl>
     *
     * The callback receives an object of the form:
     * <pre>
     * {"results" : [], "id" : N, "ok" : 1}
     * </pre>
     * You must keep track of the id returned if you want to get more 
     * results from this query. 
     *
     * @param {string} db database name
     * @param {string} collection collection name
     * @param {object} options options for getting more results
     * @param {function} [callback] callback to execute
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.more(db, collection, options, callback) {
        this._doOp("_more", "get", db, collection, options, callback);
    }

    /**
     * Delete objects from a collection
     *
     * Options may include:
     * <dl>
     *  <dt>criteria : <em>object</em></dt>
     *  <dd>criteria for removing objects</dd>
     * </dl>
     *
     * The callback receives an object of the form:
     * <pre>
     * {"ok" : 1}
     * </pre>
     *
     * @param {string} db database name
     * @param {string} collection collection name
     * @param {object} [options] options for getting more results
     * @param {function} [callback] callback to execute
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.remove(db, collection, options, callback) {
        this._doOp("_remove", "post", db, collection, options, callback);
    }

    /**
     * Get more results from a cursor.
     * Options must include:
     * <dl>
     *  <dt>criteria : <em>object</em></dt>
     *  <dd>criteria to find objects to update</dd> 
     *  <dt>newobj : <em>object</em></dt>
     *  <dd>update to perform</dd>
     * </dl>
     *
     * The callback receives an object of the form:
     * <pre>
     * {"ok" : 1}
     * </pre>
     *
     * @param {string} db database name
     * @param {string} collection collection name
     * @param {object} options options for getting more results
     * @param {function} [callback] callback to execute
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.update(db, collection, options, callback) {
        this._doOp("_update", "post", db, collection, options, callback);
    }

    /**
     * Get more results from a cursor.
     * Options must include:
     * <dl>
     *  <dt>docs : <em>array</em></dt>
     *  <dd>an array of objects to insert</dd> 
     * </dl>
     *
     * The callback receives an object of the form:
     * <pre>
     * {"ok" : 1}
     * </pre>
     *
     * @param {string} db database name
     * @param {string} collection collection name
     * @param {object} options options for getting more results
     * @param {function} [callback] callback to execute
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.insert(db, collection, options, callback) {
        this._doOp("_insert", "post", db, collection, options, callback);
    }

    /**
     * Execute a database command.
     *
     * @param {string} db database name
     * @param {object} obj the command to execute
     * @param {function} [callback] optional function to call when a response is
     * received.
     * @return undefined
     * @throws Exception if callback is not a function
     */
    this.command = function(db, obj, callback) {
        uri = "/_cmd";
        if (db && typeof db == "string") {
            uri = "/" + db + uri;
        }
        this.post(uri, "obj="+escape($.toJSON(this._pyhint(obj))), callback);
    }
};

/**
 * The default host an port to use if the constructor is not passed a server
 * name.  This is an object with fields "host" (string) and "port" (number).
 */
Mongoose.server = { host : "localhost", port : 27017 };

