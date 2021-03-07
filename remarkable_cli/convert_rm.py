# -*- coding: utf-8 -*-
# inspired by the original https://github.com/reHackable/maxio utility
# https://github.com/reHackable/maxio/blob/a0a9d8291bd034a0114919bbf334973bbdd6a218/tools/rM2svg#L1
from io import BufferedReader
import json
import logging
import os
import re
import struct


class ConvertRM:
    """Partial support for version 2.5.0.27 generated lines files."""

    def __init__(self, entity_path, logger=None):
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
            with open(pg_meta_fp, "r") as fh:
                self.pages_metadata[page_id] = json.load(fh)

    def convert_rm_file(self, fh: BufferedReader):
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

        # parsing lines body
        self._log.debug(header)
        self._log.debug("num_layers: %d", num_layers)
        for layer in range(num_layers):
            fmt = "<I"
            (num_strokes,) = struct.unpack_from(fmt, fh.read(struct.calcsize(fmt)))

            self._log.debug("num_strokes: %d", num_strokes)
            for stroke in range(num_strokes):
                fmt = stroke_fmt
                stroke_data = struct.unpack_from(fmt, fh.read(struct.calcsize(fmt)))

                pen, colour, i_unk, width = stroke_data[:4]
                num_segments = stroke_data[-1]

                self._log.debug("num_segments: %d", num_segments)
                for segment in range(num_segments):
                    fmt = "<ffffff"
                    data = fh.read(struct.calcsize(fmt))
                    segment = struct.unpack_from(fmt, data)
                    xpos, ypos, pressure, tilt, i_unk2, j_unk2 = segment
                    self._log.debug(segment)

    def convert_document(self):
        for page_id in self.page_ids:
            pg_rm_fp = os.path.join(self.pages_fp, f"{page_id}{os.extsep}rm")
            with open(pg_rm_fp, "rb") as fh:
                self.convert_rm_file(fh)
