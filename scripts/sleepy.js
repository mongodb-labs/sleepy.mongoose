/**
 * Sleepy.Mongoose is a JavaScript interface to MongoDB that is mainly
 * a proof-of-concept for the rest interface.
 *
 * REST protocol:
 * to connect, call:
 * /_connect
 *   host=hostname
 *   port=port
 * 
 * GETs
 * /dbname/collection/_query - query request
 *   criteria=&lt;search criteria&gt;
 *   skip=# to skip
 *   limit=# to return
 *   sort=sort obj
 *   batch_size=# of results to return at a time, defaults to 15
 * /dbname/collection/_more - get more results
 *   id=cursor id
 *
 * POSTs
 * /dbname/collection/_insert - insert request
 *   docs=&lt;an array of objs to insert&gt;
 *   opts=options
 * /dbname/collection/_delete - delete request
 *   criteria=&lt;criteria for deletion&gt;
 *   opts=options
 * /dbname/collection/_update - update request
 *   criteria=&lt;criteria for update&gt;
 *   newobj=&lt;update content&gt;
 *   opts=&lt;options&gt;
 *   
 * Special ops:
 * /_dbs - list of databases
 * /dbname/_cmd - database command on db dbname
 * /_cmd - database command on admin db
 *
 */

Sleepy = function(host, connect) {
    this.httpd = Sleepy.httpd.host + ":" + Sleepy.httpd.port;

    /**
     * This turns an object into an array of pairs so that Python won't mess up
     * the ordering.
     */
    this._pyhint = function(data) {
        var kv = [];
        for(var key in data) {
            kv.push({"key" : key, "value" : data[key]});
        }
        return {'$pyhint' : kv};
    }


    /**
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
            callback = Sleepy.defaultCallback;
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
                    var result = Sleepy.handleError(msg);
                    if (result.ok == 0) {
                        return;
                    }

                    callback(msg);
                },
                // TODO: better error handling
                "error" : function(request, status, err) {
                    Sleepy.handleError(err);
                }
            });
    }

    /**
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

    /**
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
};

Sleepy.httpd = { host : "http://localhost", port : 27080 };

Sleepy.defaultCallback = function(msg) { return; };

/**
 * Handles errors in database responses.
 * 
 * @returns an object.  If the "ok" field is 0, there will be a "msg" field 
 * that will describe the error that occured.  If the command succeeded (or
 * appeared to) the "ok" field will be 1.
 * @type Object
 */
Sleepy.handleError = function(msg) {
    if (!msg) {
        return {"ok" : 0, "msg" : "Something went very wrong. You'll probably need to restart the server."};
    }
    else if (!msg['ok']) {
        return {"ok" : 0, "msg" : msg['msg'] ? msg['msg'] : msg['errmsg']};
    }
    return {"ok" : 1};
};
