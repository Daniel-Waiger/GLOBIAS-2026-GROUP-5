"""Split a frame-chunked HDF5 export into two halves (to stay under GitHub's 100 MB file limit) or join them back.

Compressed chunks are copied byte-for-byte (no decompression), so split + join is exactly lossless.

usage: python split_join_h5.py split FILE.h5       -> FILE.part1.h5 (frames 0..26), FILE.part2.h5 (27..52)
       python split_join_h5.py join  FILE.h5       <- FILE.part1.h5 + FILE.part2.h5
"""
import sys
import h5py

mode, path = sys.argv[1], sys.argv[2]
key = "exported_data"
parts = [path.replace(".h5", ".part1.h5"), path.replace(".h5", ".part2.h5")]


def new_dataset(f, like, n_frames):
    ds = f.create_dataset(key, shape=(n_frames,) + like.shape[1:], dtype=like.dtype, chunks=like.chunks,
                          compression=like.compression, compression_opts=like.compression_opts, shuffle=like.shuffle)
    for k, v in like.attrs.items():
        ds.attrs[k] = v
    return ds


def copy_frames(src, dst, src_start, dst_start, n):
    rest = (0,) * (src.ndim - 1)
    for i in range(n):
        mask, chunk = src.id.read_direct_chunk((src_start + i,) + rest)
        dst.id.write_direct_chunk((dst_start + i,) + rest, chunk, mask)


if mode == "split":
    with h5py.File(path, "r") as f:
        src = f[key]
        half = (src.shape[0] + 1) // 2
        for part, (start, n) in zip(parts, [(0, half), (half, src.shape[0] - half)]):
            with h5py.File(part, "w") as g:
                copy_frames(src, new_dataset(g, src, n), start, 0, n)
                g[key].attrs["first_frame"] = start
            print(part, f"frames {start}..{start + n - 1}")
else:
    with h5py.File(parts[0], "r") as a, h5py.File(parts[1], "r") as b, h5py.File(path, "w") as f:
        total = a[key].shape[0] + b[key].shape[0]
        out = new_dataset(f, a[key], total)
        del out.attrs["first_frame"]
        copy_frames(a[key], out, 0, 0, a[key].shape[0])
        copy_frames(b[key], out, 0, a[key].shape[0], b[key].shape[0])
    print(path, f"{total} frames")
