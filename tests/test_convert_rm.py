import logging
import os
import unittest

from remarkable_cli.convert_rm import ConvertRM

DIR_PATH = os.path.dirname(os.path.realpath(__file__))


class TestConvertRM(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        logging.disable(logging.CRITICAL)
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        logging.disable(logging.NOTSET)
        return super().tearDownClass()

    def setUp(self):
        self.converter = ConvertRM(
            os.path.join(
                DIR_PATH, "data", "version-5", "07a07495-09b1-47f9-bb88-370aadc4395b"
            ),
            os.path.join(DIR_PATH, "data", "templates"),
        )

    def test_initialization(self):
        self.assertRaises(
            FileNotFoundError,
            ConvertRM,
            os.path.join(
                DIR_PATH, "data", "version-5", "00000000-0000-0000-0000-000000000000"
            ),
            os.path.join(DIR_PATH, "data", "templates"),
        )
        self.assertIsInstance(self.converter, ConvertRM)

    def test_convert_document(self):
        self.converter.convert_document()
        self.assertTrue(True)
