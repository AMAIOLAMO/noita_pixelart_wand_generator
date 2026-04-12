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
    if is_col_end == False:
        result += "BURST_2,"

    ## FIREBOMB
    if inf_mana == False:
        result += "BLOOD_MAGIC,BLOOD_MAGIC,"

    ## FIREBOMB REGULAR
    # result += "NOLLA,SUPER_TELEPORT_CAST,BURST_3,ZERO_DAMAGE,ZERO_DAMAGE," + color_spell_name + \
    #         ",FIREBOMB,ADD_TRIGGER,CASTER_CAST,DIGGER,PURPLE_EXPLOSION_FIELD,SUPER_TELEPORT_CAST"

    ## FIREBOMB TENTACLE TIMER
    result += "LIFETIME_DOWN,LIFETIME_DOWN,TENTACLE_TIMER,ZERO_DAMAGE,ZERO_DAMAGE," + color_spell_name + \
            ",FIREBOMB,SPEED,SUPER_TELEPORT_CAST"

    ## FIREBOMB TRANSMUTE too laggy
    # result += "NOLLA,SUPER_TELEPORT_CAST,BURST_3,BLOOD_MAGIC,BLOOD_MAGIC,ZERO_DAMAGE,ZERO_DAMAGE," + color_spell_name + ",FIREBOMB,TRANSMUTATION,PURPLE_EXPLOSION_FIELD,SUPER_TELEPORT_CAST"
    return result

def begin_column_str(inf_mana: bool = False) -> str:
    ## FIREBOMB
    result = ""

    if inf_mana == False:
        result += "BLOOD_MAGIC,BLOOD_MAGIC,"

    ## FIREBOMB REGULAR
    # result += "BURST_2,NOLLA,SUPER_TELEPORT_CAST,ADD_DEATH_TRIGGER,NOLLA,GRAVITY,DIGGER"

    # FIREBOMB TENTACLE TIMER
    result += "BURST_2,LIFETIME_DOWN,SUPER_TELEPORT_CAST,ADD_DEATH_TRIGGER,NOLLA,GRAVITY,DIGGER"

    return result 

### ====== CLI ====== ###

arg_parser = argparse.ArgumentParser("Noita pixel art wand generator by CxRedix")
arg_parser.add_argument(
    '-i', '--input', type=str,
    help="The input png file to start converting from, preferably lower than 128x128"
)

arg_parser.add_argument(
    '-o', '--output', type=str,
    help="The output text file to write the Wiki wand import to"
)

arg_parser.add_argument(
    '-p', '--palette', type=str,
    help="The color palette to use in json format."
)

arg_parser.add_argument(
    '-P', '--preview', type=str, nargs="?",
    help="Optional preview png file to preview the final colors"
)

arg_parser.add_argument(
    '-m', '--manainf', action="store_true",
    help="Optionally specify whether the wand should assume that it has infinite mana or not. Helps lessen the amount of spells."
)

args = arg_parser.parse_args()

if args.input == None:
    arg_parser.error("--input must be specified.")

if args.output == None:
    arg_parser.error("--output must be specified.")

if args.palette == None:
    arg_parser.error("--palette must be specified.")


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
for x in range(width):
    spell_str_io.write(",")
    spell_str_io.write(begin_column_str(args.manainf))
    spell_str_io.write("\n")

    col_pixels = []

    for y in range(height):
        is_end = y == height - 1

        pixel_color = Colori.from_rgba_tuple(pixels[x, y])

        match_color_pair = col_palette.find_closest_match(pixel_color, ColorMatchMode.DE2000)

        match_color_spell_name = match_color_pair[1]

        spell_str_io.write(",")
        spell_str_io.write(make_pixel_str(is_end, match_color_spell_name, args.manainf))

        col_pixels.append((
            match_color_pair[0].r,
            match_color_pair[0].g,
            match_color_pair[0].b,
        ))


    preview_pixels.append(col_pixels)
    
    spell_str_io.write("\n")

log_info("Render Complete")

if args.preview != None:
    log_info("Creating preview...")
    preview_pixels_array = np.array(preview_pixels, dtype=np.uint8)
    preview_img = Image.fromarray(preview_pixels_array)
    preview_img = preview_img.transpose(Image.TRANSPOSE)

    log_info("Saving preview to file: " + args.preview)

    preview_img.save(args.preview)

    log_info("Preview complete...")

log_info("Creating ce import string...")
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

log_info("Finished ce import string...")

if args.output == "-":
    log_info("Writing to output")
    log_info(ce_import_str)

else:
    log_info("Writing to " + args.output)
    with open(args.output, "w") as result_file:
       result_file.write(ce_import_str)

log_info("Clean up")
spell_str_io.close()
