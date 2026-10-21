"""Losslessly re-compress ilastik HDF5 exports (gzip + shuffle, one chunk per frame) so they fit in git.

ilastik writes its exports uncompressed (a 53-frame probability map is ~650 MB); every value is kept
bit-for-bit, only the storage encoding changes. Attributes such as 'axistags' are copied.

usage: python compress_h5.py FILE.h5 [FILE.h5 ...]   (replaces each file in place)
"""
import os
import sys
import h5py
import numpy as np

for path in sys.argv[1:]:
    tmp = path + ".tmp"
    with h5py.File(path, "r") as src, h5py.File(tmp, "w") as dst:
        def copy(name, obj):
            if isinstance(obj, h5py.Dataset):
                chunks = (1,) + obj.shape[1:] if obj.ndim > 1 else None
                out = dst.create_dataset(name, shape=obj.shape, dtype=obj.dtype, chunks=chunks,
                                         compression="gzip", compression_opts=9, shuffle=True)
                for t in range(obj.shape[0]):
                    out[t] = obj[t]
                for k, v in obj.attrs.items():
                    out.attrs[k] = v
                assert all(np.array_equal(obj[t], out[t]) for t in range(obj.shape[0]))
        src.visititems(copy)
    before, after = os.path.getsize(path), os.path.getsize(tmp)
    os.replace(tmp, path)
    print(f"{path}: {before / 1e6:.0f} MB -> {after / 1e6:.0f} MB (lossless)")
