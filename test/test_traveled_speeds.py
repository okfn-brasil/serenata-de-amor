import unittest

class TestTraveledSpeeds(unittest.TestCase):

    def setUp(self):
        self.result = 2 + 2

    def test_it_works(self):
        self.assertEqual(4, self.result)

    def test_it_works2(self):
        self.assertNotEqual(5, self.result)



if __name__ == '__main__':
    unittest.main()
