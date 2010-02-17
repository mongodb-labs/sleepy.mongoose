### PREREQUISITES

install easy-install:

    $ sudo apt-get install python-setuptools

install pymongo:

    $ sudo easy_install pymongo

### RUNNING

1. Change to the sharding tool directory
2. Run: 
      $ python httpd.py
3. Go to localhost:27080

### TROUBLESHOOTING

If anything goes wrong, please email the MongoDB user list 
(http://groups.google.com/group/mongodb-user).

### TESTS

There is a suite of tests in this test/ directory.  To run the tests, run the 
following:

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

### DOC

Everything should be documented with various degrees of thoroughness.  You can
see the documentation by opening doc/index.html in a web browser.


