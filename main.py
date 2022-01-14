# Main script for generating logic gates
__author__ = "Matteo Golin"

# Imports
import numpy as np
import time
from schematic import create_grid, wire_grid, create_grid_batch, count_gates, validate_version_count, get_gate_coords
from image import create_image_batch
from karnaugh import create_map_array, create_kmap_batch, grid_output_trees
from commands import parser, clear_output

np.set_printoptions(threshold=np.inf)  # Prints more grids without them getting cut off

# Program parameters
arguments = parser.parse_args()

inputs = arguments.i
versions = arguments.v
scalar = arguments.s
filename = arguments.fname

# Clear the output folder
if arguments.clear:
    clear_output()

start = time.time()  # Record start time

# Create a base grid
base_grid = create_grid(inputs)  # Create the grid
wire_grid(base_grid)  # Wire the grid
gate_count = count_gates(base_grid)  # Count how many gates are in the grid

validate_version_count(versions, gate_count, inputs)  # Ensure that the version count is <= # of possible permutations

print("Grid layout created.\n")  # Display that the grid layout has been created

# Create batch of random grids
unique_grids = create_grid_batch(base_grid, versions)
print()

# Karnaugh maps
kmap = create_map_array(inputs)  # Base Karnaugh map
final_gate = get_gate_coords(base_grid)[-1]  # Starting point to find outputs of a schematic
trees = grid_output_trees(base_grid, kmap, final_gate)  # Generate output trees for the base schematic
print()
unique_kmaps = create_kmap_batch(kmap, unique_grids, trees, filename)  # Get unique Karnaugh maps
print()

# Create images
create_image_batch(unique_grids, filename, scalar)
print()

end = time.time()  # Record end time

print(f"Generation completed in {time.strftime('%H:%M:%S', time.gmtime(end - start))}")  # Success message
