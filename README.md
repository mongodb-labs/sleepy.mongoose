# Sleepy.Mongoose

Sleepy.Mongoose is a REST interface for MongoDB.  

## PREREQUISITES

MongoDB and pymongo.  You can get MongoDB from http://www.mongodb.org.

You can install pymongo with easy_install:

    $ sudo easy_install pymongo

Sleepy.Mongoose requires pymongo version 1.4 or greater.

## RUNNING

Start the server by running:

      $ python httpd.py

Command line flags: 

* `-d` or `--docroot` allows you to specify the location of your files.  Defaults 
  to this directory.

## DOCUMENTATION

There is a quick tutorial you can use to get started on 
[my blog](http://www.snailinaturtleneck.com/blog/2010/02/22/sleepy-mongoose-a-mongodb-rest-interface/).

Sleepy.Mongoose only uses GETs and POSTs right now.

URIs are of the form: `/db_name/collection_name/_command`

Commands are always prefixes by underscores.  

An example: to find all documents in the collection "users" in the database
"website", you would use the following:

    http://localhost:27080/website/users/_find

You should make sure any options are URL escaped. You can easily do this with
any JavaScript shell, including the mongo shell.

For example, to query for `{"x" : 1}`, we have the string `'{"x" : 1}'`.  We run
`escape('{"x" : 1}')` and get `"%7B%22x%22%20%3A%201%7D"`.  We can now paste this beautful
string into our URL:

    http://localhost:27080/website/users/_find?criteria=%7B%22x%22%20%3A%201%7D

`{'x' : 1}` is valid JSON, but unfortunately, the Python JSON parser doesn't 
think so.  You must always use double quotes around keys, e.g., this is valid:
`{"x" : 1}`.

### Connections

Sleepy.Mongoose can create multiple connections to the same (or different) 
database servers by labelling each connection.  If no name parameter is passed
to `_connect`, the connection is labelled `default` and that connection is used
in subsequent commands (that do not specify a different host).

   curl http://localhost:27080/_connect # connects to localhost:27017 (A)
   curl --data 'name=backup' http://localhost:27080/_connect # creates another connection (B)

   curl http://localhost:27080/_find # uses A
   curl http://localhost:27080/_find?name=backup # uses B

### GET Requests

#### Hello, world

    http://localhost:27080/_hello

Basically a no-op that just makes sure the server is listening for connections.

Arguments: none

Returns: 

    {
        "ok" : 1, 
        "msg" : "Uh, we had a slight weapons malfunction, but uh... everything's
            perfectly all right now. We're fine. We're all fine here now, 
            thank you. How are you?"
    }


#### Queries

    http://localhost:27080/dbname/cname/_find

Query for documents.

Required arguments: none

Optional arguments:

* `criteria=search_criteria` (object)
* `fields=fields_to_return` (object)
* `sort=sort_fields` (object)
* `skip=num` (number)
* `limit=num` (number)
* `batch_size=num_to_return` (number)

Returns: `{"ok" : 1, "results" : [{...}, ... ], "id" : cursor_id}`

Examples:

Find all documents in the foo.bar namespace.

    curl -X GET 'http://localhost:27080/foo/bar/_find'

Find all documents in the foo.bar namespace and sort by x descending

    curl -X GET 'http://localhost:27080/foo/bar/_find?sort=%7B%22x%22%3A-1%7D'

#### Get More Results

    http://localhost:27080/_more

Get more results from an existing cursor.

Required arguments:

* `id=cursor_id` (number)

Optional arguments:

* `batch_size=num_to_return` (number)

Returns: `{"ok" : 1, "results" : [{...}, ... ], "id" : cursor_id}`

Example:

Get one more result from a cursor.

    curl -X GET 'http://localhost:27080/foo/bar/_more?id=1&batch_size=1'


### POST Requests

#### Connecting

    http://localhost:27080/_connect

Inserts one or more documents into a collection.  No database or collection
name is necessary.

If no arguments are given, it tries to connect to "localhost:27017".

Optional arguments: none

* `server=database_server` (string)

Returns: `{"ok" : 1, "host" : hostname, "port" : port_num}` on success,
`{"ok" : 0, "errmsg" : "could not connect", "host" : hostname, "port" : port_num}`
on failure.

Example:

Connecting to a mongod server running locally on port 27017.

    curl --data server=localhost:27017 'http://localhost:27080/_connect'

#### Inserts

    http://localhost:27080/dbname/cname/_insert

Inserts one or more documents into a collection.

Required arguments:

* `docs=array_of_docs` (array of objects)

Optional arguments:

* `safe=boolean` (0 or 1)

Returns: 

    {
        "status" : {
            "ok" : 1,
            "err" : null,
            "n" : 0
        }
        "oids" : [
            {"$oid" : doc1_id},
            {"$oid" : doc2_id},
            ...
        ]
    }

docX_id is a string representation of the inserted id, e.g., 
"4b9fad111d41c82cae000000".  The "status" field will only be included if you
specify "safe".

Example:

Inserting two documents (`{"x" : 2}` and `{"x" : 3}`) into the namespace foo.bar.

    curl --data 'docs=[{"x":2},{"x":3}]' 'http://localhost:27080/foo/bar/_insert'

#### Updates

    http://localhost:27080/dbname/cname/_update

Updates an existing document.

Required arguments:

* `criteria=criteria_for_update` (object)
* `newobj=modifications` (object)

Optional arguments: 

* `upsert=bool`
* `multi=bool`
* `safe=bool`

Returns: If `safe` is `false`, 

    {"ok" : 1}

If `safe` is `true`

    {"ok" : X, "n" : N, "err" : msg_or_null}

Example:

Increments a field.

    curl --data 'criteria={"x":1}&newobj={"$inc":{"x":1}}' 'http://localhost:27080/foo/bar/_update'

#### Removes

    http://localhost:27080/dbname/cname/_remove

Removes documents from a collection.

Required arguments: none

Optional arguments:

* `criteria=criteria_for_removal` (object)
* `safe=bool` (1 or 0)

Returns: `{"ok" : 1}`

Example:

Remove all documents where the "x" field is 2.

    curl --data 'criteria={"x":2}' 'http://localhost:27080/foo/bar/_remove'

#### Commands

     http://localhost:27080/dbname/_cmd

Runs a database command.

Required arguments:

* `cmd=cmd_obj` (object)

Returns: database response

Example:

Drop the 'bar' collection in the 'foo' database:

     curl --data 'cmd={"drop" : "bar"}' 'http://localhost:27080/foo/_cmd'

## TODO

There's all sorts of things that need doing interspersed with the doc above.
Also needed are: 

* Honey bunches of helpers: _ensure_index, listing databases, listing 
collections, dropping things
* Handlers to get $oid, $date, etc. into a proper BSON types

## TESTS

To run the tests, you must install restclient:

    $ easy_install restclient

Then run:

    $ python t/get.py
    $ python t/post.py


## TROUBLESHOOTING

If anything goes wrong, please email the MongoDB user list 
(http://groups.google.com/group/mongodb-user).

