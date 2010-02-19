# Sleepy.Mongoose

Sleepy.Mongoose is a REST interface for MongoDB.  

For a quick tutorial, see 
http://www.snailinaturtleneck.com/blog/2010/02/19/sleepy-mongoose-a-mongodb-rest-interface/.

### PREREQUISITES

Install easy-install:

    $ sudo apt-get install python-setuptools

Install pymongo:

    $ sudo easy_install pymongo

### RUNNING

Start the server by running:

      $ python httpd.py

### DOCUMENTATION

Start the server and go to http://localhost:27080/doc/symbols/Sleepy.Mongoose.html#constructor
to see documentation for http requests.

### TROUBLESHOOTING

If anything goes wrong, please email the MongoDB user list 
(http://groups.google.com/group/mongodb-user).

### MONGEESE

Mongeese is a JavaScript API for interacting with Mongo shards.  It is built
on Sleepy.Mongoose.

Up until now, the only way to administrate sharding was through undocumented
database functions.  Mongoose provide objects to represent the mongos process,
shards, databases, and collections.  Each of these objects have simple,
documented functions associated with them to interact with the database.

For more information, see the documentation in the doc/ directory.

### TESTS

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

