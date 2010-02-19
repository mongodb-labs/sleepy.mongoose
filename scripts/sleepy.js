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
 * Sleepy is the basic REST JavaScript interface that Mongoose is build on top 
 * of.
 *
 * @constructor
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
