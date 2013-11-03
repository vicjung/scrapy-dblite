import unittest

from dblite.serializers import cPickleSerializer
from dblite.serializers import CompressedPickleSerializer
from dblite.serializers import CompressedJsonSerializer

SOURCE_DATA = {
    u'key1': u'value1', u'key2': u'value2', u'key3': u'value3',
}


class SerializersTest(unittest.TestCase):

    def test_cpickle_serializer(self):
        ''' test_cpickle_serializer
        '''
        s = cPickleSerializer()
        self.assertEqual(s.loads(s.dumps(SOURCE_DATA)), SOURCE_DATA)

    def test_compressed_pickle_serializer(self):
        ''' test_compressed_pickle_serializer
        '''
        s = CompressedPickleSerializer()
        self.assertEqual(s.loads(s.dumps(SOURCE_DATA)), SOURCE_DATA)

    def test_compressed_json_serializer(self):
        ''' test_compressed_json_serializer
        '''
        s = CompressedJsonSerializer()
        self.assertEqual(s.loads(s.dumps(SOURCE_DATA)), SOURCE_DATA)
