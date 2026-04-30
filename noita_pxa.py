from PIL import Image
import numpy as np
from io import StringIO
import argparse
import datetime
import xerox
import time

from profile_timer import ProfileTimer

from typing import *

from colori import Colori, ColorMatchMode
from color_palette import Palette, ColorMatch


## TODO:
## 1. Create a GUI that helps display, switch on and off certain settings
## 2. Additive Color merging, specifically for colors that are hard to represent (aka the smallest value CIEDE2k is > 5 or smth like that)

str_render_ptimer = ProfileTimer()
pixel_match_render_ptimer = ProfileTimer()
palette_match_ptimer = ProfileTimer()

def log_info(msg: str):
    ct = datetime.datetime.now()
    print(f"[{ct}][INFO] {msg}")

def parse_dimension_arg(raw_str: str) -> (int, int):
    dim_list = raw_str.split('x')

    if len(dim_list) != 2:
        raise ValueError("dimension incorrect format, expected <width>x<height>, but got " + raw_str)
    
    return (int(dim_list[0]), int(dim_list[1]))


def make_pixel_str(is_col_end: bool, color_spell_name: str, inf_mana: bool = False) -> str:
    result = ""
    if not is_col_end:
        result += "BURST_2,"

    ## FIREBOMB
    if inf_mana == False:
        result += "BLOOD_MAGIC,BLOOD_MAGIC,"

    ## FIREBOMB TENTACLE TIMER
    result += "LIFETIME_DOWN,LIFETIME_DOWN,TENTACLE_TIMER,ZERO_DAMAGE,ZERO_DAMAGE," + color_spell_name + \
            ",FIREBOMB"
    
    if not is_col_end:
        result += ",SPEED,SUPER_TELEPORT_CAST"

    return result

def begin_column_str(is_last_col: bool, inf_mana: bool = False) -> str:
    ## FIREBOMB
    result = ""

    if inf_mana == False:
        result += "BLOOD_MAGIC,BLOOD_MAGIC,"

    # FIREBOMB TENTACLE TIMER
    if is_last_col == False:
        result += "BURST_2,"

    result += "LIFETIME_DOWN,SPEED,SUPER_TELEPORT_CAST,ADD_DEATH_TRIGGER,DIGGER"

    return result 

def end_column_str(is_last_col: bool) -> str:
    if is_last_col:
        return ""
    # else

    return ",SUPER_TELEPORT_CAST"

### ====== CLI ====== ###

IMPORT_FORMATS = {
    'default'  : "default format for cxredix pixelart expansion wand loader",
    'wiki_wand': "format for Component Explorer Wiki Wands",
}

COLOR_MATCH_MODES = {
    'ciede2k'          : (
        ColorMatchMode.CIEDE2000, "industrial standard for matching colors, much more accurate but slower."
    ),
    'perceptual_linear': (
        ColorMatchMode.PERCEPTUAL_LINEAR, "very naive implementation for matching colors, very fast."
    ),
}

arg_parser = argparse.ArgumentParser(
    "Noita pixel art wand generator By CxRedix",
    formatter_class = argparse.ArgumentDefaultsHelpFormatter,
    allow_abbrev = False
)
arg_parser.add_argument(
    '-i', '--input', type=str,
    help="The input png file to start converting from, preferably lower than 128x128."
)

arg_parser.add_argument(
    '-o', '--output', type=str,
    help="The output text file to write the Wiki wand import to."
)

arg_parser.add_argument(
    '-p', '--palette', type=str,
    help="The color palette to use in json format."
)

arg_parser.add_argument(
    '-P', '--preview', type=str, nargs="?",
    help="Optional preview png file to preview the final colors."
)

arg_parser.add_argument(
    '-m', '--manainf', action="store_true",
    help="Optionally specify whether the wand should assume that it has infinite mana or not. Helps lessen the amount of spells."
)

arg_parser.add_argument(
    '-f', '--format', type=str, default='default',
    help="Optionally Specifies different values for output formats for importing."
)

arg_parser.add_argument(
    '-c', '--color_match_mode', type=str, default='ciede2k',
    help="Optionally specifies which algorithm to use for matching colors, certain algorithms are faster and certain are slower."
)

arg_parser.add_argument(
    '-d', '--dimensions', type=str, default='original',
    help="Optional specifies the dimension to use, format: <width>x<height>; Example: 32x16 (i.e. 32px width, 16px height)"
)

arg_parser.add_argument(
    '-C', '--clipboard_copy', action="store_true",
    help="Optionally specify whether to copy the result to clipboard."
)

arg_parser.add_argument(
    '-D', '--dither', action="store_true",
    help="Optionally specify whether to utilize dithering, bayer matrix available for now."
)

args = arg_parser.parse_args()

if args.input is None:
    arg_parser.error("--input must be specified.")

if args.output is None:
    arg_parser.error("--output must be specified.")

if args.palette is None:
    arg_parser.error("--palette must be specified.")

if not (args.format in IMPORT_FORMATS):
    valid_options_str = ""
    for opt in IMPORT_FORMATS.keys():
        valid_options_str += f"\"{opt}\": {IMPORT_FORMATS[opt]}\n"

    arg_parser.error(
        f"'{args.format}' is not a valid import format(make sure you are using the correct letter cases). \
            the valid ones are:\n{valid_options_str}"
    )

if not (args.color_match_mode in COLOR_MATCH_MODES):
    valid_options_str = ""

    for opt in COLOR_MATCH_MODES.keys():
        valid_options_str += f"\"{opt}\": {COLOR_MATCH_MODES[opt][1]}\n"

    arg_parser.error(
        f"'{args.color_match_mode}' is not a valid color matching mode (make sure you are using the correct letter cases). \
            the valid ones are:\n{valid_options_str}"
    )


log_info("Reading palette from: " + args.palette)

col_palette = Palette.from_file(args.palette)

log_info("Palette construction complete")


log_info("Reading input from: " + args.input)
input_img = Image.open(args.input)
iwidth, iheight = input_img.size

log_info(f"Found source dimension: {iwidth}x{iheight}")

owidth = iwidth
oheight = iheight

if args.dimensions != "original":
    try:
        owidth, oheight = parse_dimension_arg(args.dimensions)


    except Exception as e:
        arg_parser.error(
            f"'{args.dimensions}' is not a valid dimension: {e}"
        )

log_info(f"Found target dimension: {owidth}x{oheight}")

if iwidth != owidth or iheight != oheight:
    log_info("Found size difference, resizing using NEAREST filtering method")
    input_img = input_img.resize((owidth, oheight), Image.NEAREST)
    log_info("resize complete")

pixels = input_img.load()


render_time_begin = time.time()
log_info("Constructing Spells and colors...")
log_info("using color match mode: " + args.color_match_mode)

bayer_mat2_2 = list(map(lambda x: x / 4 - 0.5, [
    0, 2, 3, 1
]))

rendered_color_matches = [None] * owidth * oheight

# checks whether or not a point is within a rect (assumed to 0, 0 top left)
def in_rect(x: int, y: int, width: int, height: int) -> bool:
    return not (x < 0 or x >= width or y < 0 or y >= height)

pixel_errors = [(0, 0, 0)] * owidth * oheight

def flatten_2d(x: int, y: int, width: int) -> int:
    return y * width + x

# def try_add_error_at(x: int, y: int, width: int, height: int, error: (float, float, float), mult: float, px_errors) -> bool:
#     if in_rect(x, y, width, height):
#         dr, dg, db = error
#
#         or, og, ob = px_errors[flatten_2d(x, y, width)]
#
#         or += dr
#         og += dg
#         ob += db
#
#         px_errors[flatten_2d(x, y, width)] = (or, og, ob)
#
#         return True
#     # else
#
#     return False


def render_pixel(x: int, y: int) -> ColorMatch:
    pixel_color = Colori.from_rgba_tuple(pixels[x, y])

    match_mode = COLOR_MATCH_MODES[args.color_match_mode][0]

    if args.dither:
        # bayer matrix
        bayer_mat_pos = [
            x % 2, y % 2
        ]

        mat_val_mapped = bayer_mat2_2[bayer_mat_pos[1] * 2 + bayer_mat_pos[0]] * 35

        pixel_color.r = pixel_color.r + mat_val_mapped
        pixel_color.g = pixel_color.g + mat_val_mapped
        pixel_color.b = pixel_color.b + mat_val_mapped

        pixel_color = pixel_color.saturated()

        # flyoid-steinberg
        # palette_match_ptimer.begin_append()
        # corrected_color = pixel_color
        #
        # prev_error = pixel_errors[flatten_2d(x, y, owidth)]
        #
        # corrected_color.r += prev_error.r
        # corrected_color.g += prev_error.g
        # corrected_color.b += prev_error.b
        #
        # result_match = col_palette.find_closest_match(corrected_color.saturated(), match_mode)
        # palette_match_ptimer.end_append()
        #
        # new_error = pixel_color.get_channel_linear_dist_to(
        #     result_match.get_color()
        # )
        #
        # try_add_error_at(x + 1, y,     owidth, oheight, new_error * (7.0 / 16.0), pixel_errors)
        # try_add_error_at(x - 1, y + 1, owidth, oheight, new_error * (3.0 / 16.0), pixel_errors)
        # try_add_error_at(x,     y + 1, owidth, oheight, new_error * (5.0 / 16.0), pixel_errors)
        # try_add_error_at(x + 1, y + 1, owidth, oheight, new_error * (1.0 / 16.0), pixel_errors)
        
        
        
        
        
    palette_match_ptimer.begin_append()
    result_match = col_palette.find_closest_match(pixel_color, match_mode)
    palette_match_ptimer.end_append()

    return result_match

# sx sy refer to top left (min), ex ey refer to bottom right (max)
def render_pixel_rect_to(sx: int, sy: int, ex: int, ey: int, img_width: int, img_height: int, dest):
    # + 1 due to exclusivity of range maximum
    for y in range(sy, ey + 1):
        for x in range(sx, ex + 1):
            dest[y * img_width + x] = render_pixel(x, y)

## render color pairs
pixel_match_render_ptimer.begin_append()

DEFAULT_STRIP_COUNT = 5

strip_height = int(oheight / DEFAULT_STRIP_COUNT)

# the remaining last strip's height
rem_strip_height = oheight - (strip_height * DEFAULT_STRIP_COUNT)

## threading is not efficient in python
## Process worker may be an option here
for ti in range(DEFAULT_STRIP_COUNT):
    sy = ti * strip_height
    ey = (ti + 1) * strip_height - 1

    # we append the last strip height if there is any
    if ti == DEFAULT_STRIP_COUNT - 1:
        ey += rem_strip_height

    render_pixel_rect_to(
        0, sy,
        owidth - 1, ey,
        owidth, oheight, rendered_color_matches
    )

pixel_match_render_ptimer.end_append()

## process color pairs

spell_str_io = StringIO()
spell_str_io.write("ACCELERATING_SHOT,LINE_ARC,LONG_DISTANCE_CAST\n")

spell_count = 0

preview_pixels = [
]

for x in range(owidth):
    is_last_col = x == owidth - 1

    str_render_ptimer.begin_append()

    spell_str_io.write(",")
    spell_str_io.write(
        begin_column_str(is_last_col, args.manainf)
    )
    spell_str_io.write("\n")

    str_render_ptimer.end_append()

    col_pixels = []

    for y in range(oheight):
        is_last_row = y == oheight - 1

        color_pair_match: ColorMatch = rendered_color_matches[y * owidth + x]

        match_color_spell_name = color_pair_match.get_action()

        str_render_ptimer.begin_append()

        spell_str_io.write(",")
        spell_str_io.write(
            make_pixel_str(is_last_row, match_color_spell_name, args.manainf)
        )

        str_render_ptimer.end_append()

        match_color = color_pair_match.get_color()

        col_pixels.append(match_color.to_tuple())
        pass

    str_render_ptimer.begin_append()

    spell_str_io.write("\n")
    spell_str_io.write(end_column_str(is_last_col))

    str_render_ptimer.end_append()

    preview_pixels.append(col_pixels)


render_time_total_secs = time.time() - render_time_begin
log_info(f"Render Complete, took {render_time_total_secs} seconds")

# TODO: probably can simplify this, by just grouping all of them together and forloop
# but for now this should suffice
log_info(f"-- string rendering took {str_render_ptimer.get_total_seconds()} seconds, \
    {str_render_ptimer.get_total_seconds() / render_time_total_secs * 100}%")

log_info(f"-- pixel match rendering took {pixel_match_render_ptimer.get_total_seconds()} seconds, \
    {pixel_match_render_ptimer.get_total_seconds() / render_time_total_secs * 100}%")

log_info(f"-- palette match rendering took {palette_match_ptimer.get_total_seconds()} seconds, \
    {palette_match_ptimer.get_total_seconds() / render_time_total_secs * 100}%")

if args.preview is not None:
    log_info("Creating preview...")
    preview_pixels_array = np.array(preview_pixels, dtype=np.uint8)
    preview_img = Image.fromarray(preview_pixels_array)
    preview_img = preview_img.transpose(Image.TRANSPOSE)

    log_info("Saving preview to file: " + args.preview)

    preview_img.save(args.preview)

    log_info("Preview complete...")

log_info("Creating import string...")

res_import_str = ""

if args.format == "wiki_wand":
    log_info("Using 'wiki_wand' format")
    res_import_str += ("""
    {{Wand2
    | wandPic      = Wand 0821.png\n""")

    res_import_str += f"""
    | capacity     = {len(spell_str_io.getvalue().split(','))}\n"""

    res_import_str += ("""
    | manaMax      = 100000.00
    | manaCharge   = 100000.00
    | spells       = """)

    res_import_str += (spell_str_io.getvalue()) + "\n"

    res_import_str += ("""
    }}
    """)

else:
    log_info("Using 'default' format")
    res_import_str = spell_str_io.getvalue()

log_info("Finished generating import string!")

if args.output == "-":
    log_info("Writing to output")
    log_info(res_import_str)

else:
    log_info("Writing to " + args.output)
    with open(args.output, "w") as result_file:
       result_file.write(res_import_str)

if args.clipboard_copy is True:
    log_info("Copying to clipboard...")

    xerox.copy(res_import_str)

    log_info("Clipboard copying complete!")

log_info("Clean up")
spell_str_io.close()
