from restclient import GET, POST

import json
import unittest

class TestGET(unittest.TestCase):

    def setUp(self):
        POST("http://localhost:27080/_connect", 
            params = {'server' : 'localhost:27017'})
        self._drop_collection()

    def _drop_collection(self):
        str = POST("http://localhost:27080/test/_cmd",
                   params = {'cmd' : '{"drop" : "mongoose"}'})

    def test_hello(self):
        str = GET("http://localhost:27080/_hello")

        self.assertEquals(type(str).__name__, "str")

        obj = json.loads(str)

        self.assertEquals(obj['ok'], 1)
        self.assertEquals(obj['msg'], "Uh, we had a slight weapons "+
                          "malfunction, but uh... everything's perfectly "+
                          "all right now. We're fine. We're all fine here "+
                          "now, thank you. How are you?")

    def test_find(self):
        POST("http://localhost:27080/test/mongoose/_insert",
             params={'docs' : '[{"x" : 1},{"x" : 2},{"x" : 3}]'},
             async = False)

        str = GET("http://localhost:27080/test/mongoose/_find")

        self.assertEquals(type(str).__name__, "str")

        obj = json.loads(str)

        self.assertEquals(obj['ok'], 1, str)
        self.assertEquals(type(obj['id']).__name__, "int", str)
        self.assertEquals(len(obj['results']), 3, str)


    def test_find_sort(self):
        POST("http://localhost:27080/test/mongoose/_insert",
             params={'docs' : '[{"x" : 1},{"x" : 2},{"x" : 3}]'},
             async = False)
        
        str = GET("http://localhost:27080/test/mongoose/_find",
                  {"sort" : '{"x" : -1}'})

        self.assertEquals(type(str).__name__, "str")

        obj = json.loads(str)

        self.assertEquals(obj['results'][0]['x'], 3, str)
        self.assertEquals(obj['results'][1]['x'], 2, str)
        self.assertEquals(obj['results'][2]['x'], 1, str)




if __name__ == '__main__':
    unittest.main()
