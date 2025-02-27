import json
import csv
import sys
from pathlib import Path
import argparse
from rich_argparse.contrib import ParagraphRichHelpFormatter

import btrfs_snapshot_growth.btrfs_snapshots as snaps
from btrfs_snapshot_growth.human_bytes import HumanBytes


def snapshot_diffs(snapshots):
    if len(snapshots) < 2:
        return
    parent = snapshots[0]
    diffs = []
    # for child in snapshots[1:3]:
    for child in snapshots[1:]:
        diffs.append(snaps.snapshot_diff(parent, child))
        parent = child
    return diffs


def main():
    parser = argparse.ArgumentParser(
        prog="btrfs-snapshot-growth",
        description="calculates the size diffs between snapshots",
        formatter_class=ParagraphRichHelpFormatter,
    )
    parser.add_argument("-j", "--json", action="store_true")
    parser.add_argument("-c", "--csv", action="store_true")
    parser.add_argument("snapshots", nargs="+")
    args = parser.parse_args()
    # print(args)

    # print(list(map(lambda s: Path(s), sys.argv[1:])))
    diffs = snapshot_diffs(list(map(lambda s: Path(s), args.snapshots)))
    if args.json:
        print(json.dumps(diffs, indent=2))
    elif args.csv:
        writer = csv.writer(sys.stdout, delimiter=';',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for diff in diffs:
            writer.writerow([diff['creation'], diff['size']])
    else:
        parser.error('Need --json/-j or --csv/-c')
        # raise ValueError()