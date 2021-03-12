class Pen:
    def __init__(
        self,
        name="Basic Pen",
        base_width=2.0,
        stroke_color="black",
        segment_length=-1,
        opacity=1.0,
        stroke_cap="round",
        stroke_join="round",
    ):
        self.name = name
        self.color = stroke_color
        self.base_width = base_width  # Small: 1.875; Medium 2.0; Large 2.125
        self.opacity = opacity
        self.segment_length = segment_length
        self.stroke_cap = stroke_cap
        self.stroke_join = stroke_join

    def get_polyline_attributes(self, _speed, _tilt, width, _pressure):
        segment_width = (self.base_width * width) / 2.0
        return {
            "fill": "none",
            "stroke-width": f"{segment_width:.3f}",
            "stroke": self.color,
            "stroke-opacity": f"{self.opacity:.3f}",
            "stroke-linecap": self.stroke_cap,
            "stroke-linejoin": self.stroke_join,
        }


class Ballpoint(Pen):
    def __init__(self, base_width, stroke_color):
        super().__init__(
            name="Ballpoint",
            base_width=base_width,
            stroke_color=stroke_color,
            segment_length=5,
        )

    def get_polyline_attributes(self, speed, tilt, width, pressure):
        attrs = super().get_polyline_attributes(speed, tilt, width, pressure)
        segment_width = (0.5 + pressure) + (1 * width) - 0.5 * (speed / 50)
        attrs.update(
            {
                "stroke-width": f"{segment_width:.3f}",
            }
        )
        return attrs


class Fineliner(Pen):
    def __init__(self, base_width, stroke_color):
        super().__init__(
            name="Fineliner",
            stroke_color=stroke_color,
        )

    def get_polyline_attributes(self, speed, tilt, width, pressure):
        attrs = super().get_polyline_attributes(speed, tilt, width, pressure)
        segment_width = width
        attrs.update(
            {
                "stroke-width": f"{segment_width:.3f}",
            }
        )
        return attrs


class Marker(Pen):
    def __init__(self, base_width, stroke_color):
        super().__init__(
            name="Marker",
            base_width=base_width,
            segment_length=3,
            stroke_color=stroke_color,
        )

    def get_polyline_attributes(self, speed, tilt, width, pressure):
        attrs = super().get_polyline_attributes(speed, tilt, width, pressure)
        segment_width = (width * self.base_width) / 2.7
        attrs.update(
            {
                "stroke-width": f"{segment_width:.3f}",
            }
        )
        return attrs


class Pencil(Pen):
    def __init__(self, stroke_width):
        super().__init__(
            name="Pencil",
            base_width=stroke_width,
            segment_length=2,
            # stroke_join="bevel",
        )

    def get_polyline_attributes(self, speed, tilt, width, pressure):
        attrs = super().get_polyline_attributes(speed, tilt, width, pressure)
        segment_width = (width * self.base_width) / 3.5

        segment_opacity = (0.1 * -(speed / 35)) + (1 * pressure)
        segment_opacity = min(max(0.0, segment_opacity), 1.0) - 0.1

        attrs.update(
            {
                "stroke-width": f"{segment_width:.3f}",
                "stroke-opacity": f"{segment_opacity:.3f}",
            }
        )
        return attrs


class MechanicalPencil(Pen):
    def __init__(self, stroke_width):
        super().__init__(name="Mechanical Pencil", base_width=stroke_width)

    def get_polyline_attributes(self, speed, tilt, width, pressure):
        attrs = super().get_polyline_attributes(speed, tilt, width, pressure)
        segment_width = (width * self.base_width) / 3.5

        attrs.update(
            {
                "stroke-width": f"{segment_width:.3f}",
            }
        )
        return attrs


class Brush(Pen):
    def __init__(self, base_width, stroke_color):
        super().__init__(
            name="Brush",
            base_width=base_width,
            stroke_color=stroke_color,
            segment_length=4,
        )

    def get_polyline_attributes(self, speed, tilt, width, pressure):
        attrs = super().get_polyline_attributes(speed, tilt, width, pressure)
        segment_width = (width * self.base_width) / 2.7

        intensity = (pressure ** 1.5 - 0.2 * (speed / 50)) * 1.5
        intensity = min(max(0.0, intensity), 1.0)
        attrs.update(
            {
                "stroke-width": f"{segment_width:.3f}",
                "stroke-opacity": f"{intensity:.3f}",
            }
        )
        return attrs


class Highlighter(Pen):
    def __init__(self):
        super().__init__(
            name="Highlighter", opacity=0.1, stroke_cap="square", stroke_color="yellow"
        )


class Eraser(Pen):
    def __init__(self, base_width):
        super().__init__(
            name="Eraser",
            base_width=base_width,
            stroke_color="white",
            opacity=0.0,
        )


class EraseArea(Pen):
    def __init__(self):
        super().__init__(
            name="Erase Area",
            opacity=0.0,
            stroke_color="white",
        )


class Calligraphy(Pen):
    def __init__(self, base_width, stroke_color):
        super().__init__(
            name="Calligraphy",
            base_width=base_width,
            stroke_color=stroke_color,
            segment_length=2,
        )
