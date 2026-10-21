"""Diagnosis used in the chronicle: which axis order does ilastik 1.5 expect for the 2014 labels?

Prints (1) where the 2014 label blocks sit, as stored in pixelClassification.ilp, and (2) the axis order
and shape of the label slot ilastik 1.5 creates when it opens the project (by wrapping the label
deserializer, then letting the load fail as usual).

usage (from the repo root, with ilastik 1.5's python):
  python docs/chronicle/debug_label_axes.py data/mitocheck_2d+t/pixelClassification.ilp DIR_WITH_RAW_LINK
"""
import shutil
import sys
from pathlib import Path

import h5py

project, workdir = Path(sys.argv[1]), Path(sys.argv[2])
with h5py.File(project, "r") as p:
    blocks = p["PixelClassification/LabelSets/labels000"]
    slices = sorted(b.attrs["blockSlice"] for b in blocks.values())
    print(f"label blocks stored in {project.name}: {len(slices)}")
    for s in slices[:4]:
        print("  blockSlice", s)
    print("  […]")
    for s in slices[-4:]:
        print("  blockSlice", s)

copy = workdir / project.name
shutil.copy(project, copy)
import ilastik.applets.base.appletSerializer.slotSerializer as ss

original = ss.SerialBlockSlot._deserialize


def report(self, group, slot):
    s = self.inslot[0]
    print(f"ilastik 1.5 label slot: axes {s.meta.getAxisKeys()}, shape {tuple(int(v) for v in s.meta.shape)}", flush=True)
    return original(self, group, slot)


ss.SerialBlockSlot._deserialize = report
sys.argv = ["ilastik", "--headless", f"--project={copy}"]
from ilastik_scripts.ilastik_startup import main

main()
