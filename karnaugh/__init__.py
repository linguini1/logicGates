# Module for creating Karnaugh map from grid schematic
__author__ = "Matteo Golin"

# Imports
import numpy as np
import operator
from progress.bar import IncrementalBar
from image import WIRES, GATES, OUTPUT_FOLDER, INPUT_IMAGES


# Custom boolean functions
def nand(a: bool, b: bool) -> bool:
    return not (a and b)


def nor(a: bool, b: bool) -> bool:
    return not (a or b)


def xnor(a: bool, b: bool) -> bool:
    return not (a ^ b)


# CONSTANTS
GATE_OPERATIONS = {
    "and": operator.and_,
    "or": operator.or_,
    "xor": operator.xor,
    "nand": nand,
    "nor": nor,
    "xnor": xnor
}
KMAP_FOLDER = f"{OUTPUT_FOLDER}/kmaps"


# Mathematical functions

def traverse_tree(tree: dict[str, list[str]], current_num="start", step_list=None) -> list[str] | None:

    """
    Returns a path that contains all numbers in the binary range in an order where the number only changes by one
    bit each step.
    """

    # Start at binary 0
    if current_num == "start":
        current_num = list(tree.keys())[0]
        step_list = [current_num]  # Create new step list starting at binary 0

    # Create sets for all numbers and steps
    all_number_set = set(tree.keys())
    all_steps_set = set(step_list)

    if len(all_number_set.difference(all_steps_set)) == 0:
        return step_list  # First step gets added to the end again, so remove it before returning

    # Create a tree for each possible next step
    for next_step in tree[current_num]:

        if next_step in step_list:  # Skip this step if it was already taken
            pass
        else:  # If the step can be taken, take it
            step_list.append(next_step)
            return traverse_tree(tree, current_num=next_step, step_list=step_list)


def split_gates(inputs: int) -> tuple[int, int]:

    """Splits the number of inputs across the left and right of the karnaugh map."""

    left = inputs // 2  # Larger for odd
    top = inputs - left

    return left, top


def swap_bit(number: str, bit_to_swap: int) -> str:

    """Swaps the bit at the given index and returns the new number as a string."""

    number = list(number)

    if number[bit_to_swap] == "0":
        number[bit_to_swap] = "1"
    else:
        number[bit_to_swap] = "0"

    return "".join(number)


def generate_index(inputs: int) -> list[str]:

    """
    Returns the index for the inputs along an axes of the Karnaugh map as a list of binary numbers represented as
    strings.
    """

    steps = ["0" * inputs]  # Track steps

    for step in steps:

        if len(steps) == 2 ** inputs:  # No more steps
            return steps

        for _ in range(inputs):  # Go through each bit

            next_step = swap_bit(step, _)  # Swap bit

            # If the number with the swapped bit isn't already a step, then record it and continue
            if next_step not in steps:
                steps.append(next_step)
                break


def previous_gates(grid: np.ndarray, gate_coordinates: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:

    """Returns the coordinates of the gates previous to the gate passed."""

    row, column = gate_coordinates  # Unpack coordinates
    wire_row = row - 1

    # Two gates next to each other directly behind and left
    if grid[wire_row][column] in [WIRES["dual bend up"], WIRES["dual up"]]:
        gate1 = wire_row - 1, column
        gate2 = wire_row - 1, column - 1

    # Two gates next to each other directly behind and right
    elif grid[wire_row][column] in [WIRES["dual bend down"], WIRES["dual down"]]:
        gate1 = wire_row - 1, column
        gate2 = wire_row - 1, column + 1

    # There is a merge
    elif grid[wire_row][column] == WIRES["merge"]:

        # Gate on the left
        left_column = column - 1
        while grid[wire_row][left_column] == WIRES["run"]:  # Continue down a line of straight wire until curve reached
            left_column -= 1
        gate1 = wire_row - 1, left_column

        # Gate on right
        right_column = column + 1
        while grid[wire_row][right_column] == WIRES["run"]:  # Continue down a line of straight wire until curve reached
            right_column += 1
        gate2 = wire_row - 1, right_column

    return gate1, gate2


def output_tree(grid: np.ndarray, gate_coordinates: tuple[int, int], input: str) -> dict:

    stack = [gate_coordinates]  # Create the stack of gates to be explored
    tree = {}  # Empty dictionary to store the tree structure
    input = list(reversed(input))  # Reverse the input so index 0 lines up with input a

    for gate in stack:  # Go through the stack

        previous_gate1, previous_gate2 = previous_gates(grid, gate)  # Get the two previous gates

        if previous_gate1[0] == 0:  # Found a pair of inputs

            # Set the input equal to its value set by the input
            previous_gate1 = input[previous_gate1[1]]
            previous_gate2 = input[previous_gate2[1]]

        else:  # We found a pair of gates
            stack.extend([previous_gate1, previous_gate2])  # Add the gates to the stack to be explored

        # Store the gates/inputs in the tree structure
        tree[gate] = [previous_gate1, previous_gate2]

    return tree


def grid_output_trees(grid: np.ndarray, kmap: np.ndarray, final_gate: tuple[int, int]) -> dict[tuple, dict]:

    """Creates a list of all possible output trees for a given base schematic."""

    height, width = kmap.shape  # Dimensions
    trees = {}  # Dictionary to store trees
    bar = IncrementalBar("Output Trees", max=(height - 1) * (width - 1))  # Progress bar

    for row in range(1, height):
        for column in range(1, width):

            bar.next()  # Progress

            # Combines the inputs into one string where each bit corresponds to an input
            left_inputs = kmap[row][0]
            top_inputs = kmap[0][column]
            inputs = left_inputs + top_inputs

            # Get the tree of the input
            tree = output_tree(grid, final_gate, inputs)

            # Store the tree in the dictionary
            trees[(row, column)] = tree

    bar.finish()

    return trees


def evaluate_tree(grid: np.ndarray, tree: dict) -> bool:

    """Evaluates the given tree into a single boolean output."""

    tree = tree.copy()  # Important to not modify original tree
    order = list(reversed(tree.keys()))  # Reverse the list so we evaluate from inputs upward
    final_gate = list(tree.keys())[0]  # Final gate coordinates

    for key in order:

        data_type = type(tree[key][0])

        if data_type == tuple:  # Gate found

            gate1, gate2 = tree[key]  # Unpack gates

            # Check if the gates listed have been evaluated
            if type(tree[gate1][0]) == bool and type(tree[gate2][0]) == bool:

                # Get the operation of the gate used as key
                operation = GATE_OPERATIONS[GATES[grid[key[0]][key[1]]]]

                gate1, gate2 = tree[gate1][0], tree[gate2][0]  # Unpack inputs
                result = operation(gate1, gate2)  # Apply boolean operation

                # Store result under gate coordinates
                tree[key] = [result]  # Stored in list to prevent error with variable data_type's initialization

        else:  # Input found

            # Get the operation of the gate used as key
            operation = GATE_OPERATIONS[GATES[grid[key[0]][key[1]]]]

            in1, in2 = tree[key]  # Unpack inputs
            result = operation(bool(int(in1)), bool(int(in2)))  # Apply boolean operation

            # Store result under gate coordinates
            tree[key] = [result]  # Stored in list to prevent error with variable data_type's initialization

    return tree[final_gate][0]


# Visualization functions
def create_map_array(inputs: int) -> np.ndarray:

    """Returns an empty array representation of the Karnaugh map given the number of inputs."""

    top, left = split_gates(inputs)  # Split inputs across axes of Karnaugh map

    # Generate labels for each axes of the Karnaugh map
    left_index = generate_index(left)
    top_index = generate_index(top)

    # Karnaugh map full of 0s
    height, width = len(left_index) + 1, len(top_index) + 1  # Dimensions (additional row and column for labels)
    kmap = np.full((height, width), "0", dtype=object)  # Populate with false, only true will need to be recorded

    # Filling labels
    kmap[0][0] = "#"  # Unused corner

    # Fill left column with left labels
    for _ in range(len(left_index)):
        kmap[_ + 1][0] = left_index[_]

    # Fill top row with top labels
    for _ in range(len(top_index)):
        kmap[0][_ + 1] = top_index[_]

    return kmap


def populate_map(kmap: np.ndarray, grid: np.ndarray, trees: dict[tuple, dict]) -> np.ndarray:

    """Returns the populated Karnaugh map of a given schematic."""

    new_kmap = kmap.copy()  # Create a copy of the kmap so the base isn't modified.
    height, width = kmap.shape  # Dimensions

    for row in range(1, height):
        for column in range(1, width):

            # Get the result of the input
            coord = (row, column)
            tree = trees[coord]
            output = evaluate_tree(grid, tree)

            # Store the input at the current spot
            new_kmap[row][column] = int(output)

    return new_kmap


def save_kmap(kmap: np.ndarray, filename: str, index: int):

    """Saves the Karnaugh map to a text file, completely formatted."""

    longest_char = len(kmap[1][0])  # Calculate the longest character for spacing

    with open(f"{KMAP_FOLDER}/{filename} #{index + 1}.txt", 'w') as file:  # Open file for writing

        # Write which inputs are on which side
        left, top = longest_char, len(kmap[0][1])  # Determining the amount of inputs on each side
        input_names = list(INPUT_IMAGES.keys())  # Names of inputs

        # Left side inputs
        file.write("Left side inputs: ")
        for _ in range(left):
            if _ == left - 1:  # No comma on final input in list
                file.write(input_names[_] + "\n")
            else:
                file.write(input_names[_] + ", ")

        # Top side inputs
        file.write("Top side inputs: ")
        for _ in range(left, left + top):
            if _ == left + top - 1:  # No comma on final input in list
                file.write(input_names[_] + "\n\n")
            else:
                file.write(input_names[_] + ", ")

        for row in kmap:
            new_row = ""  # Initialize new row
            for value in row:
                new_row += f"{value}{' ' * (longest_char - len(str(value)) + 1)}"  # Store the formatted row information
            file.write(new_row + "\n")  # Save the row to its file


# Batch functions
def create_kmap_batch(kmap: np.ndarray, unique_grids: dict, trees: dict[tuple, dict], filename: str) -> dict:

    """
    Returns a dictionary of Karnaugh maps that match the batch of unique schematics passed. Saves the maps to a text
    file.
    """

    unique_kmaps = {}  # Dictionary to store Karnaugh maps
    num_grids = len(unique_grids)
    bar = IncrementalBar("Karnaugh Maps", max=num_grids)  # Progress bar

    # Loop through all schematics
    for _ in range(num_grids):

        # Progress display
        bar.next()

        # Create the Karnaugh map for each schematic and save it under the index matching its schematic
        new_kmap = populate_map(kmap, unique_grids[_], trees)  # Get the matching truth table
        unique_kmaps[_] = new_kmap  # Store it in a dictionary
        save_kmap(new_kmap, filename, _)  # Save to text file

    bar.finish()

    return unique_kmaps
