from PIL import Image
import numpy as np
from io import StringIO
import argparse
import datetime
from colori import *
from color_palette import *


## TODO:
## 1. Create a GUI that helps display, switch on and off certain settings
## 2. Allow switching between without using (Modifying directly Spell lab shugged player.xml) and with using CE
## 3. Additive Color merging, specifically for colors that are hard to represent (aka the smallest value CIEDE2k is > 5 or smth like that)
## 4. Add Optional Dithering to the mix (Bayer matrix)
## 5. Allow users to specify different size scaling of the original image (maybe compression?)


## This script assumes a few things:
## 1. You are using CE(Component Explorer)'s wiki wands to import the wands (https://noita.wiki.gg/wiki/Mod:Component_Explorer)
## 2. you need to install pillow and numpy for python (`pip install pillow numpy`) preferably in a virtual environment :P
## 3. finally, you simply need to run: python noita_pxa.py --input "input_file" --output "output_file" and you have your wand!
## 4. you can import this through  Component Explorer's "Wiki Wands" > "import" tab paste and you are good to go
## 5. you can optionally show a preview image by using the --preview "preview_file" path

def log_info(msg: str):
    ct = datetime.datetime.now()
    print(f"[{ct}][INFO] {msg}")


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

arg_parser = argparse.ArgumentParser("Noita pixel art wand generator by CxRedix")
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

args = arg_parser.parse_args()

if args.input == None:
    arg_parser.error("--input must be specified.")

if args.output == None:
    arg_parser.error("--output must be specified.")

if args.palette == None:
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
pixels = input_img.load()
width, height = input_img.size

spell_str_io = StringIO()
spell_str_io.write("ACCELERATING_SHOT,LINE_ARC,LONG_DISTANCE_CAST\n")

spell_count = 0

preview_pixels = [
]

log_info("Constructing Spells and colors...")
log_info("using color match mode: " + args.color_match_mode)
for x in range(width):
    is_last_col = x == width - 1

    spell_str_io.write(",")
    spell_str_io.write(
        begin_column_str(is_last_col, args.manainf)
    )
    spell_str_io.write("\n")

    col_pixels = []

    for y in range(height):
        is_last_row = y == height - 1

        pixel_color = Colori.from_rgba_tuple(pixels[x, y])

        match_mode = COLOR_MATCH_MODES[args.color_match_mode][0]

        match_color_pair = col_palette.find_closest_match(pixel_color, match_mode)

        match_color_spell_name = match_color_pair[1]

        spell_str_io.write(",")
        spell_str_io.write(
            make_pixel_str(is_last_row, match_color_spell_name, args.manainf)
        )

        col_pixels.append((
            match_color_pair[0].r,
            match_color_pair[0].g,
            match_color_pair[0].b,
        ))

    spell_str_io.write("\n")
    spell_str_io.write(end_column_str(is_last_col))

    preview_pixels.append(col_pixels)

log_info("Render Complete")

if args.preview != None:
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

log_info("Clean up")
spell_str_io.close()
