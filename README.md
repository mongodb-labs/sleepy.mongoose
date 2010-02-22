# Sleepy.Mongoose

Sleepy.Mongoose is a REST interface for MongoDB.  

For a quick tutorial, see 
http://www.snailinaturtleneck.com/blog/2010/02/19/sleepy-mongoose-a-mongodb-rest-interface/.

## PREREQUISITES

Install easy-install:

    $ sudo apt-get install python-setuptools

Install pymongo:

    $ sudo easy_install pymongo

## RUNNING

Start the server by running:

      $ python httpd.py

## DOCUMENTATION

Sleepy.Mongoose only uses GETs and POSTs right now.

URIs are of the form: `/db_name/collection_name/_command`

Commands are always prefixes by underscores.  

An example: to find all documents in the collection "users" in the database
"website", you would use the following:

    http://localhost:27080/website/users/_find


### GET Requests

#### Hello, world

    http://localhost:27080/_hello

Basically a no-op that just makes sure the server is listening for connections.

Arguments: none

Returns: `{"ok" : 1, "msg" : string}`

#### Queries

    http://localhost:27080/dbname/cname/_find

Query for documents.

Required arguments: none

Optional arguments:
* `criteria=search_criteria` (object)
* `fields=fields_to_return` (object)
* `skip=num` (number)
* `limit=num` (number)
* `batch_size=num_to_return` (number)

Returns: `{"ok" : 1, "results" : [{...}, ... ], "id" : cursor_id}`

Example:

Find all documents in the foo.bar namespace.

    curl -X GET 'http://localhost:27080/foo/bar/_find'

TODO: sort

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

Required arguments:
* `server=database_server`

Optional arguments: none

Returns: `{"ok" : 1, "host" : hostname, "port" : port_num}`

Example:

Connecting to a mongod server running locally on port 27017.

    curl --data server=localhost:27017 'http://localhost:27080/_connect'

#### Inserts

    http://localhost:27080/dbname/cname/_insert

Inserts one or more documents into a collection.

Required arguments:
* `docs=array_of_docs`

Optional arguments: none

Returns: `{"ok" : 1}`

Example:

Inserting two documents (`{"x" : 2}` and `{"x" : 3}`) into the namespace foo.bar.

    curl --data 'docs=[{"x":2},{"x":3}]' 'http://localhost:27080/foo/bar/_insert'

TODO: safe insert

#### Updates

    http://localhost:27080/dbname/cname/_update

Updates an existing document.

Required arguments:
* `criteria=criteria_for_update`
* `newobj=modifications`

Optional arguments: none

Returns: `{"ok" : 1}`

Example:

Increments a field.

    curl --data 'criteria={"x":1}&newobj={"$inc":{"x":1}}' 'http://localhost:27080/foo/bar/_update'

TODO: uperts, multiupdates, safe mode

#### Removes

    http://localhost:27080/dbname/cname/_remove

Removes documents from a collection.

Required arguments: none

Optional arguments:
* `criteria=criteria_for_removal`

Returns: `{"ok" : 1}`

Example:

Remove all documents where the "x" field is 2.

    curl --data 'criteria={"x":2}' 'http://localhost:27080/foo/bar/_remove'

TODO: just one, safe mode


## TROUBLESHOOTING

If anything goes wrong, please email the MongoDB user list 
(http://groups.google.com/group/mongodb-user).

## MONGOOSE

Mongoose is a JavaScript API for interacting with Mongo shards.  It is built
on Sleepy.Mongoose.

Up until now, the only way to administrate sharding was through undocumented
database functions.  Mongoose provide objects to represent the mongos process,
shards, databases, and collections.  Each of these objects have simple,
documented functions associated with them to interact with the database.

## TESTS

There is a suite of tests in this test/ directory.  

To run the tests you need two shards, one listening on port 10000 and the other
on port 10001.  You need a config server at port 20000 and a mongos instance at 
27017.

To start everything up, you can just run the following commands:

    $ mkdir -p ~/sharding/a ~/sharding/b ~/sharding/logs
    $
    $ mongod --dbpath ~/sharding/a --port 10000 > ~/sharding/logs/sharda.log &
    $ mongod --dbpath ~/sharding/b --port 10001 > ~/sharding/logs/shardb.log &
    $ mongod --dbpath ~/sharding/config --port 20000 > ~/sharding/logs/configdb.log &
    $
    $ mongos --configdb localhost:20000 > ~/sharding/logs/mongos.log &

Start the server (httpd.py) and point your browser at 
http://localhost:27080/test/index.html.  There are some issues with test
synchronization at the moment, so don't worry if they don't all pass.  On the 
other hand, some should.

