# Command line arguments
__author__ = "Matteo Golin"

# Imports
import argparse as ap
import os
from image import INPUT_IMAGES, OUTPUT_FOLDER

# Parser
DESC = "Creates a set of logic gate tree schematics of a size defined by the user using pre-made sprites. Sets contain no" \
       "duplicates."
parser = ap.ArgumentParser(description=DESC)


# Custom type
def int_above_0(arg):

    """Type function for argparse that ensures an integer above 0."""

    # Ensure integer
    try:
        value = int(arg)
    except ValueError:
        raise ap.ArgumentTypeError(f"Must be an integer. (GOT: {arg})")

    # Ensure above 0
    if not value > 0:
        raise ap.ArgumentTypeError(f"Integer must be greater than 0. (GOT: {arg})")

    return value  # Integer above 0


# Get filename
parser.add_argument(
    "-fname",
    metavar="file name",
    required=True,
    help="The filename which the images will be saved under.",
    type=str
)

# Number of versions
parser.add_argument(
    "-v",
    help="Specifies the number of random versions to be made using the schematic layout.",
    type=int_above_0,  # Must be an integer above 0
    metavar="versions",
    required=True
)

# Number of inputs
parser.add_argument(
    "-i",
    help="Specifies the number of inputs to be used in the schematic image.",
    type=int,
    metavar="inputs",
    choices=range(2, len(INPUT_IMAGES)),  # Min 2 inputs and max the number of unique inputs
    default=len(INPUT_IMAGES),  # Default uses the maximum number of unique inputs
)

# Clear output folder
parser.add_argument(
    "-clear",
    help="Empties the output folder before running the program.",
    action="store_true"
)

# Scale factor
parser.add_argument(
    "-s",
    metavar="scalar",
    help="The factor by which the generated image is scaled up.",
    type=int_above_0,  # Must be an integer above 0
    default=1  # Default is 1, which means there is no scaling
)


# Function to clear output folder
def clear_output(output_folder=OUTPUT_FOLDER):

    for filename in os.listdir(output_folder):  # All files in output folder

        f_path = f"{output_folder}/{filename}"  # Path to file

        try:
            if os.path.isfile(f_path) or os.path.islink(f_path):  # Deletes files and links
                os.unlink(f_path)
            elif os.path.isdir(f_path):  # Is a directory
                clear_output(output_folder=f_path)  # Clear directory
        except Exception as e:  # Error deleting file
            print(f"Failed to delete {f_path} for reason: {e}")

