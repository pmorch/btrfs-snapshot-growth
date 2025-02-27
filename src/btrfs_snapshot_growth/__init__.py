import json
import csv
import sys
from pathlib import Path
import datetime
import argparse
from rich_argparse.contrib import ParagraphRichHelpFormatter
from rich.console import Console
from rich.progress import Progress

import btrfs_snapshot_growth.btrfs_snapshots as snaps
from btrfs_snapshot_growth.human_bytes import HumanBytes

creation_time_format = "%Y-%m-%d %H:%M:%S %z"


def snapshot_diffs(snapshots):
    if len(snapshots) < 2:
        return
    parent = snapshots[0]
    diffs = []
    # for child in snapshots[1:3]:
    with Progress(console=Console(file=sys.stderr)) as progress:
        task = progress.add_task('Diffing...', total=len(snapshots)-1)
        for child in snapshots[1:]:
            diffs.append(snaps.snapshot_diff(parent, child))
            parent = child
            progress.update(task, advance=1)
    return diffs


def main():
    parser = argparse.ArgumentParser(
        prog="btrfs-snapshot-growth",
        description="calculates the size diffs between snapshots",
        formatter_class=ParagraphRichHelpFormatter,
    )
    parser.add_argument(
        "-f", "--format", choices=["json", "csv", "human"], default="human"
    )
    parser.add_argument(
        "-g", "--gib", action="store_true", help="show sizes in gigabytes (GiB)"
    )
    parser.add_argument("snapshots", nargs="+")
    args = parser.parse_args()
    # print(args)

    # print(list(map(lambda s: Path(s), sys.argv[1:])))
    diffs = snapshot_diffs(list(map(lambda s: Path(s), args.snapshots)))
    total = 0
    for diff in diffs:
        size = diff["size"]
        if args.gib:
            size = size / (1024**3)
            diff["size"] = size
        total += size
        diff["total"] = total

    if args.format == "json":
        print(json.dumps(diffs, indent=2))
    elif args.format == "csv":
        writer = csv.writer(
            sys.stdout, delimiter=";", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )
        writer.writerow(["Creation", "Size", "Total"])
        for diff in diffs:
            writer.writerow([diff["creation"], diff["size"], diff["total"]])
    else:
        # args.format == "human"
        tzinfo = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        for diff in diffs:
            creation = diff["creation"]
            dt = datetime.datetime.fromtimestamp(creation, tz=tzinfo)
            creation_string = dt.strftime(creation_time_format)
            size = diff["size"]
            total = diff["total"]
            if args.gib:
                size = f"""{size:.3f}"""
                total = f"""{total:.3f}"""
            print(f"""{creation_string}: size: {size:>15} / {total:>15}""")
