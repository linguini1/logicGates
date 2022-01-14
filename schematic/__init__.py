# Tools for generating logic gate schematics
__author__ = "Matteo Golin"

# Imports
import collections
import numpy as np
import operator
import random
from progress.bar import IncrementalBar
from image import INPUT_IMAGES, WIRES, GATE_GENER, GATES


# Functions
def create_grid(inputs: int) -> np.ndarray:

    """
    Returns a grid of size dimension x dimension, populated with inputs in the first column.
    """

    # Character symbols for inputs
    characters = list(INPUT_IMAGES.keys()) * (inputs // 26 + 1)

    # Calculating necessary grid length based on inputs
    bin_length = len(str(bin(inputs - 1))) - 2
    width = 2 * bin_length + 1

    grid = np.full((width, inputs), " ")
    grid[0] = [characters[_] for _ in range(inputs - 1, -1, -1)]

    return grid


def wire_inputs(grid: np.ndarray):

    """Connects wires to the input row of the grid."""

    # Wire row = grid[1]

    n = len(grid[0])  # Number of inputs
    center_most = (n - 1) // 2  # Center-most input

    if n % 2 != 0:  # If n is odd

        if ((n - 1) / 2) % 2 != 0:  # If (n - 1) / 2 is odd
            grid[1][center_most] = WIRES["fork"]  # Center most input is forked

            # Wires above and below fork bend to converge with above and below inputs
            grid[1][center_most + 1] = WIRES["dual up"]
            grid[1][center_most - 1] = WIRES["dual down"]

        else:
            grid[1][center_most + 1] = WIRES["fork"]  # Input just above center-most is forked

            # Wires above and below fork bend to converge with above and below inputs
            grid[1][center_most + 2] = WIRES["dual up"]
            grid[1][center_most] = WIRES["dual down"]

        # Now all that are left are input pairs, so I can iterate through pairs the same way I did evens, and just
        # check if the places are filled

        for _ in range(n):
            if grid[1][_] == " ":  # Check if point is empty first

                # I know that if the first cell I run into is empty, the one below it should be as well because of
                # how the inputs pair up after the forking is complete.

                if _ > center_most:  # Above center point
                    grid[1][_] = WIRES["dual down"]  # Top
                    grid[1][_ + 1] = WIRES["curve down"]  # Bottom
                else:  # Below center point
                    grid[1][_] = WIRES["curve up"]  # Top
                    grid[1][_ + 1] = WIRES["dual up"]  # Bottom

    else:  # If n is even

        for _ in range(0, n, 2):  # Count by twos because wiring can be done in pairs

            if _ > center_most:  # Above center point
                grid[1][_] = WIRES["dual down"]  # Top
                grid[1][_ + 1] = WIRES["curve down"]  # Bottom
            else:  # Below center point
                grid[1][_] = WIRES["curve up"]  # Top
                grid[1][_ + 1] = WIRES["dual up"]  # Bottom

    return grid


def add_gates(grid: np.ndarray, row: int):

    """Adds gates to the current row."""

    n = len(grid[0])  # Number of inputs

    for _ in range(n):

        # A gate will come after any cell containing two wires, so any 'dual' cell or a merge cell.
        connection_points = ["2", "4", "5", "6", "7"]

        if grid[row - 1][_] in connection_points:  # If the cell directly behind is a connection point
            grid[row][_] = GATE_GENER  # Add a random gate to the cell


def bridge_gaps(grid: np.ndarray, gate_row: int, gate_index: int, action="pair"):

    """Bridges any size gap between gates for easy wiring."""

    n = len(grid[0])  # Number of inputs
    center_most = (n - 1) // 2  # Center most input
    wire_row = gate_row + 1  # Row where wires are placed

    def the_beef(operation):

        # Method of counting for next gate
        if operation == operator.add:
            next_gate_direction = range(gate_index + 1, n)  # Upward to the right
            curve_extremity = WIRES["curve down"]  # Found gate curves down
        else:
            next_gate_direction = range(gate_index - 1, 0, -1)  # Downward to the left
            curve_extremity = WIRES["curve up"]  # Found gate curves up

        # Look for next gate
        for _ in next_gate_direction:
            if grid[gate_row][_] == GATE_GENER:
                found_gate = _
                break

        difference = abs(gate_index - found_gate)  # How many spaces between gates

        if difference == 1:  # Next to each other

            if action == "pair":  # Pairing
                if abs(center_most - gate_index) > abs(center_most - found_gate):  # Bottom gate closer
                    grid[wire_row][gate_index] = WIRES["dual bend down"]
                    grid[wire_row][found_gate] = WIRES["curve down"]

                else:  # Top gate closer
                    grid[wire_row][gate_index] = WIRES["curve up"]
                    grid[wire_row][found_gate] = WIRES["dual bend up"]

            else:  # Forking

                if operation == operator.add:  # Gate immediately right
                    grid[wire_row][found_gate] = WIRES["dual bend up"]
                else:  # Gate immediately left
                    grid[wire_row][found_gate] = WIRES["dual bend down"]

        else:  # There is a space
            if difference % 2 != 0:  # Even amount of spaces

                # The two center-most points
                midpoints = operation(gate_index, difference // 2), operation(gate_index, difference // 2 + 1)

                # Determines where merge is placed (placed at point closest to center
                if abs(center_most - midpoints[0]) < abs(center_most - midpoints[1]):
                    closest_to_center = midpoints[0]
                else:
                    closest_to_center = midpoints[1]

            else:  # Odd amount of spaces
                closest_to_center = operation(gate_index, round(difference / 2))  # Midpoint

            # Key points that stay consistent
            grid[wire_row][closest_to_center] = WIRES["merge"]
            grid[wire_row][found_gate] = curve_extremity

            # Counting direction for adding runs
            if operation == operator.add:
                count_direction = range(gate_index, found_gate)  # Count UP from found gate
            else:
                count_direction = range(found_gate, gate_index)  # Count DOWN from found gate

            # The rest become runs
            for _ in count_direction:  # Count UP from found gate
                if grid[wire_row][_] == " ":  # If the spot is empty
                    grid[wire_row][_] = WIRES["run"]

    if action == "pair":

        # Gate always curves up
        grid[wire_row][gate_index] = WIRES["curve up"]

        # Proceed in rightward direction
        the_beef(operator.add)

    else:  # Fork

        # Gate is always forked
        grid[wire_row][gate_index] = WIRES["fork"]

        # Right side
        the_beef(operator.add)

        # Left side
        the_beef(operator.sub)


def wire_gates(grid: np.ndarray, row: int):

    """Wires logic gates together in the current row."""

    row -= 1  # Quick fix so that I can pass the CURRENT row without rewriting the code lol

    n = len(grid[0])  # Number of inputs
    num_of_gates = collections.Counter(grid[row])[GATE_GENER]  # Number of gates in the row
    center_gate = (num_of_gates - 1) // 2 + 1  # Center most gate

    if num_of_gates % 2 != 0:  # If num_of_gates is odd

        if ((num_of_gates - 1) / 2) % 2 == 0:  # If (num_of_gates - 1) / 2 is not odd
            center_gate += 1  # We want to fork the gate just above the center-most gate

        gate_counter = 0  # Keep track of gates so we can find center-most gate
        for _ in range(n):

            # Increase gate counter when we find a gate
            if grid[row][_] == GATE_GENER:
                gate_counter += 1

            # Center most gate found
            if gate_counter == center_gate:
                bridge_gaps(grid, row, _, action="fork")
                break

    # Now that all the forks have been placed and wired, I must wire pairs in the same way that is done for even
    # numbers of gates

    for _ in range(n):
        if grid[row + 1][_] == " ":  # Gate is skipped if it's already wired
            if grid[row][_] == GATE_GENER:  # Found a gate
                bridge_gaps(grid, row, _)


def wire_grid(grid: np.ndarray, row=1):

    """Wires the entire grid."""

    n = len(grid[0])  # Number of inputs

    # Wires the input row
    if row == 1:
        wire_inputs(grid)

    # Adds gates every second row (even numbered)
    elif row % 2 == 0:
        add_gates(grid, row)

        # End condition: one single gate means we've reached the end of our schematic
        if collections.Counter(grid[row])[GATE_GENER] == 1:
            return grid, row

    # Wires gates every second row (odd numbered)
    else:
        wire_gates(grid, row)

    wire_grid(grid, row + 1)  # Once the action for the current row is complete, recursively call for the next row


def count_gates(grid: np.ndarray):

    """Counts the number of gates in a base grid."""

    gate_count = 0
    for row in grid:
        gate_count += collections.Counter(row)[GATE_GENER]

    return gate_count


def get_gate_coords(grid: np.ndarray) -> list[tuple[int, int]]:

    """Gets the coordinates of every gate in a base schematic and returns them as a list."""

    n, width = grid.shape  # # n is number of inputs
    coords = []  # Tracks coordinates

    for row in range(n):  # Loop rows
        for column in range(width):  # Loop columns
            if grid[row][column] == GATE_GENER:  # Found a gate
                coords.append((row, column))

    return coords


def add_random_gates(grid: np.ndarray, gate_coords: list[tuple[int, int]], gate_orders: list[tuple]) -> tuple:

    """Adds random gates to a base grid and returns the grid and its combination of random gates in order as a tuple."""

    fresh_grid = grid.copy()  # Create a copy of the grid so that our original isn't modified

    while True:

        gate_order = []  # Keeps track of the order random gates are placed in

        for coordinate in gate_coords:  # Loop through coordinates

            row, column = coordinate  # Unpack values

            gate = random.choice((list(GATES.keys())))  # Pick a random gate
            gate_order += [gate]  # Track the gate
            fresh_grid[row][column] = gate  # Add it to the grid in place

        if not tuple(gate_order) in gate_orders:  # This gate order hasn't been generated yet
            break

    return fresh_grid, tuple(gate_order)


# Ensure no duplicates
def duplicate_detector(gate_orders: list[tuple[str]]) -> int:

    """Detects any schematics that have an identical combination of gates."""

    difference = len(gate_orders) - len(list(set(gate_orders)))  # List - list with no duplicates

    return difference  # Effectively the # of duplicates


# Batch making
def validate_version_count(versions: int, gate_count: int, inputs: int):

    """Determines if there are enough permutations possible to create the specified number of versions."""

    possible_versions = len(GATES) ** gate_count  # Total possible permutations

    # Formula explanation
    formula = "This is calculated using the formula 6^n, where n is the number of gates in a given schematic," \
              " and 6 is the number of different gates to choose from."

    # Checks
    if versions > possible_versions:  # Too many requested versions

        print(f"You have requested the generation of {versions} versions. Because the schematic with {inputs} inputs "
              f"only contains {gate_count} gates, there is only {possible_versions} possible different versions that can"
              f" be created.\n")

        print(formula)  # Explain calculations

        print("\nPlease try again with a different number of versions.")

        quit()  # Quit

    elif versions > possible_versions * 0.8 and inputs > 5:  # Random generation will take a while

        print("Warning, generating this many versions randomly may be computationally expensive, as many duplicates will"
              "likely be formed.")

        print("Remember that you can press Ctrl + C at any time to force the program to stop.")

        input("Press enter to continue.")


def create_grid_batch(grid: np.ndarray, versions: int) -> dict:

    """Creates a batch of grids to the specified quantity, and returns them numbered in a dictionary."""

    grids = {}  # Holds our random grids
    gate_orders = []  # Holds the gate order for each random grid
    gate_coordinates = get_gate_coords(grid)  # Get the coordinates for the gates in the base grid
    bar = IncrementalBar("Schematics", max=versions)

    for _ in range(versions):  # Make as many as there are specified versions

        # Progress display
        bar.next()

        # Generate randomized grid and its gate order
        new_grid, gate_order = add_random_gates(grid, gate_coordinates, gate_orders)

        # Store results
        grids[_] = new_grid
        gate_orders.append(gate_order)

    bar.finish()

    return grids
