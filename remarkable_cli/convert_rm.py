# -*- coding: utf-8 -*-
# inspired by the original https://github.com/reHackable/maxio utility
# https://github.com/reHackable/maxio/blob/a0a9d8291bd034a0114919bbf334973bbdd6a218/tools/rM2svg#L1
import json
import logging
import os
import re
import struct
import xml.etree.ElementTree as ET
from io import BufferedReader


class ConvertRM:
    """Partial support for version 2.5.0.27 generated lines files."""

    X_SIZE = 1404
    Y_SIZE = 1872

    STROKE_COLOUR = {
        0: "black",
        1: "gray",
        2: "white",
    }

    def __init__(self, entity_path: os.PathLike, logger: logging.Logger = None):
        """
        entity_path should be:
        - path to {uuid}.(content|metadata), without extension.
        - path to directory containing pages (.rm) files, without trailing slash
        """
        self._log = logger
        if logger is None:
            log_format = "%(asctime)s [%(levelname)s]: %(message)s"
            logging.basicConfig(format=log_format, level=logging.INFO)
            self._log = logging.getLogger(__name__)

        if not os.path.isdir(entity_path):
            self._log.error("not found: %s", entity_path)
            raise FileNotFoundError(entity_path)
        self.pages_fp = entity_path

        # Document info
        self.content_fp = f"{entity_path}{os.extsep}content"
        self.metadata_fp = f"{entity_path}{os.extsep}metadata"
        self.pagedata_fp = f"{entity_path}{os.extsep}pagedata"
        with open(self.content_fp, "r") as fh:
            self.content = json.load(fh)
        with open(self.metadata_fp, "r") as fh:
            self.metadata = json.load(fh)
        with open(self.pagedata_fp, "r") as fh:
            self.pagedata = [pg_dat.rstrip() for pg_dat in fh.readlines()]

        # Page info
        self.page_ids = self.content.get("pages", [])
        self.pages_metadata = {}
        for page_id in self.page_ids:
            pg_meta_fp = os.path.join(entity_path, f"{page_id}-metadata{os.extsep}json")
            if os.path.isfile(pg_meta_fp):
                with open(pg_meta_fp, "r") as fh:
                    self.pages_metadata[page_id] = json.load(fh)

    def _convert_rm_to_svg(self, fh: BufferedReader):
        raw_header_template = "reMarkable .lines file, version=#          "
        fmt = f"<{len(raw_header_template)}sI"
        header, num_layers = struct.unpack_from(fmt, fh.read(struct.calcsize(fmt)))

        # Verify header with byte regular expression
        header_regex = rb"^reMarkable .lines file, version=(?P<version>\d)          $"
        obtained_header = re.search(header_regex, header)
        version = obtained_header.groupdict().get("version")
        if not version:
            raise RuntimeError("invalid lines header provided")

        # determine stroke format using version number
        stroke_fmt = "<IIIfII"
        if int(version) < 5:
            stroke_fmt = "<IIIfI"

        svg_root = ET.Element(
            "svg",
            {
                "xmlns": "http://www.w3.org/2000/svg",
                "xmlns:xlink": "http://www.w3.org/1999/xlink",
                "version": "1.1",
                "x": "0px",
                "y": "0px",
                "viewBox": f"0 0 {ConvertRM.X_SIZE} {ConvertRM.Y_SIZE}",
            },
        )

        # self._log.debug(header)
        # self._log.debug("num_layers: %d", num_layers)
        for layer in range(num_layers):
            fmt = "<I"
            (num_strokes,) = struct.unpack_from(fmt, fh.read(struct.calcsize(fmt)))

            svg_layer = ET.Element("g")

            # self._log.debug("num_strokes: %d", num_strokes)
            for stroke in range(num_strokes):
                fmt = stroke_fmt
                stroke_data = struct.unpack_from(fmt, fh.read(struct.calcsize(fmt)))

                pen, colour_idx, i_unk, width = stroke_data[:4]
                num_segments = stroke_data[-1]

                if colour_idx != 0:
                    self._log.info(colour_idx)
                stroke_color = ConvertRM.STROKE_COLOUR.get(colour_idx, "black")

                svg_polyline = ET.Element(
                    "polyline",
                    {"style": f"fill:none;stroke:{stroke_color};stroke-width:{width}"},
                )
                line_points = []

                # self._log.debug("stroke_data: %s", stroke_data)
                for segment in range(num_segments):
                    fmt = "<ffffff"
                    data = fh.read(struct.calcsize(fmt))
                    segment = struct.unpack_from(fmt, data)
                    xpos, ypos, pressure, tilt, i_unk2, j_unk2 = segment
                    line_points.append(f"{xpos},{ypos}")

                svg_polyline.set("points", " ".join(line_points))
                svg_layer.append(svg_polyline)
            svg_root.append(svg_layer)
        # self._log.debug(ET.tostring(svg_root))
        return svg_root

    def convert_document(self):
        # each page is its own svg element, a document can have multiple pages
        for page_id in self.page_ids:
            pg_rm_fp = os.path.join(self.pages_fp, f"{page_id}{os.extsep}rm")
            if not os.path.isfile(pg_rm_fp):
                self._log.debug(f"skipping {pg_rm_fp}")
                continue
            with open(pg_rm_fp, "rb") as fh:
                svg_root = self._convert_rm_to_svg(fh)

            os.makedirs(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)), "..", "tests", "dump"
                ),
                exist_ok=True,
            )
            svg_test_fp = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "..",
                "tests",
                "dump",
                f"{page_id}{os.extsep}svg",
            )
            ET.ElementTree(svg_root).write(svg_test_fp)
