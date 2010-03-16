from restclient import GET, POST

import json
import unittest

class TestPOST(unittest.TestCase):

    def setUp(self):
        POST("http://localhost:27080/_connect")
        self._drop_collection()

    def _drop_collection(self):
        str = POST("http://localhost:27080/test/_cmd",
                   params = {'cmd' : '{"drop" : "mongoose"}'})

    def test_insert_err1(self):
        str = POST("http://localhost:27080/_insert",
                   params = {'docs' : '[{"foo" : "bar"}]'},
                   async = False )

        self.assertEquals(type(str).__name__, "str")

        obj = json.loads(str)

        self.assertEquals(obj['ok'], 0)
        self.assertEquals(obj['errmsg'], 'db and collection must be defined')

    def test_insert_err2(self):
        str = POST("http://localhost:27080/test/_insert",
                   params = {'docs' : '[{"foo" : "bar"}]'},
                   async = False )

        self.assertEquals(type(str).__name__, "str")

        obj = json.loads(str)

        self.assertEquals(obj['ok'], 0)
        self.assertEquals(obj['errmsg'], 'db and collection must be defined')

    def test_insert_err3(self):
        str = POST("http://localhost:27080/test/mongoose/_insert",
                   async = False )

        self.assertEquals(type(str).__name__, "str")

        obj = json.loads(str)

        self.assertEquals(obj['ok'], 0)
        self.assertEquals(obj['errmsg'], 'missing docs')

    def test_insert(self):
        str = POST("http://localhost:27080/test/mongoose/_insert",
                   params = {'docs' : '[{"foo" : "bar"}]'},
                   async = False )

        self.assertEquals(type(str).__name__, "str")

        obj = json.loads(str)

        self.assertEquals(type(obj['oids'][0]['$oid']).__name__, "unicode")

    def test_safe_insert(self):
        str = POST("http://localhost:27080/test/mongoose/_insert",
                   params = {'docs' : '[{"foo" : "bar"}]', 'safe' : 1},
                   async = False )

        self.assertEquals(type(str).__name__, "str")

        obj = json.loads(str)

        self.assertEquals(type(obj['oids'][0]['$oid']).__name__, "unicode")
        self.assertEquals(obj['status']['ok'], 1)
        self.assertEquals(obj['status']['err'], None)

    def test_safe_insert_err1(self):
        str = POST("http://localhost:27080/test/mongoose/_insert",
                   params = {'docs' : '[{"_id" : "bar"}, {"_id" : "bar"}]', 'safe' : 1},
                   async = False )

        self.assertEquals(type(str).__name__, "str")

        obj = json.loads(str)

        self.assertEquals(obj['status']['ok'], 1)
        self.assertEquals(obj['status']['code'], 11000)

if __name__ == '__main__':
    unittest.main()
