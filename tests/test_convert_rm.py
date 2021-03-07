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
            )
        )

    def test_initialization(self):
        self.assertRaises(
            FileNotFoundError,
            ConvertRM,
            os.path.join(
                DIR_PATH, "data", "version-5", "00000000-0000-0000-0000-000000000000"
            ),
        )

        self.assertIsInstance(self.converter, ConvertRM)
        self.assertEqual(
            self.converter.content,
            {
                "coverPageNumber": -1,
                "dummyDocument": False,
                "extraMetadata": {
                    "LastBallpointColor": "Black",
                    "LastBallpointSize": "2",
                    "LastBallpointv2Color": "White",
                    "LastBallpointv2Size": "1",
                    "LastCalligraphyColor": "Gray",
                    "LastCalligraphySize": "1",
                    "LastClearPageColor": "Black",
                    "LastClearPageSize": "2",
                    "LastEraseSectionColor": "Black",
                    "LastEraseSectionSize": "2",
                    "LastEraserColor": "Black",
                    "LastEraserSize": "2",
                    "LastEraserTool": "EraseSection",
                    "LastFinelinerColor": "Black",
                    "LastFinelinerSize": "2",
                    "LastFinelinerv2Color": "White",
                    "LastFinelinerv2Size": "3",
                    "LastHighlighterColor": "Black",
                    "LastHighlighterSize": "2",
                    "LastHighlighterv2Color": "Black",
                    "LastHighlighterv2Size": "2",
                    "LastMarkerColor": "Black",
                    "LastMarkerSize": "2",
                    "LastMarkerv2Color": "White",
                    "LastMarkerv2Size": "2",
                    "LastPaintbrushColor": "Black",
                    "LastPaintbrushSize": "2",
                    "LastPaintbrushv2Color": "Black",
                    "LastPaintbrushv2Size": "3",
                    "LastPen": "Finelinerv2",
                    "LastPencilColor": "Black",
                    "LastPencilSize": "2",
                    "LastPencilv2Color": "Black",
                    "LastPencilv2Size": "3",
                    "LastReservedPenColor": "Black",
                    "LastReservedPenSize": "2",
                    "LastSelectionToolColor": "Black",
                    "LastSelectionToolSize": "2",
                    "LastSharpPencilColor": "Black",
                    "LastSharpPencilSize": "2",
                    "LastSharpPencilv2Color": "Black",
                    "LastSharpPencilv2Size": "3",
                    "LastSolidPenColor": "Black",
                    "LastSolidPenSize": "2",
                    "LastTool": "Finelinerv2",
                    "LastUndefinedColor": "Black",
                    "LastUndefinedSize": "1",
                    "LastZoomToolColor": "Black",
                    "LastZoomToolSize": "2",
                },
                "fileType": "notebook",
                "fontName": "",
                "lineHeight": -1,
                "margins": 100,
                "orientation": "portrait",
                "pageCount": 3,
                "pages": [
                    "7fb6da1a-2826-4ff2-93eb-0e38a76f91bb",
                    "56f7d738-8728-46f2-a799-036cd40d2c19",
                    "b32ce4c2-df8a-44c7-b46a-294ffa8cb3f3",
                ],
                "textAlignment": "left",
                "textScale": 1,
                "transform": {
                    "m11": 1,
                    "m12": 0,
                    "m13": 0,
                    "m21": 0,
                    "m22": 1,
                    "m23": 0,
                    "m31": 0,
                    "m32": 0,
                    "m33": 1,
                },
            },
        )

        self.assertEqual(
            self.converter.metadata,
            {
                "deleted": False,
                "lastModified": "1615126599146",
                "lastOpenedPage": 1,
                "metadatamodified": False,
                "modified": False,
                "parent": "",
                "pinned": False,
                "synced": True,
                "type": "DocumentType",
                "version": 12,
                "visibleName": "Sample Pens",
            },
        )

        self.assertEqual(self.converter.pagedata, ["Blank", "Isometric", "Blank"])

        self.assertEqual(
            self.converter.pages_metadata,
            {
                "7fb6da1a-2826-4ff2-93eb-0e38a76f91bb": {
                    "layers": [{"name": "Layer 1"}]
                },
                "56f7d738-8728-46f2-a799-036cd40d2c19": {
                    "layers": [{"name": "Layer 1"}]
                },
                "b32ce4c2-df8a-44c7-b46a-294ffa8cb3f3": {
                    "layers": [
                        {"name": "Layer 1"},
                        {"name": "Layer 2"},
                        {"name": "Layer 3"},
                    ]
                },
            },
        )

    def test_convert_document(self):
        self.converter.convert_document()
        self.assertTrue(True)
