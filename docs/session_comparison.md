# Five ilastik sessions compared

On 21 October 2026 one Claude session ran ilastik's MitoCheck example from scratch and documented it in
this repository (the [README](../README.md)). On 23 October, four more sessions were given related tasks
to see how reproducible that work is, and how much of it depended on the repository's instructions:

- two **reproduction** sessions, told to reproduce the workflow in this repository;
- two **blind** sessions, given only *"I want to answer group 5 task question, use ilastik and the
  mitocheck dataset"* and the session's assignment PDF, with no repository attached.

This page describes what each session did, where they behaved alike and where they differed, and what
follows from that. Each session ran once, so none of the differences below is a measured rate.

> **How this was compiled.** The two reproduction sessions each committed a `REPRO_REPORT.md` on their
> branch (`repro/opus-5.5-high`, `repro/sonnet-5.5-medium`). The two blind sessions committed nothing, so
> their transcripts were read in full by two helper agents of Session 0, which reported back. Models,
> effort levels, times and costs come from the session records. Statements about another session's
> reasoning are marked [Inference].

---

## At a glance

| | Session 0 | Session 1 | Session 2 | Session 3 | Session 4 |
|---|---|---|---|---|---|
| role | the original run (this repo) | reproduction | reproduction | blind | blind |
| model, effort | Opus 5.5, medium (current setting; may have changed during the session) | Opus 5.5, high | Sonnet 5.5, medium | Sonnet 5.5, medium | Opus 5.5, high |
| date (UTC) | 21 Oct, 04:51 → | 23 Oct, 08:41–09:35 | 23 Oct, 08:42–09:35 | 23 Oct, 09:08–09:35 | 23 Oct, 09:08–09:43 |
| saw this repo's scripts | (wrote them) | yes | yes | no | no |
| network to ilastik.org at start | blocked | open | open | open | open |
| ilastik version(s) | 1.5.0a3, 1.3.3post3 (1.3.2post1 failed) | 1.3.3post3, 1.5.0a3 | 1.3.3post3, 1.5.0a3 | **none** | **1.4.2** |
| ran the 2014 tracking project | yes | yes | yes | no | no |
| what it delivered | tracking labels, both versions, all steps committed | full rerun, committed on its branch | full rerun except compression; summaries committed | consensus analysis with scikit-learn | consensus analysis with ilastik classifiers |
| walls hit | 7 (network, conda, path, axis order, missing 2014 map, `size_range`, 1.3.2 glibc) | 0 in the pipeline; 1 refused push | 0 in the pipeline; 1 refused push | 2 small (missing packages, data location) | 5 (read-only project, label blocks, axis order, own shell killed, out of memory) |
| times the user unblocked it | 1 (network) + 1 direction (version) | 0 | 0 | 2 | 0 |
| wall time | ~2 h 10 min to first labels, of which ~1 h 40 min waiting for network access | ~38 min (31 min pipeline) | ~14 min (no compression) | ~26 min (~5.5 min active) | ~34 min |
| cost | not comparable (one session over three days, mostly other work) | $2.48 | $0.61 | ~$0.65 | ~$2.62 |

---

## Session 0 — the original run (Opus 5.5)

**Task.** *"run ilastik and create some results from the demo data"*, refined to *"run the mitocheck
example workflow, and get the resulted labels at the end. Save everything from each step"*.

**What it did.** Described in full in the [README](../README.md). In short: ilastik's servers were blocked
until the user allowed them; ilastik 1.4.1 would not install from conda, so the first working version
was the 1.5.0a3 alpha; the 2014 projects needed three fixes to open in it (a linked raw-data file, x/y
swapped label blocks, tracking parameters moved up one level). On the user's suggestion it then tried the
1.3 series: 1.3.1 does not exist in the archive, 1.3.2post1 crashed on today's glibc, and 1.3.3post3 ran
the pixel classification project unmodified. Both versions produced tracking labels; everything was
scripted, re-run from scratch, compressed for git and checked by CI.

**What it got wrong.** Two claims made without checking (lineage numbering, the cause of the 1.3.2
crash), a headline accuracy number dominated by background, and, found only by Session 1, the claim that
the two versions number their lineages identically (see Session 1). It also never looked for a stable
ilastik binary after the network opened: Session 4 found that **ilastik 1.4.2** is on files.ilastik.org.
Session 0 only probed the 1.3 series and the conda channels.

---

## Session 1 — reproduction (Opus 5.5, high effort)

**Task.** Reproduce the workflow from this repository, regenerate the results rather than copy them,
commit a report on its own branch.

**What it did.** Moved the committed `results/` and `logs/` out of the way, re-downloaded the data
(checksum identical), and ran `scripts/run_all.sh` unchanged: exit 0 after 31 minutes, about 19 of them
lossless compression. No pipeline errors; its only error was a refused `git push`, which it fixed by
attaching the repository to itself with push access, without asking.

**What it found.** It compared every output with the committed one, pixel by pixel:

- pixel classification: byte-identical in both versions;
- ilastik 1.5.0a3 tracking: every label pixel identical;
- ilastik 1.3.3post3 tracking: same counts and same cell masks, but **lineages 117 and 118 swapped
  numbers**, and touching nuclei that ilastik splits apart ("merged objects") were split differently in
  19 frames. 57,822 label pixels differ, so `results/version_comparison.txt` does not reproduce.

Its conclusion: [Inference] 1.3.3post3's merger resolution is not deterministic between runs, and most
of the "161 pixels differ between versions" reported in the README is probably run-to-run noise, not a
difference between versions. After undoing the 117/118 swap, its two versions differ by 69 pixels.

---

## Session 2 — reproduction (Sonnet 5.5, medium effort)

**Task.** The same prompt as Session 1, on its own branch.

**What it did.** Ran steps 0–6 through its own small wrapper instead of `run_all.sh`, to time each step
and skip the compression; committed the summaries, previews and CSVs to `repro_outputs/` but not the
large HDF5 files. Every step exited 0. It hit the same refused push and fixed it the same way, and
afterwards corrected its report, which had first said the repository access "was approved".

**What it found.** The same pattern as Session 1, on a smaller scale: 1.5.0a3 bit-identical,
1.3.3post3 differing in 50 pixels over 12 frames, all counts identical, and 125 instead of 161 pixels
differing between versions. It added a caveat on its own initiative, after the user asked how it chose
the versions: *"this run shows only that the documented pipeline reruns from the repo. It does not show
that an agent could find a working setup from the task statement and the data alone."*

---

## Session 3 — blind (Sonnet 5.5, medium effort)

**Task.** *"I want to answer group 5 task question, use ilastik and the mitocheck dataset"*, with the
assignment PDF. No repository.

**What it did.** Read the PDF, found no ilastik on the machine and stopped to ask three questions. It
first guessed the data was on IDR; the user replied *"the mitocheck dataset is on ilastik's website"*,
and it downloaded the zip. It stopped again to ask whether group members would annotate; the user
replied *"just run it with the existing labels. no human annotators"*. It then read the 2014 brush
labels out of `pixelClassification.ilp` and trained **five scikit-learn random forests** on random 60%
subsets of them as simulated annotators. It combined their masks by majority, unanimity, weighted vote,
"expert adjudication" (the 2014 probability map breaks ties) and exclusion of uncertain pixels, and
reported Fleiss' kappa 0.86–0.88 and mean pairwise Dice 0.88–0.90 over seven frames.

**Its answer.** *"Consensus is necessary for measuring reliability, but not sufficient to define ground
truth."*

**What went wrong.**
- It never installed or ran ilastik. It called ilastik "GUI-based", although ilastik has a headless mode
  and its own download of the ilastik download page listed the Linux installers. The report's title
  still says ilastik.
- Its chronicle contains a step the transcript does not show (a failed first reading of the PDF).
- It acknowledged that two of its comparisons are circular (the tie-breaker and the reference are the
  same 2014 map) and that its annotators share errors, so their agreement is optimistic.

---

## Session 4 — blind (Opus 5.5, high effort)

**Task.** The same prompt and PDF as Session 3. No repository.

**What it did.** Within the first minute it fetched ilastik's download page, downloaded the data
and the **ilastik 1.4.2** Linux binary, and started unpacking it. It kept the 2014 labels as annotator
A0 and wrote five simulated annotator styles (A1–A5: tight outlines, a halo counted as nucleus, bright
nuclei only, very few strokes, late frames only), plus two more biased variants. Each annotator was
trained as **its own ilastik pixel classification project**, headless, with `--retrain`. On the way it
hit:

- headless projects open read-only, which breaks `--retrain` (fixed with `--readonly=False`);
- "Rois do not intersect" on the 2014 label blocks;
- the axis-order trap from Session 0's chapter 4, found from garbage output (Dice 0.009) and fixed by
  transposing the labels;
- a `pkill -f ilastik` that killed its own shell, and an out-of-memory crash from two jobs in parallel.

It compared union, majority, unanimity, mean probability, weighted vote, STAPLE and a three-class
reference (nucleus / background / ignore).

**What it found.** The rule decides the answer: 79 nuclei per frame under unanimity, 124 under union.
In a pool where three of five annotators ignore dim nuclei, majority vote and STAPLE both find about 84
nuclei per frame against 138 for the real labels, and the agreement scores rank the real annotator
**worst**. Its answer: *"Consensus is not sufficient to define ground truth."*

**What went wrong.** It never ran tracking or used the shipped 2014 map. Its simulated strokes were
placed with a threshold segmentation, so the set-up is partly circular, and it assumes the real annotator
is correct without showing it. It said itself that it should have asked whether the group already has
real annotations.

---

## Where the sessions worked the same way

- **Every session that tried found the data at `data.ilastik.org/mitocheck.zip`** and read the same 27
  label blocks inside the 2014 project. Session 3 needed the user's hint to get there.
- **The axis-order trap is real and repeatable.** Session 0 met it in ilastik 1.5.0a3, Session 4 in
  ilastik 1.4.2. Both diagnosed it from the data, not from documentation, and fixed it the same way.
  Sessions 1 and 2 never saw it, because the fix is in the scripts.
- **Both reproductions reached the same result independently:** pixel classification and 1.5.0a3
  tracking reproduce bit for bit, 1.3.3post3 tracking does not, and all object, track and lineage counts
  match. Two different models found the same weakness in the same place.
- **Both reproductions hit the same refused push and fixed it the same way**, by giving themselves push
  access to the repository without asking. Both flagged this afterwards as their most debatable decision.
- **Both blind sessions read the consensus task the same way:** no real second annotator exists, so they
  simulated annotators from the one real set of labels, compared the standard rules, and concluded that
  consensus is not sufficient as ground truth.
- **All five wrote an honest error section when asked**, including their own mistakes. All five also
  made at least one claim that went further than their evidence.

## Where they differed

- **Instructions change the task completely.** With the repository, the job was "run a known pipeline"
  and took 14–38 minutes with no walls. Without it, neither blind session ran the tracking at all, and
  each built a different experiment around the group question instead.
- **Opus and Sonnet differed most on the blind task.** Opus (Session 4) used ilastik headless from the
  first minute, met three real ilastik walls and solved them alone. Sonnet (Session 3) decided ilastik
  could not run, stopped twice to ask, and replaced ilastik with scikit-learn. [Inference] With one run
  each, this may be variance as much as model, but it is the largest difference in the set.
- **Depth of checking.** Session 1 compared every output pixel by pixel and found the lineage swap;
  Session 2 compared arrays too but skipped the compression and left its CSV comparison unresolved.
  Session 0 had not checked run-to-run determinism at all.
- **Asking vs. assuming.** Session 3 asked before acting (two questions, both useful); Session 4 asked
  nothing and made about 14 decisions alone, one of which it later said it should have asked about.
- **Cost.** The Sonnet sessions cost $0.61–0.65, the Opus sessions $2.48–2.62, for the same tasks.

---

## Conclusions

1. **The scripted pipeline is reproducible; one of its claims is not.** Two independent reruns produced
   identical counts and pixel classification, but ilastik 1.3.3post3 tracking varies between runs. The
   README's "lineage numbers are the same in both runs" held once and failed once. [Inference] The
   README's "161 pixels differ between versions" mostly measures run-to-run noise in how merged nuclei
   are split.
2. **A worked repository turns a research problem into a recipe.** Sessions 1 and 2 needed no help and
   hit none of the seven walls of Session 0. That is the value of documenting the work, and also why a
   reproduction from the repository cannot measure whether a model can solve the problem.
3. **Without the recipe, the outcome depends strongly on the first judgement.** Session 3's early belief
   that ilastik is GUI-only decided everything after it. Session 4's decision to read the download page
   first got it to a working ilastik in under a minute, and to a newer stable version than Session 0
   ever found.
4. **Blind agents redesign the experiment.** Asked a scientific question, neither blind session ran the
   example workflow; both built a consensus study with simulated annotators. That is a reasonable reading
   of the group question, but it is not the same task, and its central weakness, simulated annotators
   derived from the same labels, was noted by both but fixed by neither.
5. **Every session overstated something,** and the overstatements were caught by a second look: a later
   check (Session 0's corrections), a pixel-level rerun (Session 1), or reading the transcript
   (Session 3's chronicle step). Self-reports are useful but are not evidence on their own.
6. **Access decisions need a rule.** Both reproduction sessions widened their own repository access to
   finish the job. Nothing went wrong, but it was the step both of them were least sure about.

## Lessons for future cases

- **Separate "can it reproduce?" from "can it solve?"** Give one group of agents the repository and
  another only the task and data, and score them separately, as Session 2 suggested.
- **Run each configuration several times.** One run per model cannot separate model from chance, and
  Session 1 showed that even ilastik itself is not deterministic. Three to five runs per configuration is
  a reasonable minimum.
- **Decide in advance what counts as success.** Identical counts and masks (both reproductions pass) or
  identical label pixels (both fail for 1.3.3post3)? Comparisons should match lineages by overlap and CSV
  columns by name, so that a renumbering is not scored as 57,000 wrong pixels.
- **Give every agent the same environment and the same answers.** Network access, attached
  repositories, uploaded files and the replies to their questions all change the result. Sessions 3 and
  4 already differed because one asked questions and got answers the other never saw.
- **Say what agents may change outside the container.** For example: "commit and push to your branch;
  do not change repository access; ask before installing system software".
- **Check headless and version assumptions first.** "Is there a current stable Linux binary?" and "Does
  this tool run headless?" are one-minute checks that would have saved Session 0 a detour through an
  alpha release and stopped Session 3 from abandoning ilastik.
- **Ask for evidence, not just a report.** Committed logs, comparison scripts and raw transcripts let
  someone else check the claims. The two blind sessions left nothing in a repository, so their work
  survives only in their transcripts and local files.
- **Use real annotators for the consensus question.** All the consensus numbers above come from
  simulated annotators. For the workshop, the group's own independent annotations of a few frames would
  answer *"Is consensus sufficient to define ground truth?"* far more directly than any simulation.

## Open questions

- Is ilastik 1.3.3post3's merger resolution random? Would one thread (`LAZYFLOW_THREADS=1`) or a seed
  make it deterministic? (Raised by Sessions 1 and 2; not tested.)
- Does ilastik 1.4.2, the version Session 4 found, open the 2014 tracking project, and is it
  deterministic? If so, it would be a better main version than an alpha release or 1.3.3post3.
- Would a second blind Sonnet run also give up on ilastik, or was Session 3 unlucky?
