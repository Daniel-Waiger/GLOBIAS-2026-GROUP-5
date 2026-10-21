"""Make the legacy MitoCheck conservationTracking.ilp (ilastik 1.0.7, 2014) loadable by ilastik 1.5.

1. The tracking parameters were saved per image lane ('ConservationTracking/Parameters/0/<name>');
   ilastik 1.5 expects them directly under 'ConservationTracking/Parameters/<name>'.
2. 'max_nearest_neighbors' did not exist in 2014; it is set to 3, ilastik 1.5's default.
   (How many candidate objects in the next frame each object may be linked to.)

All other parameter values are copied unchanged.

usage: python fix_legacy_tracking_params.py PROJECT.ilp   (modifies the file in place)
"""
import sys
import h5py

project = sys.argv[1]
with h5py.File(project, "r+") as p:
    params = p["ConservationTracking/Parameters"]
    if "0" in params:
        lane = params["0"]
        for name in list(lane.keys()):
            p.copy(lane[name], params, name=name)
        del params["0"]
    if "max_nearest_neighbors" not in params:
        params["max_nearest_neighbors"] = 3
    for name in sorted(params):
        print(f"  {name} = {params[name][()]}")
