from PIL import Image
import colorsys as colsys
import numpy as np
from enum import Enum
from io import StringIO
import ciede2000 as ciede


## This script assumes a few things:
## You are using CE's wiki wands to import the wands
## you have the image file(input.png) stored in the running directory
## The result will be printed out in console, you need to copy and import this in CE (Component Editor)
## you need to install pillow and numpy for python (`pip install pillow numpy`) preferably in a virtual environment :P

def clampf(v: float, a: float, b: float) -> float:
    return max(
        a, min(b, v)
    )

## returns shortest distance in a circular hue 0 ~ 1
def hue_min_dist(hue_a: float, hue_b: float) -> float:
    dt = hue_a - hue_b
    return min(
        abs(dt),
        abs(dt + 1)
    )

class ColorMatchMode(Enum):
    PERCEPTUAL_LINEAR = 1
    DE2000 = 2


class Colori:
    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b
        pass

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

        return clampf(raw_pluminance, 0, 1)


def tuple_rgba_to_colori(color_tuple) -> Colori:
    r, g, b, _ = color_tuple
    return Colori(
        r, g, b
    )


color_pairs = [
    (Colori(255, 40,  19),  "COLOUR_RED"),
    (Colori(255, 97, 37),  "COLOUR_ORANGE"),
    (Colori(255, 173, 16),  "COLOUR_YELLOW"),
    (Colori(151, 255, 71),  "COLOUR_GREEN"),
    (Colori(55, 195, 255), "COLOUR_BLUE"),
    (Colori(126, 67,  255), "COLOUR_PURPLE"),

    (Colori(255, 255, 255),  "GLIMMERS_EXPANDED_COLOUR_WHITE"),
    (Colori(255, 83, 244),  "GLIMMERS_EXPANDED_COLOUR_PINK"),
    (Colori(241, 101, 171),  "GLIMMERS_EXPANDED_COLOUR_WEIRD_FUNGUS"),
    (Colori(132, 0, 0),  "GLIMMERS_EXPANDED_COLOUR_BLOOD"),
    (Colori(255, 97, 1),  "GLIMMERS_EXPANDED_COLOUR_FIRE"),
    (Colori(0, 238, 51),  "GLIMMERS_EXPANDED_COLOUR_ACID"),
    (Colori(38,   198, 41), "GLIMMERS_EXPANDED_COLOUR_DIMINUTION"),
    (Colori(70,   246, 150), "GLIMMERS_EXPANDED_COLOUR_TEAL"),
    (Colori(63, 79, 138), "GLIMMERS_EXPANDED_COLOUR_FREEZING_LIQUID"),
    (Colori(86, 63,  103), "GLIMMERS_EXPANDED_COLOUR_OMINOUS"),
    (Colori(233, 190,  93), "GLIMMERS_EXPANDED_COLOUR_MIMICIUM"),
    (Colori(255, 165,  209), "GLIMMERS_EXPANDED_COLOUR_TRUE_RAINBOW"),
    (Colori(240, 162, 1), "GLIMMERS_EXPANDED_COLOUR_MIDAS"),
    (Colori(163, 244, 143), "GLIMMERS_EXPANDED_COLOUR_LIVELY_CONCOCTION"),
    (Colori(53, 187, 43), "GLIMMERS_EXPANDED_COLOUR_DIVINE_GROUND"),
    (Colori(0,   0,   0),   "COLOUR_INVIS"), # assumes the background is black
    # (Colori(0, 0, 0),   "GLIMMERS_EXPANDED_COLOUR_VOID"),

    # # my own expansion
    (Colori(99, 160, 188), "GLIMMERS_EXPANDED_CX_COLOUR_DIAMOND_BRICK"),
    (Colori(220, 221, 140), "GLIMMERS_EXPANDED_CX_COLOUR_AUSTRALIUM"),
    (Colori(186, 161, 91), "GLIMMERS_EXPANDED_CX_COLOUR_MOLTEN_COPPER"),
    (Colori(58, 25, 119), "GLIMMERS_EXPANDED_CX_COLOUR_CREEPY_LIQUID"),
    (Colori(45, 84, 14), "GLIMMERS_EXPANDED_CX_COLOUR_FUNGUS_GREEN"),
    (Colori(57, 100, 92), "GLIMMERS_EXPANDED_CX_COLOUR_WATER"),
    (Colori(129, 129, 129), "GLIMMERS_EXPANDED_CX_COLOUR_CEMENT"),
    (Colori(244, 206, 104), "GLIMMERS_EXPANDED_CX_COLOUR_CHEESE"),
    (Colori(145, 0, 172), "GLIMMERS_EXPANDED_CX_COLOUR_MOLTEN_PLASTIC_RED"),
    (Colori(121, 173, 67), "GLIMMERS_EXPANDED_CX_COLOUR_RED_BRICK"),
    (Colori(205, 77, 77), "GLIMMERS_EXPANDED_CX_COLOUR_VOMIT"),
    (Colori(185, 159, 89), "GLIMMERS_EXPANDED_CX_COLOUR_MOLTEN_BRASS"),
    (Colori(204, 113, 113), "GLIMMERS_EXPANDED_CX_COLOUR_FROZEN_BLOOD"),
    (Colori(28, 46, 45), "GLIMMERS_EXPANDED_CX_COLOUR_BONE"),
    (Colori(255, 239, 0), "GLIMMERS_EXPANDED_CX_COLOUR_URINE"),
    (Colori(224, 153, 41), "GLIMMERS_EXPANDED_CX_COLOUR_AMBROSIA"),
    (Colori(185, 159, 89), "GLIMMERS_EXPANDED_CX_COLOUR_MOLTEN_GLASS"),
    (Colori(0, 191, 229), "GLIMMERS_EXPANDED_CX_COLOUR_UNSTABLE_TELEPORTATIUM"),
    (Colori(128, 207, 235), "GLIMMERS_EXPANDED_CX_COLOUR_TELEPORTATIUM"),
    (Colori(65, 64, 37), "GLIMMERS_EXPANDED_CX_COLOUR_WOOD"),
    (Colori(235, 115, 8), "GLIMMERS_EXPANDED_CX_COLOUR_JUHHANUSSIMA_BROWN"),
    (Colori(241, 213, 72), "GLIMMERS_EXPANDED_CX_COLOUR_HOLY_MATTER"),
    (Colori(102, 174, 67), "GLIMMERS_EXPANDED_CX_COLOUR_FUNGUS_RED"),
    (Colori(88, 103, 122), "GLIMMERS_EXPANDED_CX_COLOUR_FUSE_DARK"),
    (Colori(36, 61, 255), "GLIMMERS_EXPANDED_CX_COLOUR_MIDAS_PRECURSOR"),
    (Colori(48, 109, 193), "GLIMMERS_EXPANDED_CX_COLOUR_INVISIBLIUM"),
    (Colori(105, 87, 67), "GLIMMERS_EXPANDED_CX_COLOUR_PUS"),
    (Colori(240, 162, 1), "GLIMMERS_EXPANDED_CX_COLOUR_DRAUGHT_OF_MIDAS"),
    (Colori(255, 247, 230), "GLIMMERS_EXPANDED_CX_COLOUR_MILK"),
    (Colori(11, 255, 230), "GLIMMERS_EXPANDED_CX_COLOUR_CONC_MANA"),
    (Colori(255, 81, 241), "GLIMMERS_EXPANDED_CX_COLOUR_PLASMA_PINK"),
]

def find_closest_color_pair(color: Colori, match_mode: ColorMatchMode):
    dist = color_pairs[0][0].dist_to(color)
    best_pair = color_pairs[0]


    # yes the first element being done multiple times but I dont care
    for color_pair in color_pairs:
        new_dist = color_pair[0].dist_to(color, match_mode)

        if new_dist < dist:
            dist = new_dist
            best_pair = color_pair

    return best_pair


def make_pixel_str(is_col_end: bool, color_spell_name: str) -> str:
    result = ""
    if is_col_end == False:
        result += "BURST_2,"

    # result += "NOLLA,SUPER_TELEPORT_CAST,LIFETIME_DOWN,LIFETIME_DOWN,LIFETIME_DOWN,LIFETIME," + color_spell_name + ",BLOOD_MAGIC,BLOOD_MAGIC,BLOOD_MAGIC,DEATH_CROSS_BIG,SUPER_TELEPORT_CAST"
    result += "NOLLA,SUPER_TELEPORT_CAST,BURST_3,BLOOD_MAGIC,BLOOD_MAGIC,ZERO_DAMAGE,ZERO_DAMAGE," + color_spell_name + ",FIREBOMB,ADD_TRIGGER,CASTER_CAST,DIGGER,PURPLE_EXPLOSION_FIELD,SUPER_TELEPORT_CAST"
    return result

def begin_column_str() -> str:
    # return "BURST_2,BLOOD_MAGIC,BLOOD_MAGIC,NOLLA,SUPER_TELEPORT_CAST,ADD_DEATH_TRIGGER,NOLLA,GRAVITY,DEATH_CROSS"
    return "BURST_2,BLOOD_MAGIC,BLOOD_MAGIC,NOLLA,SUPER_TELEPORT_CAST,ADD_DEATH_TRIGGER,NOLLA,GRAVITY,DIGGER"

print("Reading image")
img = Image.open("input.png")
pixels = img.load()
width, height = img.size


spell_str_io = StringIO()
spell_str_io.write("ACCELERATING_SHOT,LINE_ARC,LONG_DISTANCE_CAST\n")
# spells_str = "ACCELERATING_SHOT,LONG_DISTANCE_CAST\n"

spell_count = 0

preview_pixels = [
]

print("Constructing Spells and colors...")
for x in range(width):
    spell_str_io.write(",")
    spell_str_io.write(begin_column_str())
    spell_str_io.write("\n")
    # spells_str += "," + begin_column_str() + "\n"

    col_pixels = []

    for y in range(height):
        is_end = y == height - 1

        pixel_color = tuple_rgba_to_colori(pixels[x, y])

        match_color_pair = find_closest_color_pair(pixel_color, ColorMatchMode.DE2000)

        match_color_spell_name = match_color_pair[1]

        spell_str_io.write(",")
        spell_str_io.write(make_pixel_str(is_end, match_color_spell_name))
        # spells_str += "," + make_pixel_str(is_end, match_color_spell_name)

        col_pixels.append((
            match_color_pair[0].r,
            match_color_pair[0].g,
            match_color_pair[0].b,
        ))


    preview_pixels.append(col_pixels)
    
    spell_str_io.write("\n")
    # spells_str += "\n"
print("Render Complete")

print("Creating preview...")
preview_pixels_array = np.array(preview_pixels, dtype=np.uint8)
preview_img = Image.fromarray(preview_pixels_array)
preview_img = preview_img.rotate(-90).transpose(Image.FLIP_LEFT_RIGHT)
preview_img.save('preview.png')
print("Preview complete...")

print("Creating ce import string...")
ce_import_str = ""
ce_import_str += ("""
{{Wand2
| wandPic      = Wand 0821.png\n""")

ce_import_str += f"""
| capacity     = {len(spell_str_io.getvalue().split(','))}\n"""

ce_import_str += ("""
| manaMax      = 100000.00
| manaCharge   = 100000.00
| spells       = """)

ce_import_str += (spell_str_io.getvalue()) + "\n"

ce_import_str += ("""
}}
""")

print("Finished ce import string...")

print("Writing to result.txt")
with open("result.txt", "w") as result_file:
   result_file.write(ce_import_str)


print("Clean up")
spell_str_io.close()
