# BTRFS snapshot growth

It has always bothered me with btrfs that I have no good way of seeing btrfs disk
usage over time.

I know about `btrfs quota` (not good for performance) and `btrfs filesystem du
-s` (which I think is rather useless - see below).

This was inspired by my question in: [Best
way to show/visualize btrfs disk usage? - Unix &amp; Linux Stack
Exchange](https://unix.stackexchange.com/questions/790596/best-way-to-show-visualize-btrfs-disk-usage) and is an answer to it.

## Usage

Download this module and then:

```shell
$ uv venv
$ uv pip install -e .
$ sudo uv run btrfs-snapshot-growth /btrfs/snapshots/@store.* -g
Diffing... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
2025-01-05 00:00:01 +0100: size:          43.712 /          43.712
2025-02-02 00:00:04 +0100: size:         112.808 /         156.520
2025-02-09 00:00:00 +0100: size:         214.459 /         370.978
2025-02-16 00:00:00 +0100: size:           1.539 /         372.517
2025-02-21 00:00:01 +0100: size:           8.233 /         380.750
2025-02-22 00:00:02 +0100: size:           2.475 /         383.224
2025-02-23 00:00:00 +0100: size:          90.131 /         473.356
2025-02-24 00:00:01 +0100: size:         203.395 /         676.751
2025-02-25 00:00:02 +0100: size:          16.746 /         693.496
2025-02-26 00:00:03 +0100: size:           0.348 /         693.844
2025-02-26 12:00:10 +0100: size:           0.554 /         694.399
2025-02-26 13:00:04 +0100: size:           0.000 /         694.399
...
2025-02-28 12:00:03 +0100: size:           0.000 /         697.593
```

Visualised e.g. in this Google Docs [sheet](https://docs.google.com/spreadsheets/d/18BIblrURfgKthKKdWiwxcZGC8jDoT16pGHfdpnYI0Fw/edit?usp=sharing):

![visualised usage](https://i.imgur.com/RoWMA6K.png)

This allows me to see that usage went up a lot in the period around Feb 2-9, and
also on Feb 23 and 24.

**Help**:
```shell
$ uv run btrfs-snapshot-growth --help     
Usage: btrfs-snapshot-growth [-h] [-f {json,csv,human}] [-g]
                             snapshots [snapshots ...]

calculates the size diffs between snapshots

Positional Arguments:
  snapshots

Options:
  -h, --help            show this help message and exit
  -f, --format {json,csv,human}
  -g, --gib             show sizes in gigabytes (GiB)
```

(Outputs in JSON, CSV, human readabe output (the default))

## Background

Synology's fantastic "Storage Estimation Report" visualization impressed me
.

**How was this graph made?**

[![Synology's "Storage Estimation Report" visualization][1]][1]

(different data)

The user first chooses a start and end date. It then starts with the first
snapshot (ordered by time) and for each successive snapshot, it shows how much
extra space is required to store it (relative to the first snapshot which is at
y=0).

**Explanation:** This volume is a periodic rsync of another file system, and
just before the snapshot on Feb 4 the highlighed snapshot) I renamed a large
folder on the source file system and rsynced that to the btrfs volume, so the
original files got deleted and the new ones got recreated from scratch. So yup,
creating the snapshot on 02/04/2025 used roughly 410GB. **Fix**: Remove the
snapshot, restore to the previous snapshot, rename the folder in the btrfs
volume also, and then rsync again. **Result:** Almost no disk usage by the new
snapshot (not shown) because no files actually changed, only a large
subdirectory got renamed.


## How it works

`btrfs send` and `btrfs recieve --dump` are the key.

This calculates the diff between two snapshots:

```shell
$ sudo btrfs send -p \
    /btrfs/snapshots/@store.20250105T0000 \
    /btrfs/snapshots/@store.20250202T0000 --no-data -q | \
    btrfs receive --dump | grep len= | \
    sed 's/.*len=//' | perl -p -e '$sum += $_; $_="" ; END { print $sum }'

121126236218
```

That value is actually the second row in the output above. This (small) project
just automates that in python and formats the output "nicely".

## Why I think `btrfs filesystem du -s` is useless

I would love to be proven wrong here.

Assume I have a file system with some large files in it. I take two snapshots A1
and A2. I then `rm` those files and re-download them again, so the file contents
are exactly the same, but they're now on different inodes (or whatever) and so
btrfs can't do copy-on-write/CoW for them. I take two snapshots B1 and B2. So
now A1 and A2 are identical and B1 and B2 are identical. And all 4 snapshots
contain *exactly* the same files.

What I want to know is that the difference between A2 and B1 is huge, because
all the files were rewritten and use more space in the BTRFS file system.

But in this scenario `btrfs filesystem du -s A1 A2 B1 B2` will show the exact
same total and zero exclusive, right?

  [1]: https://i.sstatic.net/AJnf5hI8.png
