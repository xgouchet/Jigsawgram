#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
import json
from argparse import ArgumentParser, Namespace
from typing import List

from PIL import Image

TEMPLATES = ["a", "b", "c", "d", "e", "f", "g"]
ROW_COUNT = 3

TARGET_SIZE = 1024
MARGIN_SIZE = 72

INPUT_SIZE = TARGET_SIZE + (2 * MARGIN_SIZE)


def parse_arguments(args: list) -> Namespace:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(help='Generation mode')

    parser_single = subparsers.add_parser("single")
    parser_single.add_argument("-i", "--index", required=True, type=int, help="the index of the tile in Instagram")
    parser_single.add_argument("-m", "--missing", nargs='*', type=int, required=False,
                               help="a list of missing tiles id")

    parser_list = subparsers.add_parser("list")
    parser_list.add_argument("missing_list", type=str, help="the source json describing the missing tiles")

    return parser.parse_args(args)


def get_source_image(index: int) -> Image:
    fp = "source/" + str(index) + ".png"
    if os.path.isfile(fp):
        return Image.open(fp, mode='r')
    else:
        print(" ⚠ File " + fp + " does not exist")
        return Image.new("RGB", (INPUT_SIZE, INPUT_SIZE), (0, 0, 0))


def get_overlay_image(index: int) -> Image:
    fp = "overlay/overlay_" + str(index) + ".png"
    if os.path.isfile(fp):
        return Image.open(fp)
    else:
        print(" ⚠ File " + fp + " does not exist")
        return Image.new("RGBA", (INPUT_SIZE, INPUT_SIZE), (0, 0, 0, 0))


def get_mask_image(index: int) -> Image:
    template_name = TEMPLATES[index % 7]
    fp = "mask/mask_" + template_name + ".png"
    if os.path.isfile(fp):
        return Image.open(fp, mode='r')
    else:
        print(" ⚠ File " + fp + " does not exist")
        return Image.new("RGB", (INPUT_SIZE, INPUT_SIZE), (0, 0, 0))


def get_bump_image(index: int) -> Image:
    template_name = TEMPLATES[index % 7]
    fp = "bump/bump_" + template_name + ".png"
    if os.path.isfile(fp):
        return Image.open(fp, mode='r')
    else:
        print(" ⚠ File " + fp + " does not exist")
        return Image.new("RGB", (INPUT_SIZE, INPUT_SIZE), (128, 128, 128))


def get_stroke_image(index: int) -> Image:
    template_name = TEMPLATES[index % 7]
    fp = "stroke/stroke_" + template_name + ".png"
    if os.path.isfile(fp):
        return Image.open(fp, mode='r')
    else:
        print(" ⚠ File " + fp + " does not exist")
        return Image.new("RGB", (INPUT_SIZE, INPUT_SIZE), (255, 255, 255))


def get_tileid_image(index: int) -> Image:
    template_name = TEMPLATES[index % 7]
    fp = "tileid/tileid_" + template_name + ".png"
    if os.path.isfile(fp):
        return Image.open(fp)
    else:
        print(" ⚠ File " + fp + " does not exist")
        return Image.new("RGB", (INPUT_SIZE, INPUT_SIZE), (255, 255, 255))


def in_coords(x: int, y: int) -> int:
    return x + (y * INPUT_SIZE)


def generate_jigsaw(index: int, missing: List[int]):
    print("Generating jigsaw picture for index " + str(index) + " with missing tiles " + repr(missing))
    source = get_source_image(index).getdata()
    mask = get_mask_image(index).getdata()
    bump = get_bump_image(index).getdata()
    stroke = get_stroke_image(index).getdata()
    tileid = get_tileid_image(index).getdata()
    overlay = get_overlay_image(index).getdata()

    l_source = get_source_image(index + 1).getdata()
    l_mask = get_mask_image(index + 1).getdata()
    r_source = get_source_image(index - 1).getdata()
    r_mask = get_mask_image(index - 1).getdata()
    t_source = get_source_image(index + ROW_COUNT).getdata()
    t_mask = get_mask_image(index + ROW_COUNT).getdata()
    b_source = get_source_image(index - ROW_COUNT).getdata()
    b_mask = get_mask_image(index - ROW_COUNT).getdata()

    output = Image.new('RGB', (TARGET_SIZE, TARGET_SIZE), (0, 0, 0))
    output_data = output.load()

    for x in range(0, TARGET_SIZE):
        for y in range(0, TARGET_SIZE):
            x_in = x + MARGIN_SIZE
            y_in = y + MARGIN_SIZE
            source_px = source[in_coords(x_in, y_in)]
            overlay_px = overlay[in_coords(x_in, y_in)]
            tileid_px = tileid[in_coords(x_in, y_in)]
            tile_id = int(tileid_px[0] * 16 / 85) + \
                      int(tileid_px[1] * 4 / 85) + \
                      int(tileid_px[2] / 85)
            mask_a = mask[in_coords(x_in, y_in)][0] / 256
            bump_a = bump[in_coords(x_in, y_in)][0] / 256
            stroke_a = stroke[in_coords(x_in, y_in)][0] / 256

            if missing is not None and tile_id in missing:
                pixel = (0, 0, 0)
            else:
                if x < MARGIN_SIZE:
                    l_source_px = l_source[in_coords(x_in + TARGET_SIZE, y_in)]
                    l_mask_a = l_mask[in_coords(x_in + TARGET_SIZE, y_in)][0] / 256
                    base = (
                        int((source_px[0] * mask_a) + (l_source_px[0] * l_mask_a)),
                        int((source_px[1] * mask_a) + (l_source_px[1] * l_mask_a)),
                        int((source_px[2] * mask_a) + (l_source_px[2] * l_mask_a))
                    )
                elif x > TARGET_SIZE - MARGIN_SIZE:
                    r_source_px = r_source[in_coords(x_in - TARGET_SIZE, y_in)]
                    r_mask_a = r_mask[in_coords(x_in - TARGET_SIZE, y_in)][0] / 256
                    base = (
                        int((source_px[0] * mask_a) + (r_source_px[0] * r_mask_a)),
                        int((source_px[1] * mask_a) + (r_source_px[1] * r_mask_a)),
                        int((source_px[2] * mask_a) + (r_source_px[2] * r_mask_a))
                    )
                elif y < MARGIN_SIZE:
                    t_source_px = t_source[in_coords(x_in, y_in + TARGET_SIZE)]
                    t_mask_a = t_mask[in_coords(x_in, y_in + TARGET_SIZE)][0] / 256
                    base = (
                        int((source_px[0] * mask_a) + (t_source_px[0] * t_mask_a)),
                        int((source_px[1] * mask_a) + (t_source_px[1] * t_mask_a)),
                        int((source_px[2] * mask_a) + (t_source_px[2] * t_mask_a))
                    )
                elif y > TARGET_SIZE - MARGIN_SIZE:
                    b_source_px = b_source[in_coords(x_in, y_in - TARGET_SIZE)]
                    b_mask_a = b_mask[in_coords(x_in, y_in - TARGET_SIZE)][0] / 256
                    base = (
                        int((source_px[0] * mask_a) + (b_source_px[0] * b_mask_a)),
                        int((source_px[1] * mask_a) + (b_source_px[1] * b_mask_a)),
                        int((source_px[2] * mask_a) + (b_source_px[2] * b_mask_a))
                    )
                else:
                    base = (
                        int(source_px[0] * mask_a),
                        int(source_px[1] * mask_a),
                        int(source_px[2] * mask_a)
                    )

                if bump_a > 0.5:
                    factor = 1 - (2 * (bump_a - 0.5))
                    pixel = (
                        int(255 - ((255 - base[0]) * factor)),
                        int(255 - ((255 - base[1]) * factor)),
                        int(255 - ((255 - base[2]) * factor)),
                    )
                else:
                    pixel = (
                        int(base[0] * bump_a * 2),
                        int(base[1] * bump_a * 2),
                        int(base[2] * bump_a * 2)
                    )

            jigsaw = (
                int((pixel[0] * 0.1) + (pixel[0] * 0.9 * stroke_a)),
                int((pixel[1] * 0.1) + (pixel[1] * 0.9 * stroke_a)),
                int((pixel[2] * 0.1) + (pixel[2] * 0.9 * stroke_a))
            )
            overlay_src = overlay_px[3] / 256
            overlay_dst = 1 - overlay_src
            output_data[x, y] = (
                int((jigsaw[0] * overlay_dst) + (overlay_px[0] * overlay_src)),
                int((jigsaw[1] * overlay_dst) + (overlay_px[1] * overlay_src)),
                int((jigsaw[2] * overlay_dst) + (overlay_px[2] * overlay_src))
            )

    if not os.path.exists('output'):
        os.makedirs('output')
    output_path = "output/" + str(index) + ".png"
    output.save(output_path)
    print(" ✔ Generated file " + output_path)


def generate_list(path: str):
    with open(path) as json_file:
        config = json.load(json_file)

    for key in config:
        index = int(key)
        missing = config[key]
        generate_jigsaw(index, missing)


def run_main() -> int:
    cli_args = parse_arguments(sys.argv[1:])

    if "missing_list" in cli_args:
        generate_list(cli_args.missing_list)
    else:
        generate_jigsaw(cli_args.index, cli_args.missing)

    return 0


if __name__ == "__main__":
    sys.exit(run_main())
