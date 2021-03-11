class Pen:
    def __init__(
        self,
        name="Basic Pen",
        base_width=2.0,
        stroke_color="black",
        segment_length=-1,
        opacity=1.0,
        stroke_cap="round",
    ):
        self.name = name
        self.color = stroke_color
        self.base_width = base_width  # Small: 1.875; Medium 2.0; Large 2.125
        self.opacity = opacity
        self.segment_length = segment_length
        self.stroke_cap = stroke_cap

    def get_polyline_attributes(self, speed, tilt, width, pressure):
        return {
            "fill": "none",
            # "stroke-width": f"{self.base_width:.3f}",
            "stroke-width": f"{(self.base_width * width)/2.0:.3f}",
            "stroke": self.color,
            "opacity": f"{self.opacity:.3f}",
            "stroke-linecap": self.stroke_cap,
            "stroke-linejoin": "round",
            # "stroke-miterlimit": "1",
        }


class Ballpoint(Pen):
    def __init__(self, base_width, stroke_color):
        super().__init__(
            name="Ballpoint",
            base_width=base_width,
            stroke_color=stroke_color,
            segment_length=5,
        )

    def get_polyline_attributes(self, *args):
        attrs = super().get_polyline_attributes(*args)
        speed, tilt, width, pressure = args
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
            # base_width=(base_width ** 2.1) * 1.3,
            stroke_color=stroke_color,
        )

    def get_polyline_attributes(self, *args):
        attrs = super().get_polyline_attributes(*args)
        speed, tilt, width, pressure = args
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

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        segment_width = 0.9 * (((1 * width)) - 0.4 * tilt) + (0.1 * last_width)
        return segment_width


class Pencil(Pen):
    def __init__(self, stroke_width):
        super().__init__(name="Pencil", base_width=stroke_width, segment_length=2)

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        segment_width = 0.7 * (
            (((0.8 * self.base_width) + (0.5 * pressure)) * (1 * width))
            - (0.25 * tilt ** 1.8)
            - (0.6 * speed / 50)
        )
        max_width = self.base_width * 10
        segment_width = segment_width if segment_width < max_width else max_width
        return segment_width

    def get_segment_opacity(self, speed, tilt, width, pressure, last_width):
        segment_opacity = (0.1 * -(speed / 35)) + (1 * pressure)
        segment_opacity = self.cutoff(segment_opacity) - 0.1
        return segment_opacity


class MechanicalPencil(Pen):
    def __init__(self, stroke_width):
        super().__init__(
            name="Mechanical Pencil", base_width=stroke_width
        )


class Brush(Pen):
    def __init__(self, base_width, stroke_color):
        super().__init__(
            name="Brush",
            base_width=base_width,
            stroke_color=stroke_color,
            segment_length=2,
        )

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        segment_width = 0.7 * (
            ((1 + (1.4 * pressure)) * (1 * width)) - (0.5 * tilt) - (0.5 * speed / 50)
        )  # + (0.2 * last_width)
        return segment_width

    def get_segment_color(self, speed, tilt, width, pressure, last_width):
        intensity = (pressure ** 1.5 - 0.2 * (speed / 50)) * 1.5
        intensity = self.cutoff(intensity)
        # using segment color not opacity because the dots interfere with each other.
        # Color must be 255 rgb
        rev_intensity = abs(intensity - 1)
        segment_color = [
            int(rev_intensity * (255 - self.base_color[0])),
            int(rev_intensity * (255 - self.base_color[1])),
            int(rev_intensity * (255 - self.base_color[2])),
        ]

        return "rgb" + str(tuple(segment_color))


class Highlighter(Pen):
    def __init__(self):
        super().__init__(
            name="Highlighter", opacity=0.3, stroke_cap="square", stroke_color="yellow"
        )


class Eraser(Pen):
    def __init__(self, base_width):
        super().__init__(
            name="Eraser",
            stroke_cap="square",
            base_width=base_width * 2,
            stroke_color="white",
        )


class EraseArea(Pen):
    def __init__(self):
        super().__init__(name="Erase Area", opacity=0.0, stroke_cap="square")


class Calligraphy(Pen):
    def __init__(self, base_width, stroke_color):
        super().__init__(
            name="Calligraphy",
            base_width=base_width,
            stroke_color=stroke_color,
            segment_length=2,
        )

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        segment_width = 0.9 * (((1 + pressure) * (1 * width)) - 0.3 * tilt) + (
            0.1 * last_width
        )
        return segment_width
