# Shape Analysis 101: every file explained in plain language

Repository: <https://github.com/uhlmanngroup/shapeanalysis101> (BSD 3-Clause, © 2021 Uhlmann Group @ EMBL-EBI).
Authors: Johannes Hugger and Virginie Uhlmann (Uhlmann group, EMBL-EBI); the spline toolbox is by Virginie Uhlmann
and the spline shape space by Virginie Uhlmann and Anna Song (after Song, Uhlmann, Fageot & Unser 2020). Short passages
from the notebooks are reproduced only as marked quotations; everything else below is a description, not a copy.
Snapshot read: commit `bfccc0c` (21 Nov 2023), the only commit in the shallow clone.

**How this was produced.** The repo was cloned and split across four reader agents: notebook 1 plus the data;
notebook 2A; notebook 2B plus the spline code; notebook 3 plus the embedding code. A coordinating pass then
merged their reports and re-checked the key claims against the source. No code from the repository was
executed. Data files were opened read-only, and pickled files were opened with a restricted loader. Some
numbers come from re-implementing the maths in separate scripts; those are marked *(re-computed)*.

**Labels used:**
- **[Inference]**: deduced from the code but not demonstrated by running it.
- **[Unverified]**: background knowledge not found in the repo.

Everything else was read directly from the files.

---

## 1. What the course is about (the big picture)

The course teaches how to turn the *outline* of a biological object into numbers, and then how to compare,
average and classify those outlines. Two biological datasets are used:

| Dataset | What it shows | Question asked |
|---|---|---|
| **C. elegans** (roundworms), from the Broad BBBC010 collection | Brightfield images of worms in a live/dead assay | How do the body shapes of live and dead worms differ? |
| **MEF_LMNA**, mouse embryonic fibroblasts, from the kukionfr *Micropattern_MEF_LMNA_Image* repo | Fluorescence images of wild-type cells and lamin-deficient (LMNA−/−) cells | Can a cell's type be told from its outline alone? |

The four notebooks form a pipeline:

```
1 Data Preparation ──► outline → points (discrete model) and → smooth curve (continuous / spline model)
        │
        ├─► 2A Discrete Shape Analysis    (12 points per worm: align, average, measure distance, PCA)
        ├─► 2B Continuous Shape Analysis  (same ideas, but on spline curves)
        └─► 3  Shape Embeddings           (a neural network learns a shape "fingerprint" for MEF cells)
```

"Shape" has a precise meaning throughout: **what is left after removing position, size and rotation.** Two
worms that differ only in where they lie, how big they are, or which way they point have the *same* shape.

---

## 2. File-by-file inventory

| File | Type | What it is |
|---|---|---|
| `README.md` | text | Setup instructions, citations, reading list (section 3) |
| `LICENSE` | text | BSD 3-Clause: free to use, modify and redistribute with attribution; no warranty |
| `shapeanalysis101_env.yml` | config | Conda recipe with GPU support: Python 3.7.7, PyTorch 1.8.1, CUDA 11.1, scipy 1.5.3, scikit-learn 0.23.2, plus h5py, jupyter, matplotlib, numpy, scikit-image |
| `env_wo_gpu.yml` | config | The same without CUDA (PyTorch 1.7.0); creates environment `shapeanalysis101_2` |
| `1 - Data Preparation.ipynb` | notebook | Exercise: from images to point and spline models (section 4) |
| `2A - Discrete Shape Analysis.ipynb` | notebook | Exercise: landmark-based shape statistics (section 5) |
| `2B - Continuous Shape Analysis.ipynb` | notebook | Exercise: spline-based shape statistics (section 6) |
| `3 - Shape Embeddings.ipynb` | notebook | Exercise: deep-learning shape fingerprints (section 7) |
| `solutions/[Solution] …ipynb` (×4) | notebooks | The same notebooks with answers filled in and results saved. They are large because plots are embedded as images. |
| `spline_models/spline_curve_model.py` | code | Builds smooth cubic B-spline curves through points (section 6.1) |
| `spline_models/spline_shape_space.py` | code | Shape statistics on spline curves (section 6.2) |
| `spline_models/.DS_Store` | junk | macOS Finder metadata (header bytes `Bud1`), committed by accident; irrelevant |
| `shape_embeddings/model.py` | code | PointNet neural network (section 7.1) |
| `shape_embeddings/criterion.py` | code | Loss functions that tell the network how wrong it is (section 7.2) |
| `shape_embeddings/data_handling.py` | code | Loads MEF point clouds and splits them into training and validation sets (section 7.3) |
| `shape_embeddings/utils.py` | code | Helpers: centring, augmentation, classifier, the script that made `mef_data.npy` (section 7.4) |
| `shape_embeddings/main.py` | code | Stand-alone training script, an alternative to the notebook (section 7.5) |
| `data/…` | data | See section 2.1 |

### 2.1 Data files

Shapes and values below were measured from the files.

| File | Contents | Used by |
|---|---|---|
| `data/C. elegans/…A23_w2…tif`, `…B07_w2…tif` | Worm images, 520×696 px, 16-bit. Well A23 = "dead", well B07 = "live". | Notebook 1 |
| `data/C. elegans/…A23_w1…tif`, `…B07_w1…tif` | Second channel of the same wells (exposure 25 ms vs 45 ms for w2) | **Nothing**: no notebook uses them |
| `data/C. elegans/B07_06_ground_truth.png` | Black-and-white mask of one worm: 0 = background, 255 = worm, 1,212 worm pixels | Notebook 1 |
| `data/C. elegans/point_models.npy` | 1,377 worms × 12 points × (x, y). Plain numbers. | Notebook 2A |
| `data/C. elegans/labels.npy` | 1,377 labels: 0 = dead (579 worms), 1 = live (798 worms) | 2A, 2B |
| `data/C. elegans/spline_models.npy` | 1,377 saved spline-curve objects. Each is open with M = 6, stored as 10 coefficient pairs. **Pickle file**: loading it runs the repo's code. | Notebook 2B |
| `data/MEF_LMNA/{wildtype,lmna_deficient}/raw_images/xy001c1.tif`, `xy001c2.tif` | Cell images, 1024×1280 px, 16-bit. c1 = cell body, c2 = nucleus (per the variable names). | Notebook 1, `utils.py` |
| `data/MEF_LMNA/xy001c1_instances.h5` | Label image (HDF5): 0 = background, 1–11 = eleven individual cells. It matches the **wild-type** image (correlation 0.82, against 0.02 for the lamin-deficient one). The file name does not say this. | Notebook 1 |
| `data/MEF_LMNA/mef_data.npy` | A dictionary of 5,377 cells (2,438 wild-type, 2,939 lmna) from 200 source images. Each cell is 120 (row, col) points chosen at random from its outline, so the points are *unordered*. | Notebook 3, `shape_embeddings/` |

---

## 3. README, LICENSE and environment files

- **README.md** gives three ways to install:
  1. `conda env create -f shapeanalysis101_env.yml` (needs an NVIDIA GPU).
  2. `env_wo_gpu.yml`, for CPU only.
  3. A manual fallback with Python 3.8 and no PyTorch. This is enough for notebooks 1, 2A and 2B but **not 3**.

  It also says solution notebooks must be moved to the repo root before running, because they use relative
  paths such as `data/...`. It gives citations for the spline toolbox, for 2B (Song et al. 2020, SIAM J.
  Imaging Sciences) and for 3 (Hugger & Uhlmann 2021, preprint), and a reading list (Dryden & Mardia;
  Klingenberg 2020; Khosla et al. 2020).
- **Things the environment files do not cover**:
  - `tifffile` (imported by notebook 3 and `utils.py`) and `imageio` (notebook 1) are not listed in either yml.
  - `napari` (used in `utils.py`) is not listed either.
  - scikit-image is unpinned, so a fresh install gets a new version. [Inference] Notebook 1's
    `skimage.morphology.skeletonize_3d` failed to import in a current scikit-image during this review.
- **LICENSE**: BSD 3-Clause. You may reuse the code, including commercially, if you keep the copyright
  notice. You may not use the authors' names to endorse your product. There is no warranty.

---

## 4. Notebook 1: Data Preparation

**Goal (cell 1):** "learn how to extract different kinds of object models from images, and how to prepare
them for subsequent shape analysis."

The exercise and solution versions differ in only 4 cells (18, 26, 32, 33). The exercise leaves blanks such
as `N=`, which are syntax errors until filled in.

| Cells | Step | What happens |
|---|---|---|
| 0–3 | Setup | Imports numpy, imageio, h5py, matplotlib and the repo's `B3_spline_curve` |
| 4–9 | Look at the raw data | Shows a live and a dead worm. Shows wild-type and lamin-deficient MEFs, with the cell channel in green and the nucleus in red. |
| 10–15 | Ex. 0.1–0.2: load and show masks | Worm mask from PNG (binary). MEF mask from HDF5 (one number per cell). Asks which format is more convenient (no answer given). |
| 16–18 | Ex. 0.3: MEF outlines | **Solution:** `find_contours(mef_mask, 0)`, then keep outlines with more than 150 points. 17 outlines are found and 10 kept; the 7 dropped (3–96 points) are segmentation debris. |
| 19–21 | Ex. 0.4: plot outlines | Pre-filled |
| 22–29 | Ex. 0.5–0.6: worm midline | **Solution:** `celegans_contour = skeletonize(celegans_mask)`. This gives a head-to-tail line of about 104 pixels. The variable is called "contour" but holds the midline. |
| 30–36 | Ex. 1.1–1.2: point model | **Solution:** N = 20 evenly spaced points along the worm (method below) |
| 37–42 | Ex. 2.1–2.2: spline model | Pre-filled: fit a cubic B-spline through the 20 points, sample it at 1000 points per segment, plot |

### Methods in notebook 1, in plain language

- **Mask** (cells 11–15). A second image the same size as the photo, where each pixel says which object it
  belongs to (0 = background). A *binary* mask says only "object / not object". An *instance* mask gives
  each cell its own number.
- **`find_contours(mask, 0)`** (cell 18). Imagine the image as a landscape where a pixel's value is its
  height. The function traces the line where the height crosses a given level, here the edge between
  background (0) and object. It works on each 2×2 block of pixels and places the line between pixel
  centres. [Inference: this "marching squares" method is how scikit-image implements it; the notebook only
  says to read the documentation.] The output is an ordered loop of (row, column) points around each object.
- **Skeleton** (cells 24–25). The worm shape is peeled away one pixel layer at a time until a one-pixel-wide
  centre line is left.
  - *Finding an end.* For each line pixel, look at its 3×3 neighbourhood with the centre removed. A pixel in
    the middle of the line has neighbours on two sides, which form two separate groups. A tip has neighbours
    on one side only, which form one group. The first tip found is the start point.
  - *Ordering* (`order()`, cell 24). From the start, repeatedly step to the nearest unvisited pixel. This
    lists the pixels head to tail.
- **Even spacing by arc length** (cell 33, second version). The raw pixels are unevenly spaced, because a
  diagonal step is longer than a straight one.
  1. Walk along the line and add up the distance travelled: s₀ = 0, sᵢ = sᵢ₋₁ + (distance from point i−1 to
     point i).
  2. Build a function that, given a distance *s*, returns the position at that distance by drawing straight
     lines between neighbouring points.
  3. Ask for N distances equally spaced from 0 to the total length.

  The result is N points equally far apart along the worm. The solution cell also contains a first,
  index-based version, which the second one silently overwrites.

  The 12-point models in `point_models.npy` have segment lengths that vary by only about 2% within each
  worm, so they appear to have been made this way. [Inference]
- **Cubic B-spline** (cells 39–41) is explained in section 6.1.

Other notes on notebook 1:
- `closed_curve=False` (cell 39) is right for a worm, which is an open line. A student who picks a MEF cell
  must change it to `True`.
- Plots swap (row, col) to (x, y) in some cells but not others, so some panels look rotated or mirrored.
- The headings "[FOR MLF ONLY]" are a typo for MEF.

---

## 5. Notebook 2A: Discrete (landmark) shape analysis

**Data:** `point_models.npy`, 1,377 worms × 12 points, and `labels.npy`.
**Pipeline:**
1. Remove position and size.
2. Remove rotation.
3. Compute the average shape.
4. Measure distances between shapes.
5. Find the main ways shapes vary (PCA).
6. Repeat per class (dead vs live).
7. Generate synthetic worms.

Cell numbers below refer to the exercise. In the solution, add 1 from cell 3 onwards, because the solution
has an extra cell that sets the plot resolution.

### 5.1 Section 1: alignment (cells 10–24)

**1.1 Preshape, filled in by the student** (solution cell 12):
`centered = points − mean(points)` and then `preshape = centered / ‖centered‖`.

- *Subtracting the mean* moves the worm's centre of mass to (0, 0), which removes **position**.
- *Dividing by the norm* rescales the worm to size 1, which removes **size**. ‖centered‖ is the square root
  of the sum of the squared distances of all points from the centre.

  Example: a worm 3 units long and a copy 6 units long become identical after this step.
- The result is called a **preshape**: position and size are gone, rotation is still there. Average sizes
  before normalising were 129 (dead) and 110 (live) *(re-computed)*. That information is thrown away on
  purpose, because size is not "shape" here.

**1.2 Best rotation by trial and error, filled in by the student** (solution cell 16).
- The error function rotates worm 2 by an angle θ using the rotation matrix
  R(θ) = [[cos θ, −sin θ], [sin θ, cos θ]]. It then measures how far its points are from worm 1's points.
- `scipy.optimize.minimize` tries angles until the error stops shrinking. Result: θ = −1.4923 rad (about −85.5°).
- Detail: the student's "RMSE" is just the total distance, not divided by the number of points. Dividing by
  a constant would not change which angle is best, so the answer is unaffected.

**1.3–1.4 The same rotation in one line, using complex numbers** (cells 18–22). A point (x, y) can be
written as one complex number, x + iy.
- *Why this helps:* multiplying by e^{iθ} = cos θ + i·sin θ rotates the point by θ around the origin.
  Written out, (x + iy)(cos θ + i sin θ) = (x cos θ − y sin θ) + i(x sin θ + y cos θ). That is exactly the
  rotation matrix, done in a single multiplication.
- A worm becomes a list of 12 complex numbers z = (z₁ … z₁₂).
- *Best rotation formula:* θ = angle( Σₖ conj(z2ₖ) · z1ₖ ). In code: `np.angle(z2.conj().T @ z1)`. It gives
  −1.4922899425, the same as the trial-and-error answer to 9 digits.
- *Why it works:*
  - The squared mismatch is ‖z1 − e^{iθ}z2‖² = ‖z1‖² + ‖z2‖² − 2·Re(e^{iθ}·Σ conj(z1ₖ)z2ₖ).
  - Both sizes are 1, so only the last term changes with θ. It is largest, and the mismatch smallest, when
    e^{iθ} cancels the angle of that sum.
  - *Analogy:* each pair of matching points casts a vote, a little arrow pointing at the rotation it wants.
    Large, well-separated points cast longer arrows. Adding up all the arrows gives the consensus direction.
  - Worked example: z2 = 1, the point (1, 0), and z1 = i, the point (0, 1). Then conj(1)·i = i, whose angle
    is 90°. Turning (1, 0) by 90° gives (0, 1).
- Cells 23–24 show that for 2D vectors [10, 7] and [5, 5], the ordinary angle formula and the complex
  formula give the same angle (0.17467).

### 5.2 Section 2: Kendall shape space (cells 25–46)

All centred, size-1 shapes lie on the surface of a high-dimensional ball (a "hypersphere"). Shapes that
differ only by rotation count as the same point. This curved space is **Kendall's shape space**.

- **2.1** The student converts all preshapes to complex numbers: `preshapes[:,:,0] + 1j*preshapes[:,:,1]`.
- **2.2 Fréchet mean** (the function `meanFrechet` is provided; the student calls it).
  - *Idea:* on a curved surface a plain average can fall off the surface, like averaging two cities' positions
    on a globe and landing underground. The **Fréchet mean** is instead the shape that minimises the sum of
    squared distances to all shapes.
  - *How it is computed:*
    1. Build the 12×12 table S = Σᵢ zᵢ zᵢᴴ, where ᴴ means "flip and take complex conjugates".
    2. Take its **top eigenvector**, the single direction in which all worms agree most once each is
       allowed to spin freely.
    3. Re-centre it and rescale it to size 1.
  - The notebook cites the proof as Dryden & Mardia, Result 8.2.
  - Sketch [Unverified as to the book's wording]: the squared distance from a size-1 candidate m to worm zᵢ is
    1 − |mᴴzᵢ|². Minimising the total is the same as maximising mᴴ S m, and the top eigenvector does that.
  - The top eigenvalue is 1291.5 out of 1377 *(re-computed)*, so the worms agree strongly. The mean worm is
    an almost straight line.
- **2.3** The student aligns every worm to the mean, using the one-line rotation from 1.4.
- **2.4** The student averages the aligned worms point by point. This gives nearly the same shape as the
  Fréchet mean, but shorter (size 0.9645 *(re-computed)*), because averaging arrows that point in slightly
  different directions gives a shorter arrow.
- **2.5 Generalised Procrustes Analysis** (code provided). Pick a random reference worm, align all worms to
  it, average, align to the new average, and repeat until nothing changes.
  - The solution comment says the result "is completely different from the Fréchet mean". A re-computation
    disagrees: from 6 random starts, the loop converged within about 1e-5 of the Fréchet mean in 1–2
    rounds *(re-computed)*.
  - [Inference] Each round is in effect "multiply by S and rescale". That is power iteration, a standard way
    to find the top eigenvector, so it must arrive at the same answer. A visible difference would be only an
    overall rotation of the plot.
- **2.6 Geodesic path** (the student fills in `steps` and `path`).
  - *Geodesic distance* ρ = arccos(|zᴴw|): the angle between two shapes on the ball, i.e. the length of the
    shortest arc. It is the shape-space version of a great-circle flight route.
  - *Geodesic path* ("slerp"): path(t) = [sin((1−t)ρ)·e^{iθ}z + sin(tρ)·w] / sin ρ, for t from 0 to 1. This is
    a smooth morph from one shape to the other along that arc. In the solution plot, the straight mean worm
    bends gradually into a U shape.
  - Quirk: 11 shapes are computed but only 10 are drawn, so the final target worm is never shown.
- **2.7–2.8 Three distances, compared for one random worm:**

  | Distance | Formula | Value |
  |---|---|---|
  | Geodesic (along the curved surface) | arccos(\|zᴴw\|) | 0.35815 |
  | Procrustes (straight line after best rotation) | ‖z − e^{iθ}w‖ | 0.35624 |
  | Chord | √(2 − 2\|zᴴw\|) | 0.35624 |

  - The Procrustes and chord distances are **the same thing**, equal to 15 digits. Expanding
    ‖z − e^{iθ}w‖² at the best θ gives exactly 2 − 2|zᴴw|.
  - The arc is always a little longer than the straight line. *Analogy:* the flight path over the globe is
    longer than a tunnel through it.
  - At small distances the two nearly agree.

### 5.3 Section 3: PCA, the main ways worms vary (cells 47–59)

**Why the tangent space is needed.** PCA works only on flat spaces, but shape space is curved. The fix is to
use the **tangent plane** at the mean: a flat sheet touching the ball at the mean shape, like a flat paper
map laid on a globe at one city.
- `logarithmMap(mean, shape)` flattens a shape onto the sheet. It records the direction and distance from
  the mean, after best rotation. The length is set to ρ.
- `exponentialMap(mean, v)` goes back: cos(t)·mean + (sin t / t)·v, where t = ‖v‖. This means "walk
  distance t on the globe in direction v".

**What PCA means here.**
- Each flattened worm is a list of 24 real numbers (12 real parts, then 12 imaginary parts).
- PCA finds the direction in which the worms differ most (mode 1), then the next most among directions at
  right angles to it (mode 2), and so on.
- *Analogy:* if every worm were a person and the 24 numbers their measurements, PCA would find that
  "overall build" explains most of the differences, and "arm length relative to leg length" explains a
  little more.

**Results:**
- **Tangent PCA (3.1–3.3):** variance explained is 66.1%, 13.3%, 8.7%, 7.4%, 2.2%, 1.0%. The first four
  modes cover 95.4%.
  - Only 20 of the 24 components carry variation. [Inference] 24 numbers, minus 2 for position, 1 for size
    and 1 for rotation, leaves 20 shape dimensions.
  - **Mode 1 is bending**: the worm curls into a C shape in one direction or the other.
  - The scatter plot of PC1 against PC2 is not one round cloud. It has a dense core plus an "arch" of
    strongly bent worms.
- **Flat PCA (3.4, bonus):** the same analysis without flattening gives 59.4% / 19.5% / 9.4% / 6.8%.
  Treating the curved space as flat moves variance between modes, which is the point of the comparison.

### 5.4 Section 4: dead vs live (cells 60–75)

- The student computes a Fréchet mean and runs tangent PCA for each class separately.

  | Class | Mode 1 | Mode 2 | Number of active modes | Mode-1 bend size |
  |---|---|---|---|---|
  | Dead | 78.2% | 8.9% | 16 | about ±0.015 |
  | Live | 66.8% | 13.2% | 20 | about ±0.12 |

- **Main biological finding:**
  - Dead worms are nearly straight, rigid rods.
  - Live worms bend about 8–10 times more.
  - The "arch" in the global scatter plot comes from the live worms.
  - The two class means are both close to the overall mean (distances 0.028 and 0.023 *(re-computed)*), so
    the difference lies in the *spread* of shapes, not in the average shape.
  - [Inference from plot scales]
- The solution's live-class plot mixes the global mean's x-coordinates with the live mean's y-coordinates.
  This is a display error only.

### 5.5 Section 5: generating synthetic worms (cells 76–80)

- *Intended method:*
  1. Draw random numbers for the first 3 modes.
  2. Add them to the mean on the flat sheet.
  3. Map the result back to shape space with `exponentialMap`.

  The notebook asks "How good do you think this model is?"
- *Observed:* the saved plot shows jumbled point sets, not worms.
- [Inference] The code multiplies the random spread by an extra √(n−1) ≈ 28 (`sqrt(explained_variance_*(n-1))`).
  That pushes the samples far outside the data, where the exponential map wraps around the ball.

### 5.6 Exercise vs solution, and code problems

- The exercise version has three code problems:
  - It uses `np.complex`, which was removed in NumPy ≥ 1.24. The solution uses `complex`.
  - Cell 40 contains the typo `sample_preshape].imag`.
- Both versions use `np.Inf`, which was removed in NumPy 2.0.
- No classifier is trained in 2A. The labels are used only to split the data.

---

## 6. Notebook 2B and `spline_models/`: Continuous (spline) shape analysis

Notebook 2B repeats 2A's pipeline, but each worm is a **smooth curve** instead of 12 dots.

### 6.1 `spline_curve_model.py` (223 lines; author V. Uhlmann, "Spline Fitting Toolbox v1.0")

**The bump function `B3.value(x)`** (lines 134–140):

```
β(x) = 2/3 − x² + |x|³/2      when |x| < 1
β(x) = (2 − |x|)³ / 6         when 1 ≤ |x| ≤ 2
β(x) = 0                      otherwise
```

- This is a smooth hill, 4 units wide and 2/3 tall at the centre.
- **A curve is a sum of copies of this hill**: curve(t) = Σₖ cₖ · β(t − k).
  - Each cₖ is a *control point*, an (x, y) position.
  - Each hill is shifted to sit at position k.
- *Analogy:* a flexible ruler pulled by a row of magnets. Each magnet (control point) pulls only the nearby
  part of the ruler, because each hill is only 4 wide. So any point on the curve depends on about 4
  neighbouring control points.
- At whole numbers t the hills overlap with weights 1/6, 4/6, 1/6, which add up to 1. This is why shifting
  all control points by the same amount shifts the whole curve by that amount.
- `firstDerivativeValue` and `secondDerivativeValue` give the slope and curvature of the hill. Neither is
  used by any notebook.

**Fitting: finding control points so the curve passes through given points** (`filterSymmetric`, lines 166–194).
- At whole numbers t, the curve equals (cₖ₋₁ + 4cₖ + cₖ₊₁)/6. That is a blurred version of the control
  points. Fitting means *un-blurring*.
- The code un-blurs with a fast two-pass "recursive filter":
  1. A forward sweep: cp[k] = s[k] + p·cp[k−1].
  2. A backward sweep: cm[k] = p·(cm[k+1] − cp[k]).
  3. Multiply the result by 6.

  The constant p = −2 + √3 ≈ −0.268 (line 168) is the root of p² + 4p + 1 = 0, chosen to exactly cancel the
  1-4-1 blur.
- Each sweep is like a running average whose memory fades by a factor of 0.268 per step.
- The result is an **exact interpolation**: the curve passes through every point. [Inference from the
  algebra; not run.]
- `filterPeriodic` (lines 196–222) does the same for closed loops, with wrap-around.

**The class `B3_spline_curve(M, closed)`** (lines 9–128):
- `get_spline_coefficients(points)` (lines 46–68) does the fitting.
  - For open curves it first repeats each end point twice, so M points produce **M + 4 coefficients**. This
    is why the stored worm splines have M = 6 but 10 coefficient pairs.
- `sample(rate)` evaluates the curve densely, giving rate·(M−1)+1 points for an open curve.
- `parameterToWorld(t)` evaluates the curve at a single parameter value t.
- `centroid`, `translate`, `scale` and `rotate` move the control points. None of them is used by any notebook.
- **Bug, line 72:** it raises `SplineCurve.noCoefsMessage`, but no `SplineCurve` exists. You get a confusing
  NameError instead of the intended "no coefficients" message.

### 6.2 `spline_shape_space.py` (240 lines; authors V. Uhlmann and A. Song; cites Song et al. 2020)

The same geometry as 2A, with one change. Instead of comparing control points one by one, it compares the
**whole continuous curves**.

- **`B3_Phi(M)`** (lines 19–28) builds a table Φ of how much each pair of hills overlaps, Φ[k,l] = ∫ βₖ(t)·βₗ(t) dt.
  - With it, the overlap of two whole curves z and w is simply zᴴ Φ w.
  - *Analogy:* two curves are compared by how much they cover the same ground, not just by their magnets.
  - The table is computed by numerical integration, M² times. That is slow but the table is small.
- **`B3_shape_space`** (lines 30–137) provides:
  - `hermitianProduct` = zᴴΦw;
  - `configurationNorm` = √(zᴴΦz), the size of a curve;
  - `preshape`: centre, then scale to size 1;
  - `meanFrechet`: the top eigenvector of Σ zzᴴ Φ;
  - `theta` and `align`: best rotation = angle(zᴴΦw);
  - `geodesicDistance` = arccos|zᴴΦw|;
  - `geodesicPath` (slerp);
  - `exponentialMap` and `log`: the flat-map round trip of section 5.3.

  These are 2A's formulas with Φ inserted.
- **Open question about open curves:** for open curves, the code uses the *periodic* (wrap-around) overlap
  table with M + 4 coefficients. [Unverified] Whether that matches the paper's treatment of open curves.
- **Bugs:** `fullDistance` and `partialDistance` (lines 109 and 113) call `hermitianProduct` without `self.`,
  so they crash with NameError if called. No notebook calls them.
- **`B3_PCA`** (lines 139–240) runs PCA on the flat tangent sheet.
  - First the numbers are multiplied by √Ψ, where Ψ is two copies of Φ, one for the real parts and one for
    the imaginary parts. After that, ordinary straight-line distance equals the whole-curve distance.
    [Inference from the algebra]
  - The eigenvalues are not divided by the number of worms. The percentages are unaffected.
- The repo contains no "dictionary learning" code, although that phrase is in the cited paper's title.

### 6.3 Notebook 2B walkthrough

Libraries: numpy, matplotlib, scipy, and `spline_models`. Data: `spline_models.npy` and `labels.npy`. The
notebook loads the spline objects with `allow_pickle=True`. That is only safe if you trust the files.

| Section | What it does | Student work |
|---|---|---|
| 0 | Load 1,377 splines (M = 6, open). Plot 5. The code claims to pick 5 at random, but it actually plots the first five. | Run only |
| 1.1–1.2 | Convert coefficients to complex numbers; make preshapes | Run only |
| 1.3 | Align two random worms | Run only |
| 1.4 | Fréchet mean. The text says 6 complex numbers replace 12. **In fact the code uses M + 4 = 10.** | Run only |
| 1.5 | Geodesic path from the mean to a worm. Again the last shape is not drawn. | Run only |
| 2.1–2.2 | Tangent PCA; plot ±0.2 × each mode around the mean | Run only |
| 3.1–3.2 | Split into dead and live; plot examples | Run only |
| 3.3 | Fréchet mean per class | **Fill in** (`shape_space.meanFrechet(...)`) |
| 3.4 | PCA per class | **Fill in** (`B3_PCA(...).transform(...)`) |
| 3.5 | First 2 modes per class | **Fill in** (copy of 2.2 per class) |
| 4.1 | Generate 5 synthetic live worms from 3 modes | Run only |

- The only text outputs are `M=6` and `Closed curve? False`. All other results are figures.
- The exercise stubs in 3.3 use variable names (`mean_shape_Frechet_parameters_dead`) that differ from those
  the later cells expect (`mean_shape_Frechet_dead`).

---

## 7. Notebook 3 and `shape_embeddings/`: learned shape fingerprints

**Task:** tell wild-type MEFs from lamin-deficient ones from the cell outline alone.

1. Each cell is 120 unordered (row, col) points from `mef_data.npy`.
2. A neural network (**PointNet**) turns each cell into a list of 2048 numbers, the **embedding**, a shape
   fingerprint.
3. During training a small extra network (the **projection head**) shrinks the embedding to 128 numbers, and
   a **supervised contrastive loss** is computed on those.
4. Quality is checked by training a simple linear classifier on the 2048-number embeddings of held-out cells.

### 7.1 `model.py`: the network

- **Building blocks:**
  - *"Conv1d with kernel 1"*: the same small formula applied to every point separately. Every point is
    asked the same questions.
  - *ReLU*: replaces negative numbers by 0. Without it, stacking layers would add no power.
  - *BatchNorm*: rescales numbers to a stable range, which makes training steadier.
- **`SpatialTransformer3d`** (lines 7–44). Despite the "3d" in its name, it works on 2D points.
  - A mini-network looks at the whole cell and proposes a 2×2 matrix (a rotation or stretch) to apply to all
    points first.
  - It starts as the "do nothing" matrix [[1,0],[0,1]].
  - This is PointNet's "T-Net" (arXiv 1612.00593, cited in the notebook).
- **`SpatialTransformerkd`** (lines 47–87): the same idea on the 64-number per-point features. It is only
  used if `feature_transform=True`.
- **`PointNetFeat`** (lines 90–133):
  1. Apply the 2×2 transform.
  2. Turn each point into 64, then 128, then 1024 numbers.
  3. **Max-pool** (line 127): for each of the 1024 features, keep the largest value over all points.
  - *Why max-pool:* the maximum does not care about the order of the points, so shuffling a cell's points
    cannot change the answer.
  - *Analogy:* asking a crowd 1024 questions and recording, for each question, the most extreme answer
    anyone gave.
- **`PointNet`** (lines 136–168): `PointNetFeat`, then two layers (1024 → 1024 → 2048) that produce the
  **embedding**.
  - The **projection head** (2048 → 128) is followed by `F.normalize`, which rescales the output to length 1.
  - After that rescaling, the dot product of two outputs equals their **cosine similarity**: 1 means they
    point the same way, 0 means unrelated, −1 means opposite.
  - Hand-counted size: about 8.6 million adjustable weights. [Inference]
  - Unlike the original PointNet paper, no penalty keeps the transform matrices well behaved.

### 7.2 `criterion.py`: the loss

**`SupConLoss`** (lines 71–157) is adapted from HobbitLong/SupContrast and implements Khosla et al. 2020
(arXiv 2004.11362). For each cell (the **anchor**):
- cells of the same type in the batch are **positives**;
- cells of the other type are **negatives**.

Per anchor i, with zᵢ its length-1 128-number vector and τ = 0.07 the "temperature":

```
Lᵢ = −(1/|P(i)|) · Σ over positives p of  log [ exp(zᵢ·z_p / τ)  /  Σ over all a ≠ i of exp(zᵢ·z_a / τ) ]
```

Reading it from the inside out:
1. zᵢ·z_p is how similar two cells look (from −1 to 1).
2. Dividing by τ = 0.07 multiplies the similarities by about 14. This sharpens the differences: τ is a
   "pickiness" knob.
3. exp(…) / Σ exp(…) is a **softmax**. It turns the similarities into probabilities: "of all the other cells
   in the batch, how likely is it that p is my neighbour?"
4. −log turns that probability into a penalty: 0 when the probability is 1, large when it is small.
5. The penalty is averaged over all positives, then over all anchors (lines 151–155). The extra factor
   τ/τ_base equals 1 with the defaults.

The code also subtracts each row's maximum before taking exp (lines 132–133). That leaves the result
unchanged and only prevents numerical overflow.

*Worked example:* a batch of 4 cells, where A and B are wild-type and C and D are lmna. For anchor A, the loss
is small when A·B is much larger than A·C and A·D. If all four look identical, the loss is −log(1/3) ≈ 1.10.

*Useful benchmark:* with a batch of 200 and no information in the embeddings, each anchor sees 199 equally
similar cells, so the loss is about ln(199) ≈ 5.29.

`DiscriminiativeLoss` (lines 5–67, misspelled in the source) is an alternative "pull together / push apart
with margins" loss. Nothing in the tutorial uses it.

### 7.3 `data_handling.py`

- `get_MEF_loaders` labels a cell 0 if its key contains "wildtype", else 1. It shuffles the cells without a
  fixed random seed, then splits them 75% for training and 25% for validation. **The split therefore changes
  on every run.**
- **Bug:** its `transforms` argument is never used. The notebook overrides this function with its own copy
  (cell 7), which does pass transforms on.
- `get_MEF_loader` returns all cells in one unshuffled loader. It is used for visualisation.
- `MEFDataset` always applies `Center()` first (see the bug in section 7.6).

### 7.4 `utils.py`

| Function / class | Purpose | Notes |
|---|---|---|
| `load_data`, `visualize_data`, `show_image` | Load or show raw MEF images and masks | Imported by notebook 3 but never called there |
| `segmentation_to_pointcloud` | **Made `mef_data.npy`**: outlines longer than 120 points, then 120 points picked at random | Uses `napari` without importing it, and opens a viewer window per cell (leftover debugging). The random picks are unseeded, so the file cannot be regenerated exactly. |
| `run_logistic_regression` | Measures embedding quality (below) | Folds are not shuffled |
| `Center` | Subtracts the mean | **Wrong axis**, see section 7.6 |
| `RandomCoordsFlip` | Augmentation: a random mirror flip | `random` is not imported, so it crashes if used |
| `RandomNoise` | Augmentation: adds small jitter (σ = 0.01, at most ±0.05) | Negligible on pixel coordinates in the hundreds [Inference] |

**Logistic regression with 5-fold cross-validation, in plain language:**
- Logistic regression adds up the 2048 numbers with learned weights and squashes the total through an
  S-shaped curve into a probability of "lamin-deficient".
- *5-fold cross-validation:* cut the data into 5 parts that keep the same class ratio. Train on 4 parts and
  test on the fifth. Rotate through all five and average the accuracy.
- If such a simple straight-line rule can separate the classes, the embedding has organised them well.

### 7.5 `main.py`: stand-alone training

- It has no command-line options. [Inference] Something like `PYTHONPATH=. python shape_embeddings/main.py`
  from the repo root would be needed, because of mixed import styles.
- Settings:
  - `PointNet(embed_dim=2048, feat_dim=128, feature_transform=True)`;
  - the **Adam** optimiser with learning rate 1e-4 (step size) and weight decay 1e-4 (a small pull of weights
    toward zero to limit overfitting);
  - batch size 100;
  - 999 epochs (full passes over the data), with validation every 4th epoch.
- **It saves nothing** (no model file, no embeddings) and runs only on the CPU.
- **Bug, line 25:** `run_loss += run_loss` should be `+= loss.item()`, so the validation loss is always 0.

### 7.6 Notebook 3 walkthrough and results

| Section | What it does | Student work |
|---|---|---|
| 0 (cells 3–7) | Dataset and loaders, re-typed in the notebook | Run only |
| 1 (cells 8–13) | PointNet encoder and model, re-typed (same as `model.py`) | Run only |
| 2 (cells 14–16) | Shortened `SupConLoss` | Run only |
| 3 (cells 17–29) | Training: hyperparameters in cell 25 (batch 200, learning rate 1e-4, embedding 2048, output 128, τ = 0.07, **epochs = 1**). The task is to "find a set of suitable parameters". | Tune parameters |
| 4.1 (cell 33) | Run all cells through the trained model; collect the 2048-number embeddings and labels | **Fill in** |
| 4.2 (cell 36) | PCA to 2D, scatter plot coloured by type | **Fill in** |
| 4.3 (cell 39) | k-means with 2 clusters compared with the true labels | **Fill in** |

Only cells 33, 36 and 39 differ between exercise and solution.

**Saved results (CPU, 1 epoch):**

| | Exercise run | Solution run |
|---|---|---|
| Accuracy with random, untrained weights | 0.835 | 0.835 |
| Train loss after 1 epoch | 5.269 | 5.276 |
| Validation accuracy after 1 epoch | 0.741 | 0.822 |

[Inference] What these numbers say:
- A loss of about 5.27 is close to the "learned nothing" level of ln(199) ≈ 5.29.
- Accuracy after one epoch is *lower* than the untrained baseline.
- So the saved outputs do not show a trained model; students are expected to raise `epochs` themselves.
- The two runs differ because the train/validation split is unseeded.

**Problems found, in order of impact:**

1. **`Center` averages over the wrong axis.** Confirmed by reading the data and the code together.
   - The cells are stored as (120, 2) arrays and transposed to (2, 120) before `Center` runs.
   - `Center` subtracts the mean over `axis=-2`, which is now the axis of length 2, the (row, col) pair of
     each point.
   - So each point (r, c) becomes ((r−c)/2, (c−r)/2) instead of having the cell's centre subtracted.
   - Consequence: every point now carries a single number, (c − r)/2, twice (once negated). Half of each
     point's position is lost before the network sees it. Cells are also not truly centred.
   - Small demonstration: the points (100, 300), (120, 310), (90, 250) become (−100, 100), (−95, 95), (−80, 80).
   - The fix would be `axis=-1` for (2, N) arrays.
   - [Inference] Despite this, the untrained baseline reaches 0.835 accuracy. The remaining 1D signal (a
     diagonal projection of each point) still carries information.
2. **The model never returns to training mode.** `validation_loop` switches the model to evaluation mode,
   and `train_loop` never switches it back (notebook cells 19, 21 and 29; `main.py`). BatchNorm therefore
   uses frozen statistics during all training.
3. **"Best model" is not a snapshot.** `best_params = model.state_dict()` stores references to the live
   weights, not a copy. The baseline is also never considered as a candidate for "best".
4. **No data augmentation is applied anywhere.** The transforms are never passed in (cell 27), the package
   loader ignores them, and `RandomCoordsFlip` would crash anyway.
5. **The k-means plot is not informative.** It uses raw embedding dimensions 0 and 1, not the PCA axes. It is
   not scored with a number and not seeded. The PCA plot sets labels but never draws a legend.
6. **Smaller issues:**
   - The notebook's `SupConLoss` depends on a global `device` variable, defined later in cell 23.
   - The text says "we will use the VM's GPU", but the code falls back to the CPU, and the saved output is
     CPU.
   - Any batch where an anchor has no positive gives NaN, a 0/0 at `criterion.py` line 151.

---

## 8. Bugs and oddities across the repo (summary)

| # | Where | Problem | Affects tutorial run? |
|---|---|---|---|
| 1 | `shape_embeddings/utils.py` `Center` + loaders | Wrong axis: discards half the coordinate information | **Yes** (notebook 3) |
| 2 | Notebook 3 cells 19/21/29, `main.py` | Model stuck in eval mode during training | **Yes** |
| 3 | Notebook 3 cell 29 | `best_params` is not a copy | Yes (minor) |
| 4 | Notebook 3 cell 25 | `epochs = 1` gives an untrained-looking result | Yes (by design) |
| 5 | `main.py:25` | Validation loss always 0 | `main.py` only |
| 6 | `utils.py` `RandomCoordsFlip`, `segmentation_to_pointcloud` | Missing `random` / `napari` imports | Not called |
| 7 | `data_handling.py:18` | `transforms` argument ignored | Overridden in notebook |
| 8 | `spline_curve_model.py:72` | Undefined `SplineCurve` | Only on misuse |
| 9 | `spline_shape_space.py:109,113` | Missing `self.` | Not called |
| 10 | Notebook 2A cell 37 (solution) | Comment says GPA differs from the Fréchet mean; re-computation says it converges to it | Teaching text |
| 11 | Notebook 2A cell 80, 2B 4.1 | Synthetic-shape spread inflated by √(n−1) [Inference] | Yes (bad samples) |
| 12 | Notebooks 2A/2B | Last geodesic shape not drawn; "random" selection not random (2B cell 8) | Cosmetic |
| 13 | Notebook 2B cell 22 | Says 6 complex numbers describe a worm; the code uses 10 | Teaching text |
| 14 | Notebooks 1/2A | `skeletonize_3d`, `np.complex`, `np.Inf` break on current scikit-image / NumPy | **Yes**, on a modern install |
| 15 | `spline_models.npy`, `mef_data.npy` | Pickle files; `spline_models.npy` runs repo code when loaded | Security note |
| 16 | `spline_models/.DS_Store` | Accidentally committed macOS file | No |

---

## 9. What is not determined

- **Notebook answers.** The intended answers to the open discussion questions (notebooks 1, 2A, 2B) are not
  written in either version.
- **C. elegans channels.** What the w1 and w2 channels of the worm images are. [Unverified] In BBBC010 they
  may be brightfield and a fluorescence stain.
- **Open-curve treatment.** Whether 2B's handling of open curves matches Song et al. (2020). The paper was not
  read.
- **The 2021 preprint.** The content of Hugger & Uhlmann (2021). Nothing in the code refers to it beyond the
  README citation.
- **Figures.** Only text outputs were checked numerically. Statements about figure contents come from
  reading the saved images.
