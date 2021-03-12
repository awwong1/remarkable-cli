# -*- coding: utf-8 -*-
# inspired by the original https://github.com/reHackable/maxio utility
# https://github.com/reHackable/maxio/blob/a0a9d8291bd034a0114919bbf334973bbdd6a218/tools/rM2svg#L1
import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from io import BufferedReader
from struct import calcsize, unpack_from
from tempfile import TemporaryFile

from reportlab.graphics import renderPDF
from reportlab.pdfgen.canvas import Canvas
from svglib.svglib import svg2rlg

from .pens import (
    Ballpoint,
    Brush,
    Calligraphy,
    EraseArea,
    Eraser,
    Fineliner,
    Highlighter,
    Marker,
    MechanicalPencil,
    Pen,
    Pencil,
)


class ConvertRM:
    """Partial support for version 2.5.0.27 generated lines files."""

    X_SIZE = 1404
    Y_SIZE = 1872

    STROKE_COLOUR = {
        0: "#000000",
        1: "#c7c7c7",
        2: "#ffffff",
    }

    @staticmethod
    def _blank_template():
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
        blank_layer = ET.Element("g", {"id": "Background"})
        blank_layer.append(
            ET.Element(
                "rect",
                {
                    "x": "0",
                    "y": "0",
                    "width": f"{ConvertRM.X_SIZE}",
                    "height": f"{ConvertRM.Y_SIZE}",
                    "fill": "#FFFFFF",
                },
            )
        )
        svg_root.append(blank_layer)
        return ET.ElementTree(svg_root)

    def __init__(
        self,
        entity_path: os.PathLike,
        local_templates_path: str,
        logger: logging.Logger = None,
    ):
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
        self.templates_fp = local_templates_path

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

    def _convert_rm_to_svg(self, fh: BufferedReader, template_tree: ET.ElementTree):
        raw_header_template = "reMarkable .lines file, version=#          "
        fmt = f"<{len(raw_header_template)}sI"
        header, num_layers = unpack_from(fmt, fh.read(calcsize(fmt)))

        # Verify header with byte regular expression
        header_regex = rb"^reMarkable .lines file, version=(?P<version>\d)          $"
        obtained_header = re.search(header_regex, header)
        version = obtained_header.groupdict().get("version")
        if not version:
            raise RuntimeError("invalid lines header provided")

        # determine stroke format using version number
        stroke_fmt = "<IIIfII"  # Version 5
        if int(version) < 5:
            stroke_fmt = "<IIIfI"  # Version 3 (anything pre 5)

        svg_root = template_tree.getroot()

        for layer_idx in range(num_layers):
            fmt = "<I"
            (num_strokes,) = unpack_from(fmt, fh.read(calcsize(fmt)))

            svg_layer = ET.Element("g")

            for stroke_idx in range(num_strokes):
                stroke_data = unpack_from(stroke_fmt, fh.read(calcsize(stroke_fmt)))

                pen_idx, colour_idx, i_unk, stroke_width = stroke_data[:4]
                num_segments = stroke_data[-1]
                stroke_color = ConvertRM.STROKE_COLOUR.get(colour_idx, "black")

                if pen_idx in (2, 15):
                    pen = Ballpoint(stroke_width, stroke_color)
                elif pen_idx in (4, 17):
                    pen = Fineliner(stroke_width, stroke_color)
                elif pen_idx in (3, 16):
                    pen = Marker(stroke_width, stroke_color)
                elif pen_idx in (1, 14):
                    pen = Pencil(stroke_width)
                elif pen_idx in (7, 13):
                    pen = MechanicalPencil(stroke_width)
                elif pen_idx in (0, 12):
                    pen = Brush(stroke_width, stroke_color)
                elif pen_idx in (5, 18):
                    pen = Highlighter()
                elif pen_idx in (21,):
                    pen = Calligraphy(stroke_width, stroke_color)
                elif pen_idx in (8,):
                    pen = EraseArea()
                elif pen_idx in (6,):
                    pen = Eraser(stroke_width)
                else:
                    self._log.warning("unknown pen type %d", pen_idx)
                    pen = Pen()

                svg_layer.append(ET.Comment(f"Stroke: {stroke_data}"))

                line_points = []
                for segment_idx in range(num_segments):
                    fmt = "<ffffff"
                    segment = unpack_from(fmt, fh.read(calcsize(fmt)))
                    x_pos, y_pos, speed, tilt, width, pressure = segment
                    pt = f"{x_pos},{y_pos}"

                    if (line_points and line_points[-1] != pt) or not line_points:
                        line_points.append(pt)

                    if pen.segment_length < 0 or segment_idx % pen.segment_length != 0:
                        continue

                    attrs = pen.get_polyline_attributes(speed, tilt, width, pressure)
                    attrs["points"] = " ".join(line_points)
                    svg_polyline = ET.Element("polyline", attrs)
                    svg_layer.append(svg_polyline)
                    line_points = [pt]

                attrs = pen.get_polyline_attributes(speed, tilt, width, pressure)
                attrs["points"] = " ".join(line_points)
                svg_polyline = ET.Element("polyline", attrs)
                svg_layer.append(svg_polyline)

            svg_root.append(svg_layer)
        # self._log.debug(ET.tostring(svg_root))
        return template_tree

    def convert_document(
        self, pdf_output_path: os.PathLike, creator="awwong1/remarkable-cli"
    ):
        pdf_output = Canvas(pdf_output_path)
        title = self.metadata.get("visibleName", "Untitled")
        pdf_output.setSubject(title)
        title_ext = f"{title}{os.extsep}pdf"
        pdf_output.setTitle(title_ext)
        pdf_output.setCreator(creator)

        for idx, page_id in enumerate(self.page_ids):
            pg_rm_fp = os.path.join(self.pages_fp, f"{page_id}{os.extsep}rm")
            if not os.path.isfile(pg_rm_fp):
                self._log.debug(f"skipping {pg_rm_fp}")
                continue

            template_filename = self.pagedata[idx]
            template_svg_fp = os.path.join(
                self.templates_fp, f"{template_filename}{os.extsep}svg"
            )

            ET.register_namespace("", "http://www.w3.org/2000/svg")
            template_tree = ConvertRM._blank_template()

            if template_filename == "Blank":
                self._log.debug("overriding Blank template with clean svg root")
            elif os.path.isfile(template_svg_fp):
                template_tree = ET.parse(template_svg_fp)
            else:
                self._log.warning(
                    "template %s not found at %s", template_filename, template_svg_fp
                )

            with open(pg_rm_fp, "rb") as fh:
                template_tree = self._convert_rm_to_svg(fh, template_tree)

            with TemporaryFile(mode="w+b") as tf:
                template_tree.write(tf)
                tf.seek(0)
                drawing = svg2rlg(tf)
                pdf_output.setPageSize((drawing.width, drawing.height))
            renderPDF.draw(drawing, pdf_output, 0, 0)
            pdf_output.showPage()

        pdf_output.save()
