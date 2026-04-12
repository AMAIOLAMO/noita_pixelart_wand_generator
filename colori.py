import math_utils as umath
import colorsys as colsys
import ciede2000 as ciede
from enum import Enum

class ColorMatchMode(Enum):
    PERCEPTUAL_LINEAR = 1
    DE2000 = 2

class Colori:
    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    @staticmethod
    def from_rgba_tuple(rgba: (int, int, int, int)) -> "Colori":
        r, g, b, _ = rgba
        return Colori(
            r, g, b
        )

    ## the higher the more different
    def dist_to(self, other, match_mode = ColorMatchMode.PERCEPTUAL_LINEAR) -> float:
        if match_mode == ColorMatchMode.DE2000:
            return ciede.ciede2000(self.to_lab(), other.to_lab())

        if match_mode == ColorMatchMode.PERCEPTUAL_LINEAR:
            dr = self.r - other.r
            dg = self.g - other.g
            db = self.b - other.b

            ## Perceptual weights (human vision sensitivity)
            return (
                0.2126 * dr * dr +
                0.7152 * dg * dg +
                0.0722 * db * db
            )

        raise ValueError('match mode invalid')
        return 0
    
    def to_hsl(self) -> (float, float, float):
        hue, light, sat = colsys.rgb_to_hls(self.r / 255, self.g / 255, self.b / 255)
        return (hue, sat, light)

    # reference https://gist.github.com/manojpandey/f5ece715132c572c80421febebaf66ae
    def to_lab(self) -> (float, float, float):
        in_color = [self.r, self.g, self.b]

        num = 0
        RGB = [0, 0, 0]

        for value in in_color:
            value = float(value) / 255

            if value > 0.04045:
                value = ((value + 0.055) / 1.055) ** 2.4
            else:
                value = value / 12.92

            RGB[num] = value * 100
            num = num + 1

        XYZ = [0, 0, 0, ]

        X = RGB[0] * 0.4124 + RGB[1] * 0.3576 + RGB[2] * 0.1805
        Y = RGB[0] * 0.2126 + RGB[1] * 0.7152 + RGB[2] * 0.0722
        Z = RGB[0] * 0.0193 + RGB[1] * 0.1192 + RGB[2] * 0.9504
        XYZ[0] = round(X, 4)
        XYZ[1] = round(Y, 4)
        XYZ[2] = round(Z, 4)

        # Observer= 2°, Illuminant= D65
        XYZ[0] = float(XYZ[0]) / 95.047         # ref_X =  95.047
        XYZ[1] = float(XYZ[1]) / 100.0          # ref_Y = 100.000
        XYZ[2] = float(XYZ[2]) / 108.883        # ref_Z = 108.883

        num = 0
        for value in XYZ:

            if value > 0.008856:
                value = value ** (0.3333333333333333)
            else:
                value = (7.787 * value) + (16 / 116)

            XYZ[num] = value
            num = num + 1

        Lab = [0, 0, 0]

        L = (116 * XYZ[1]) - 16
        a = 500 * (XYZ[0] - XYZ[1])
        b = 200 * (XYZ[1] - XYZ[2])

        Lab[0] = round(L, 4)
        Lab[1] = round(a, 4)
        Lab[2] = round(b, 4)

        return (
            Lab[0], Lab[1], Lab[2]
        )


    ## returns perceptual luminance between 0 and 1
    def perceptual_luminance(self) -> float:
        raw_pluminance = \
            0.2126 * (self.r / 255) + \
            0.7152 * (self.g / 255) + \
            0.0722 * (self.b / 255)

        return umath.clampf(raw_pluminance, 0, 1)
    
    def to_tuple(self) -> (int, int, int):
        return (self.r, self.g, self.b)


# def tuple_rgba_to_colori(color_tuple) -> Colori:
#     r, g, b, _ = color_tuple
#     return Colori(
#         r, g, b
#     )

