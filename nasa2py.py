"""
NASA Earth Information Center - Earth Jukebox

MODULE: MEMBER 2
IMAGE PROCESSING & GRID COLOR EXTRACTION

Input:
    NASA GEOS-FP Near-Surface Wind Speed image

Member 2 responsibilities:
    1. Load NASA image
    2. Convert image to RGB
    3. Divide image into 5x5 grid
    4. Extract pixels from every grid cell
    5. Calculate mean RGB
    6. Calculate median RGB
    7. Save extracted information
    8. Create grid overlay image
    9. Create color palette image

Requirements:
    pip install pillow numpy
"""

import os
import json
import numpy as np

from PIL import Image, ImageDraw


# ---------------------------------------------------------------------------
# 1. LOAD NASA IMAGE
# ---------------------------------------------------------------------------

def load_image_rgb(image_path: str) -> np.ndarray:
    """
    Load the NASA image and convert it to RGB.

    Returns:
        NumPy array with shape:

        (height, width, 3)

    The 3 channels are:
        R = Red
        G = Green
        B = Blue
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found at: {image_path}"
        )

    with Image.open(image_path) as img:

        # Convert image to standard RGB
        img_rgb = img.convert("RGB")

        # Convert image to NumPy array
        rgb_array = np.array(
            img_rgb,
            dtype=np.uint8
        )

    print("\nNASA image loaded successfully!")

    print(
        f"Dimensions : "
        f"{rgb_array.shape[1]} px wide x "
        f"{rgb_array.shape[0]} px high"
    )

    print(
        f"Channels   : {rgb_array.shape[2]} "
        f"(R, G, B)"
    )

    return rgb_array


# ---------------------------------------------------------------------------
# 2. DIVIDE IMAGE INTO 5x5 GRID
# ---------------------------------------------------------------------------

def extract_grid_colors(
    rgb_array: np.ndarray,
    grid_rows: int = 5,
    grid_cols: int = 5
) -> list:

    """
    Divide the image into a 5x5 grid.

    For each cell we calculate:

        - cell number
        - row
        - column
        - bounding box
        - mean RGB
        - median RGB

    Returns:
        List containing information about all cells.
    """

    # Get image dimensions
    height, width, _ = rgb_array.shape

    # Calculate cell size
    cell_height = height // grid_rows
    cell_width = width // grid_cols

    print("\n------------------------------------------")
    print("GRID PROCESSING")
    print("------------------------------------------")

    print(
        f"Grid       : {grid_rows} x {grid_cols}"
    )

    print(
        f"Total cells: {grid_rows * grid_cols}"
    )

    print(
        f"Cell size  : approximately "
        f"{cell_width} x {cell_height} pixels"
    )

    results = []

    # ---------------------------------------------------------------
    # Loop through every row
    # ---------------------------------------------------------------

    for row in range(grid_rows):

        # -----------------------------------------------------------
        # Loop through every column
        # -----------------------------------------------------------

        for col in range(grid_cols):

            # Calculate starting Y coordinate
            y_start = row * cell_height

            # Calculate ending Y coordinate
            y_end = (
                height
                if row == grid_rows - 1
                else (row + 1) * cell_height
            )

            # Calculate starting X coordinate
            x_start = col * cell_width

            # Calculate ending X coordinate
            x_end = (
                width
                if col == grid_cols - 1
                else (col + 1) * cell_width
            )

            # -------------------------------------------------------
            # Extract pixels belonging to this grid cell
            # -------------------------------------------------------

            cell_pixels = rgb_array[
                y_start:y_end,
                x_start:x_end
            ]

            # -------------------------------------------------------
            # Calculate mean RGB
            # -------------------------------------------------------

            mean_rgb = np.mean(
                cell_pixels,
                axis=(0, 1)
            ).astype(int)

            r_mean = int(mean_rgb[0])
            g_mean = int(mean_rgb[1])
            b_mean = int(mean_rgb[2])

            # -------------------------------------------------------
            # Calculate median RGB
            # -------------------------------------------------------

            median_rgb = np.median(
                cell_pixels,
                axis=(0, 1)
            ).astype(int)

            r_median = int(median_rgb[0])
            g_median = int(median_rgb[1])
            b_median = int(median_rgb[2])

            # -------------------------------------------------------
            # Create cell information
            # -------------------------------------------------------

            cell_data = {

                "cell_index":
                    row * grid_cols + col + 1,

                "row":
                    row,

                "col":
                    col,

                "bbox": {

                    "x1": x_start,
                    "y1": y_start,

                    "x2": x_end,
                    "y2": y_end
                },

                "mean_rgb": [
                    r_mean,
                    g_mean,
                    b_mean
                ],

                "median_rgb": [
                    r_median,
                    g_median,
                    b_median
                ]
            }

            # Add cell information to results
            results.append(cell_data)

    return results


# ---------------------------------------------------------------------------
# 3. SAVE EXTRACTED DATA AS JSON
# ---------------------------------------------------------------------------

def save_results(
    grid_results: list,
    output_path: str
):
    """
    Save extracted grid information as JSON.
    """

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            grid_results,
            file,
            indent=4
        )

    print(
        f"\nGrid data saved to:"
        f"\n{output_path}"
    )


# ---------------------------------------------------------------------------
# 4. CREATE GRID OVERLAY IMAGE
# ---------------------------------------------------------------------------

def create_grid_overlay(
    rgb_array: np.ndarray,
    grid_results: list,
    output_path: str
):
    """
    Creates an image showing the 5x5 grid
    on top of the original NASA image.
    """

    # Convert NumPy array back into PIL image
    image = Image.fromarray(rgb_array)

    # Create drawing object
    draw = ImageDraw.Draw(image)

    # Draw every cell
    for cell in grid_results:

        bbox = cell["bbox"]

        # Draw rectangle around cell
        draw.rectangle(
            [
                bbox["x1"],
                bbox["y1"],
                bbox["x2"],
                bbox["y2"]
            ],
            outline="yellow",
            width=2
        )

        # Draw cell number
        draw.text(
            (
                bbox["x1"] + 5,
                bbox["y1"] + 5
            ),
            f"#{cell['cell_index']}",
            fill="white"
        )

    # Save image
    image.save(output_path)

    print(
        f"Grid overlay saved to:"
        f"\n{output_path}"
    )


# ---------------------------------------------------------------------------
# 5. CREATE COLOR PALETTE
# ---------------------------------------------------------------------------

def create_color_palette(
    grid_results: list,
    output_path: str,
    grid_rows: int = 5,
    grid_cols: int = 5
):
    """
    Creates a 5x5 image.

    Each block represents the mean RGB
    colour of one grid cell.
    """

    block_size = 100

    palette_width = grid_cols * block_size
    palette_height = grid_rows * block_size

    palette = Image.new(
        "RGB",
        (
            palette_width,
            palette_height
        )
    )

    draw = ImageDraw.Draw(palette)

    # Draw every colour block
    for cell in grid_results:

        x1 = cell["col"] * block_size
        y1 = cell["row"] * block_size

        x2 = x1 + block_size
        y2 = y1 + block_size

        draw.rectangle(
            [
                x1,
                y1,
                x2,
                y2
            ],
            fill=tuple(cell["mean_rgb"]),
            outline="black"
        )

        # Cell number
        draw.text(
            (
                x1 + 5,
                y1 + 5
            ),
            f"#{cell['cell_index']}",
            fill="white"
        )

    # Save palette
    palette.save(output_path)

    print(
        f"Color palette saved to:"
        f"\n{output_path}"
    )


# ---------------------------------------------------------------------------
# 6. MAIN PROGRAM
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    project_folder = os.path.dirname(os.path.abspath(__file__))

    image_file = os.path.join(
        project_folder,
        "images",
        "wind_speed.jpg"
    )

    output_folder = os.path.join(
        project_folder,
        "output"
    )

    os.makedirs(output_folder, exist_ok=True)

    pixels = load_image_rgb(image_file)

    regions = extract_grid_colors(
        pixels,
        grid_rows=5,
        grid_cols=5
    )

    print("\n" + "=" * 80)
    print("MEMBER 2 - GRID EXTRACTION RESULTS")
    print("=" * 80)

    for cell in regions:
        print(
            f"Cell {cell['cell_index']}: "
            f"Mean RGB = {tuple(cell['mean_rgb'])}, "
            f"Median RGB = {tuple(cell['median_rgb'])}"
        )

    save_results(
        regions,
        os.path.join(
            output_folder,
            "wind_grid_data.json"
        )
    )

    create_grid_overlay(
        pixels,
        regions,
        os.path.join(
            output_folder,
            "wind_grid_overlay.png"
        )
    )

    create_color_palette(
        regions,
        os.path.join(
            output_folder,
            "wind_color_palette.png"
        )
    )

    print("\nMember 2 processing completed!")
    print(f"Total cells processed: {len(regions)}")

    print("\nOutput files:")
    print("1. output/wind_grid_data.json")
    print("2. output/wind_grid_overlay.png")
    print("3. output/wind_color_palette.png")