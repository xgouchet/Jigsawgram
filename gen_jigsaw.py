#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
import json
import numpy
from argparse import ArgumentParser, Namespace
from typing import List

from PIL import Image

PLACEHOLDER = [
    (255, 0, 0),
    (0, 128, 255),
    (255, 128, 0),
    (0, 0, 255),
    (128, 255, 0),
    (128, 0, 255),
    (0, 255, 0),
    (255, 0, 128),
    (0, 255, 128)
]

TEMPLATES = ["a", "b", "c", "d", "e", "f", "g"]
ROW_COUNT = 3

INPUT_WIDTH = 1168
INPUT_HEIGHT = 1168

TARGET_WIDTH_POST = 1024
TARGET_HEIGHT_POST = 1024


RAW_WIDTH_STORY = 2880
RAW_HEIGHT_STORY = 2880

TARGET_WIDTH_STORY = 1080
TARGET_HEIGHT_STORY = 1920

OVERLAP = 72
DOUBLE_OVERLAP = OVERLAP * 2

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
        return Image.new("RGB", (INPUT_WIDTH, INPUT_HEIGHT), PLACEHOLDER[index % 9])


def get_post_image(index: int) -> Image:
    fp = "output/raw_" + str(index) + ".png"
    if os.path.isfile(fp):
        return Image.open(fp, mode='r')
    else:
        print(" ⚠ File " + fp + " does not exist")
        return Image.new("RGB", (TARGET_WIDTH_POST, TARGET_HEIGHT_POST), PLACEHOLDER[index % 9])


def get_overlay_image(index: int) -> Image:
    fp = "overlay/overlay_" + str(index) + ".png"
    if os.path.isfile(fp):
        return Image.open(fp)
    else:
        print(" ⚠ File " + fp + " does not exist")
        return Image.new("RGBA", (INPUT_WIDTH, INPUT_HEIGHT), (0, 0, 0, 0))


def get_mask_image(index: int) -> Image:
    template_name = TEMPLATES[index % 7]
    fp = "mask/mask_" + template_name + ".png"
    if os.path.isfile(fp):
        return Image.open(fp, mode='r')
    else:
        print(" ⚠ File " + fp + " does not exist")
        return Image.new("RGB", (INPUT_WIDTH, INPUT_HEIGHT), (0, 0, 0))


def get_bump_image(index: int) -> Image:
    template_name = TEMPLATES[index % 7]
    fp = "bump/bump_" + template_name + ".png"
    if os.path.isfile(fp):
        return Image.open(fp, mode='r')
    else:
        print(" ⚠ File " + fp + " does not exist")
        return Image.new("RGB", (INPUT_WIDTH, INPUT_HEIGHT), (128, 128, 128))


def get_stroke_image(index: int) -> Image:
    template_name = TEMPLATES[index % 7]
    fp = "stroke/stroke_" + template_name + ".png"
    if os.path.isfile(fp):
        return Image.open(fp, mode='r')
    else:
        print(" ⚠ File " + fp + " does not exist")
        return Image.new("RGB", (INPUT_WIDTH, INPUT_HEIGHT), (255, 255, 255))


def get_tileid_image(index: int) -> Image:
    template_name = TEMPLATES[index % 7]
    fp = "tileid/tileid_" + template_name + ".png"
    if os.path.isfile(fp):
        return Image.open(fp)
    else:
        print(" ⚠ File " + fp + " does not exist")
        return Image.new("RGB", (INPUT_WIDTH, INPUT_HEIGHT), (255, 255, 255))


def in_coords(x: int, y: int) -> int:
    return x + (y * INPUT_WIDTH)


def generate_jigsaw(index: int, missing: List[int], with_overlay:bool, prefix: str):
    print("Generating jigsaw picture for index " + str(index) + " with missing tiles " + repr(missing))

    target_width = TARGET_WIDTH_POST
    target_height = TARGET_HEIGHT_POST
    offset_x_in = int((INPUT_WIDTH - target_width) / 2)
    offset_y_in = int((INPUT_HEIGHT - target_height) / 2)
    source = get_source_image(index).getdata()
    mask = get_mask_image(index).getdata()
    bump = get_bump_image(index).getdata()
    stroke = get_stroke_image(index).getdata()
    tileid = get_tileid_image(index).getdata()
    if with_overlay:
        overlay = get_overlay_image(index).getdata()

    l_source = get_source_image(index + 1).getdata()
    l_mask = get_mask_image(index + 1).getdata()
    r_source = get_source_image(index - 1).getdata()
    r_mask = get_mask_image(index - 1).getdata()
    t_source = get_source_image(index + ROW_COUNT).getdata()
    t_mask = get_mask_image(index + ROW_COUNT).getdata()
    b_source = get_source_image(index - ROW_COUNT).getdata()
    b_mask = get_mask_image(index - ROW_COUNT).getdata()

    output = Image.new('RGB', (target_width, target_height), (0, 0, 0))
    output_data = output.load()

    for x in range(0, target_width):
        for y in range(0, target_height):
            x_in = x + offset_x_in
            y_in = y + offset_y_in
            if x_in in range(0, INPUT_WIDTH) and y_in in range(0, INPUT_HEIGHT):
                source_px = source[in_coords(x_in, y_in)]
                if with_overlay:
                    overlay_px = overlay[in_coords(x_in, y_in)]
                tileid_px = tileid[in_coords(x_in, y_in)]
                mask_a = mask[in_coords(x_in, y_in)][0] / 256
                bump_a = bump[in_coords(x_in, y_in)][0] / 256
                stroke_a = stroke[in_coords(x_in, y_in)][0] / 256
                tile_id = int(tileid_px[0] * 16 / 85) + \
                          int(tileid_px[1] * 4 / 85) + \
                          int(tileid_px[2] / 85)
            
            if missing is not None and tile_id in missing:
                pixel = (0, 0, 0)
            else:
                base = [0, 0, 0]
                # Main tiles
                base[0] = (source_px[0] * mask_a)
                base[1] = (source_px[1] * mask_a)
                base[2] = (source_px[2] * mask_a)

                # Left neighbour tiles
                if x < DOUBLE_OVERLAP - offset_x_in:
                    if y_in in range(0, INPUT_HEIGHT):
                        l_source_px = l_source[in_coords(x_in + INPUT_WIDTH - DOUBLE_OVERLAP, y_in)]
                        l_mask_a = l_mask[in_coords(x_in + INPUT_WIDTH - DOUBLE_OVERLAP, y_in)][0] / 256
                        base[0] = base[0] + (l_source_px[0] * l_mask_a)
                        base[1] = base[1] + (l_source_px[1] * l_mask_a)
                        base[2] = base[2] + (l_source_px[2] * l_mask_a)

                # Right neighbour tiles
                if x > target_width + offset_x_in - DOUBLE_OVERLAP:
                    if y_in in range(0, INPUT_HEIGHT):
                        r_source_px = r_source[in_coords(x_in - INPUT_WIDTH + DOUBLE_OVERLAP, y_in)]
                        r_mask_a = r_mask[in_coords(x_in - INPUT_WIDTH + DOUBLE_OVERLAP, y_in)][0] / 256
                        base[0] = base[0] + (r_source_px[0] * r_mask_a)
                        base[1] = base[1] + (r_source_px[1] * r_mask_a)
                        base[2] = base[2] + (r_source_px[2] * r_mask_a)

                # Top neighbour tiles
                if y < DOUBLE_OVERLAP - offset_y_in:
                    if x_in in range(0, INPUT_WIDTH):
                        t_source_px = t_source[in_coords(x_in, y_in + INPUT_HEIGHT - DOUBLE_OVERLAP)]
                        t_mask_a = t_mask[in_coords(x_in, y_in + INPUT_HEIGHT - DOUBLE_OVERLAP)][0] / 256
                        base[0] = base[0] + (t_source_px[0] * t_mask_a)
                        base[1] = base[1] + (t_source_px[1] * t_mask_a)
                        base[2] = base[2] + (t_source_px[2] * t_mask_a)

                # Bottom neighbour tiles
                if y > target_height + offset_y_in - DOUBLE_OVERLAP:
                    if x_in in range(0, INPUT_WIDTH):
                        b_source_px = b_source[in_coords(x_in, y_in - INPUT_HEIGHT + DOUBLE_OVERLAP)]
                        b_mask_a = b_mask[in_coords(x_in, y_in - INPUT_HEIGHT + DOUBLE_OVERLAP)][0] / 256
                        base[0] = base[0] + (b_source_px[0] * b_mask_a)
                        base[1] = base[1] + (b_source_px[1] * b_mask_a)
                        base[2] = base[2] + (b_source_px[2] * b_mask_a)

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
            if with_overlay:
                overlay_src = overlay_px[3] / 256
                overlay_dst = 1 - overlay_src
                output_data[x, y] = (
                    int((jigsaw[0] * overlay_dst) + (overlay_px[0] * overlay_src)),
                    int((jigsaw[1] * overlay_dst) + (overlay_px[1] * overlay_src)),
                    int((jigsaw[2] * overlay_dst) + (overlay_px[2] * overlay_src))
                )
            else:
                output_data[x, y] = (jigsaw[0], jigsaw[1], jigsaw[2])

    if not os.path.exists('output'):
        os.makedirs('output')
    output_path = "output/" + prefix + "_" + str(index) + ".png"
    output.save(output_path)
    print(" ✔ Generated file " + output_path)


def generate_story(index: int):
    target_width = RAW_WIDTH_STORY
    target_height = RAW_HEIGHT_STORY
    offset_x_in = int((TARGET_WIDTH_POST - target_width) / 2)
    offset_y_in = int((TARGET_HEIGHT_POST - target_height) / 2)

    output = Image.new('RGB', (target_width, target_height), (0, 0, 0))
    output_data = output.load()

    post_tl = get_post_image(index + ROW_COUNT + 1).getdata()
    post_t = get_post_image(index + ROW_COUNT).getdata()
    post_tr = get_post_image(index + ROW_COUNT - 1).getdata()
    post_l = get_post_image(index + 1).getdata()
    post_c = get_post_image(index).getdata()
    post_r = get_post_image(index - 1).getdata()
    post_bl = get_post_image(index - ROW_COUNT + 1).getdata()
    post_b = get_post_image(index - ROW_COUNT).getdata()
    post_br = get_post_image(index - ROW_COUNT - 1).getdata()
            
    for x in range(0, target_width):
        for y in range(0, target_height):
            x_in = x + offset_x_in
            y_in = y + offset_y_in

            if x_in<0 and y_in<0:
                post_px = post_tl[x_in + TARGET_WIDTH_POST + ((y_in+TARGET_HEIGHT_POST) * TARGET_WIDTH_POST)]
            elif x_in<0 and y_in in range(0, TARGET_HEIGHT_POST):
                post_px = post_l[x_in + TARGET_WIDTH_POST + (y_in * TARGET_WIDTH_POST)]
            elif x_in<0 and y_in>=TARGET_HEIGHT_POST:
                post_px = post_bl[x_in + TARGET_WIDTH_POST + ((y_in-TARGET_HEIGHT_POST) * TARGET_WIDTH_POST)]
            elif x_in in range(0, TARGET_WIDTH_POST) and y_in<0:
                post_px = post_t[x_in + ((y_in+TARGET_HEIGHT_POST) * TARGET_WIDTH_POST)]
            elif x_in in range(0, TARGET_WIDTH_POST) and y_in in range(0, TARGET_HEIGHT_POST):
                post_px = post_c[x_in + (y_in * TARGET_WIDTH_POST)]
            elif x_in in range(0, TARGET_WIDTH_POST) and y_in>=TARGET_HEIGHT_POST:
                post_px = post_b[x_in + ((y_in-TARGET_HEIGHT_POST) * TARGET_WIDTH_POST)]
            elif x_in>=TARGET_WIDTH_POST and y_in<0:
                post_px = post_tr[x_in - TARGET_WIDTH_POST + ((y_in+TARGET_HEIGHT_POST) * TARGET_WIDTH_POST)]
            elif x_in>=TARGET_WIDTH_POST and y_in in range(0, TARGET_HEIGHT_POST):
                post_px = post_r[x_in - TARGET_WIDTH_POST + (y_in * TARGET_WIDTH_POST)]
            elif x_in>=TARGET_WIDTH_POST and y_in>=TARGET_HEIGHT_POST:
                post_px = post_br[x_in - TARGET_WIDTH_POST + ((y_in-TARGET_HEIGHT_POST) * TARGET_WIDTH_POST)]
            else:
                post_px = [0, 0, 0]

            output_data[x, y] = (post_px[0], post_px[1], post_px[2])

    angle = ((index * 137.50309) % 42.0) - 23

    output_r = output.rotate(angle, Image.BICUBIC, True)
    dw = int((output_r.width - TARGET_WIDTH_STORY) / 2)
    dh = int((output_r.height - TARGET_HEIGHT_STORY)/2)
    box = (dw, dh, dw+TARGET_WIDTH_STORY, dh+TARGET_HEIGHT_STORY)
    output_c = output_r.crop(box)

    if not os.path.exists('output'):
        os.makedirs('output')
    output_path = "output/story_" + str(index) + ".png"
    output_c.save(output_path)
    output.close()
    output_r.close()
    print(" ✔ Generated file " + output_path)


def generate_list(path: str):
    with open(path) as json_file:
        config = json.load(json_file)

    for key in config:
        index = int(key)
        missing = config[key]
        generate_jigsaw(index, missing, True, "post")
        generate_jigsaw(index, missing, False, "raw")

    for key in config:
        index = int(key)
        generate_story(index)


def run_main() -> int:
    cli_args = parse_arguments(sys.argv[1:])

    if "missing_list" in cli_args:
        generate_list(cli_args.missing_list)
    else:
        generate_jigsaw(cli_args.index, cli_args.missing)
        generate_story(cli_args.index)

    return 0


if __name__ == "__main__":
    sys.exit(run_main())
