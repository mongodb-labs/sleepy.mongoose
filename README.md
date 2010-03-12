# Sleepy.Mongoose

Sleepy.Mongoose is a REST interface for MongoDB.  

## PREREQUISITES

MongoDB and pymongo.  You can get MongoDB from http://www.mongodb.org.

You can install pymongo with easy_install:

    $ sudo easy_install pymongo

## RUNNING

Start the server by running:

      $ python httpd.py

## DOCUMENTATION

There is a quick tutorial you can use to get started on 
[my blog](http://www.snailinaturtleneck.com/blog/2010/02/22/sleepy-mongoose-a-mongodb-rest-interface/).

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

Required arguments:

* `server=database_server` (string)

Optional arguments: none

Returns: `{"ok" : 1, "host" : hostname, "port" : port_num}`

Example:

Connecting to a mongod server running locally on port 27017.

    curl --data server=localhost:27017 'http://localhost:27080/_connect'

#### Inserts

    http://localhost:27080/dbname/cname/_insert

Inserts one or more documents into a collection.

Required arguments:

* `docs=array_of_docs` (array of objects)

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

* `criteria=criteria_for_update` (object)
* `newobj=modifications` (object)

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

* `criteria=criteria_for_removal` (object)

Returns: `{"ok" : 1}`

Example:

Remove all documents where the "x" field is 2.

    curl --data 'criteria={"x":2}' 'http://localhost:27080/foo/bar/_remove'

TODO: just one, safe mode

## TODO

There's all sorts of things that need doing interspersed with the doc above.
Also needed are: 

* Honey bunches of helpers: _ensure_index, _command (which is done but not 
doc-ed), listing databases, listing collections, dropping things
* Handlers to get $oid, $date, etc. into a proper BSON types


## TROUBLESHOOTING

If anything goes wrong, please email the MongoDB user list 
(http://groups.google.com/group/mongodb-user).

