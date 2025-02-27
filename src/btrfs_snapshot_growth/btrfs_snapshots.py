import re
import subprocess
from datetime import datetime
from pathlib import Path

creation_time_format = "%Y-%m-%d %H:%M:%S %z"


def snapshot_creation_datetime(snapshot: Path) -> datetime:
    args = ["btrfs", "subvolume", "show", str(snapshot)]
    # print(" ".join(args))
    res = subprocess.run(args, capture_output=True, check=True)
    lines = res.stdout.decode().strip().split("\n")
    date_obj = None
    for line in lines[1:]:
        match = re.match(r"^\s+Creation time:\s+(.*)$", line)
        if match:
            date_obj = datetime.strptime(match[1], creation_time_format)
    if date_obj is None:
        raise RuntimeError(f"no creation time from {snapshot}")
    return date_obj


def _send_dump(parent, child):
    cmd = [
        "btrfs",
        "send",
        "-p",
        str(parent),
        str(child),
        "--no-data",
        "-q",
    ]
    # print(" ".join(cmd))
    ps = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output = subprocess.run(
        ["btrfs", "receive", "--dump"], stdin=ps.stdout, check=True, capture_output=True
    )
    lines = output.stdout.decode().strip().split("\n")
    return lines


def _send_size(lines):
    sum = 0
    for line in lines:
        match = re.match(r".*len=(\d+).*", line)
        if match:
            sum += int(match[1])
    return sum


def snapshot_diff_size(parent, child):
    lines = _send_dump(parent, child)
    return _send_size(lines)


def snapshot_diff(parent, child):
    creation_unixtime = int(snapshot_creation_datetime(child).timestamp())
    size = snapshot_diff_size(parent, child)
    return {"snapshot": str(child), "size": size, "creation": creation_unixtime}
