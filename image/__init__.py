# Tools for generating logic gates
__author__ = "Matteo Golin"

# Imports
from PIL import Image
import numpy as np
import os
from progress.bar import IncrementalBar

# Constants

# Folders
ASSET_FOLDER = "assets"
OUTPUT_FOLDER = "output"
SCHEMATIC_FOLDER = f"{OUTPUT_FOLDER}/schematics"
GATES_FOLDER = f"{ASSET_FOLDER}/gates"
INPUTS_FOLDER = f"{ASSET_FOLDER}/inputs"
NUMBERING_FOLDER = f"{ASSET_FOLDER}/numbering"
WIRES_FOLDER = f"{ASSET_FOLDER}/wires"

# Symbols for schematics
GATE_GENER = "□"  # Generic gate symbol
WIRES = {
    "fork": u'\u2524',
    "merge": "2",  # Changing this breaks the program somehow
    "run": "|",
    "dual up": "4",
    "dual down": "5",
    "dual bend up": "6",
    "dual bend down": "7",
    "curve up": u'\u2518',
    "curve down": u'\u2510'
}
GATES = {
    "&": "and",
    "*": "nand",
    ")": "or",
    "(": "nor",
    "%": "xnor",
    "^": "xor"
}

GRID_SIZE = (17, 17)  # Width, height
NUM_SIZE = (5, 5)  # Width, height

# Colours
TRANSPARENT = (255, 0, 0, 0)
BG = (150, 162, 179, 255)

# Images
GATE_IMAGES = {
    "and": Image.open(f"{GATES_FOLDER}/and.png"),
    "or": Image.open(f"{GATES_FOLDER}/or.png"),
    "nand": Image.open(f"{GATES_FOLDER}/nand.png"),
    "nor": Image.open(f"{GATES_FOLDER}/nor.png"),
    "xor": Image.open(f"{GATES_FOLDER}/xor.png"),
    "xnor": Image.open(f"{GATES_FOLDER}/xnor.png")
}
WIRE_IMAGES = {
    WIRES["fork"]: Image.open(f"{WIRES_FOLDER}/fork.png"),
    WIRES["merge"]: Image.open(f"{WIRES_FOLDER}/merge.png"),
    WIRES["run"]: Image.open(f"{WIRES_FOLDER}/run.png"),
    WIRES["dual up"]: Image.open(f"{WIRES_FOLDER}/dualUp.png"),
    WIRES["dual down"]: Image.open(f"{WIRES_FOLDER}/dualDown.png"),
    WIRES["dual bend up"]: Image.open(f"{WIRES_FOLDER}/dualBendUp.png"),
    WIRES["dual bend down"]: Image.open(f"{WIRES_FOLDER}/dualBendDown.png"),
    WIRES["curve up"]: Image.open(f"{WIRES_FOLDER}/curveUp.png"),
    WIRES["curve down"]: Image.open(f"{WIRES_FOLDER}/curveDown.png")
}

INPUT_IMAGES = {}
for filename in os.listdir(INPUTS_FOLDER):
    INPUT_IMAGES[filename.replace(".png", "")] = Image.open(f"{INPUTS_FOLDER}/{filename}")

NUMBER_IMAGES = {}
for filename in os.listdir(NUMBERING_FOLDER):
    NUMBER_IMAGES[filename.replace(".png", "")] = Image.open(f"{NUMBERING_FOLDER}/{filename}")


# Basic image functions
def rescale(img: Image.Image, scale_factor: int) -> Image.Image:

    """Rescales the image by a given factor using the nearest neighbour method. Returns the scaled image."""

    width, height = img.size
    new_dimensions = width * scale_factor, height * scale_factor

    scaled_img = img.resize(new_dimensions, Image.NEAREST)

    return scaled_img


# Create number tag
def number_tag(num: int) -> Image.Image:

    """Creates a pixel art number tag given a number."""

    num = str(num)  # Convert number to string

    # Dimensions for tag
    height = NUM_SIZE[1]
    width = (len(num) + 1) * NUM_SIZE[0]

    # Create base image with '#'
    base = Image.new("RGBA", (width, height), TRANSPARENT)
    base.paste(NUMBER_IMAGES["#"])

    for _ in range(len(num)):
        x = (_ + 1) * 5  # Y coordinate
        base.paste(NUMBER_IMAGES[num[_]], (x, 0))  # Paste corresponding number in its place

    return base


# Create image from grid
def image_from_grid(grid: np.ndarray) -> Image.Image:

    """Creates an image from the grid passed and saves it with with the specified filename."""

    # Dimensions
    grid = np.rot90(grid)
    n, width = grid.shape
    new_width, new_height = width * GRID_SIZE[0], n * GRID_SIZE[1]

    # Create the base image
    base = Image.new('RGBA', (new_width, new_height), TRANSPARENT)

    # Iterate through grid
    for row in range(n):
        for column in range(width):

            do_nothing = False  # Assume we will find a gate or wire

            # Found gate
            if grid[row][column] in GATES:
                cell = GATE_IMAGES[GATES[grid[row][column]]]  # Get gate image

            # Found wire
            elif grid[row][column] in WIRES.values():
                cell = WIRE_IMAGES[grid[row][column]]  # Get the corresponding wire image

            # Empty
            elif grid[row][column] == " ":
                do_nothing = True  # Do nothing

            # Input
            else:
                cell = INPUT_IMAGES[grid[row][column]].transpose(Image.ROTATE_270)  # Rotate too

            if not do_nothing:  # We found a gate or wire

                # Traverse x and y by a factor of GRID_SIZE
                x = column * GRID_SIZE[1]
                y = row * GRID_SIZE[0]

                base.paste(cell, (x, y))  # Paste the cell where it belongs

    return base


def add_background(schematic: Image.Image) -> Image.Image:

    """Adds background to transparent schematic PNG."""

    # Create background
    background = Image.new("RGBA", schematic.size, BG)

    # Add schematic to background
    composite = Image.alpha_composite(background, schematic)

    return composite


def create_image_batch(unique_grids: dict[int, np.ndarray], filename: str, scalar=1):

    """
    Creates a batch of images from the given grid layout, and returns the gate combinations for each schematic image.
    """

    versions = len(unique_grids)  # Number of version
    bar = IncrementalBar("Images", max=versions)  # Progress bar

    for _ in range(versions):

        # Progress display
        bar.next()

        # Image making
        schematic = image_from_grid(unique_grids[_])  # Get transparent schematic and its gate list

        schematic = schematic.transpose(Image.ROTATE_90)  # Rotate 90 deg
        tag = number_tag(_ + 1)  # Create tag image
        schematic.paste(tag, (1, 1))  # Add tag to image

        final = add_background(schematic)  # Add a background

        # Optional rescaling
        if scalar != 1:  # If a scale factor is passed
            final = rescale(final, scalar)  # Rescale

        final.save(f"{SCHEMATIC_FOLDER}/{filename} #{_ + 1}.png")  # Save to output folder

    bar.finish()
