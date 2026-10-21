"""Convert the hand-drawn labels of a legacy ilastik project from t,x,y,c to t,y,x,c.

The MitoCheck pixelClassification.ilp (saved with ilastik 0.6, 2014) stores its
label blocks in the movie's on-disk axis order t,x,y,c. ilastik 1.5 handles
images internally as t,y,x,c, so loading those blocks fails ("Rois do not
intersect"). This script swaps axes 1 and 2 of every label block and of its
'blockSlice' coordinates, so each label lands on exactly the same pixel.

usage: python fix_legacy_labels.py PROJECT.ilp   (modifies the file in place)
"""
import sys
import h5py
import numpy as np

project = sys.argv[1]
with h5py.File(project, "r+") as p:
    for labelset in p["PixelClassification/LabelSets"].values():
        for name in list(labelset.keys()):
            block = labelset[name]
            data = np.swapaxes(block[()], 1, 2)
            slices = block.attrs["blockSlice"].strip("[]").split(",")
            slices[1], slices[2] = slices[2], slices[1]
            del labelset[name]
            new = labelset.create_dataset(name, data=data)
            new.attrs["blockSlice"] = "[" + ",".join(slices) + "]"
        print(f"{labelset.name}: {len(labelset)} blocks converted to t,y,x,c")
