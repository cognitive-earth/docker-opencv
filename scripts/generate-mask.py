#!/usr/bin/env python3
import argparse
from pathlib import Path

import cv2
import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a binary OpenCV mask while preserving selected enclosed holes."
    )
    parser.add_argument("input", help="Input image path.")
    parser.add_argument(
        "output",
        nargs="?",
        help="Output mask path. Defaults to a parameter-stamped name beside the input.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=8,
        help="Foreground threshold; pixels greater than this become foreground.",
    )
    parser.add_argument(
        "--kernel-size",
        type=int,
        default=5,
        help="Elliptical morphology kernel size.",
    )
    parser.add_argument(
        "--close-iterations",
        type=int,
        default=2,
        help="Number of morphology close iterations.",
    )
    parser.add_argument(
        "--preserve-holes",
        type=int,
        default=2,
        help="Number of largest enclosed dark holes to preserve in the final mask.",
    )
    return parser.parse_args()


def default_output_path(input_path, threshold, kernel_size, close_iterations, preserve_holes):
    suffix = (
        f".mask.preserve-{preserve_holes}-holes"
        f".threshold{threshold}.close{kernel_size}x{kernel_size}"
        f".iter{close_iterations}.png"
    )
    return input_path.with_suffix(suffix)


def validate_args(args):
    if not 0 <= args.threshold <= 255:
        raise SystemExit("--threshold must be between 0 and 255")
    if args.kernel_size < 1 or args.kernel_size % 2 == 0:
        raise SystemExit("--kernel-size must be a positive odd integer")
    if args.close_iterations < 0:
        raise SystemExit("--close-iterations must be zero or greater")
    if args.preserve_holes < 0:
        raise SystemExit("--preserve-holes must be zero or greater")


def main():
    args = parse_args()
    validate_args(args)

    input_path = Path(args.input)
    output_path = (
        Path(args.output)
        if args.output
        else default_output_path(
            input_path,
            args.threshold,
            args.kernel_size,
            args.close_iterations,
            args.preserve_holes,
        )
    )

    img = cv2.imread(str(input_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise SystemExit(f"Could not read image: {input_path}")

    _, raw_fg = cv2.threshold(img, args.threshold, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (args.kernel_size, args.kernel_size),
    )
    closed_fg = cv2.morphologyEx(
        raw_fg,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=args.close_iterations,
    )

    n, labels, stats, _ = cv2.connectedComponentsWithStats(closed_fg, 8)
    if n <= 1:
        raise SystemExit("No foreground object found")

    largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    outer_mask = np.where(labels == largest, 255, 0).astype(np.uint8)

    holes_to_preserve = np.zeros_like(raw_fg)
    selected_holes = []
    if args.preserve_holes:
        raw_bg_inside_outer = np.where(
            (outer_mask == 255) & (raw_fg == 0),
            255,
            0,
        ).astype(np.uint8)
        num_holes, hole_labels, hole_stats, _ = cv2.connectedComponentsWithStats(
            raw_bg_inside_outer,
            8,
        )

        candidates = []
        for label in range(1, num_holes):
            x = int(hole_stats[label, cv2.CC_STAT_LEFT])
            y = int(hole_stats[label, cv2.CC_STAT_TOP])
            w = int(hole_stats[label, cv2.CC_STAT_WIDTH])
            h = int(hole_stats[label, cv2.CC_STAT_HEIGHT])
            area = int(hole_stats[label, cv2.CC_STAT_AREA])

            touches_image_boundary = (
                x == 0
                or y == 0
                or x + w == raw_fg.shape[1]
                or y + h == raw_fg.shape[0]
            )
            if not touches_image_boundary:
                candidates.append((area, label, x, y, w, h))

        candidates.sort(key=lambda candidate: (-candidate[0], candidate[1]))
        selected_holes = candidates[: args.preserve_holes]

        for _, label, *_ in selected_holes:
            holes_to_preserve[hole_labels == label] = 255

    mask = outer_mask.copy()
    mask[holes_to_preserve == 255] = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), mask):
        raise SystemExit(f"Could not write mask: {output_path}")

    selected = ", ".join(
        f"area={area} bbox=({x},{y},{w},{h})"
        for area, _, x, y, w, h in selected_holes
    )
    print(f"input={input_path}")
    print(f"output={output_path}")
    print(f"source_shape={img.shape}")
    print(f"outer_area={int(stats[largest, cv2.CC_STAT_AREA])}")
    print(f"preserve_holes={args.preserve_holes}")
    print(f"selected_holes={selected or 'none'}")
    print(f"mask_white_pixels={int(np.count_nonzero(mask))}")


if __name__ == "__main__":
    main()
