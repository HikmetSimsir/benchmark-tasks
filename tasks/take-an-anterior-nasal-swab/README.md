# Take an anterior nasal swab on a training head: whole tip in, 4 pressed circles per nostril, cap home

A nasal-swab practice head (printed PLA shell; simplified face, adult-size nose and nostrils) lies face up on the
table, fixed to it, with its crown away from the robot. In front of its chin, a transport tube lies on a small stand
with its mouth toward the robot's right. In the tube is a sterile foam swab on the tube's plug-style blue cap, in place
as shipped, modelled on the Puritan 25-1506 1PF BT BL (15.19 cm overall, foam tip 0.48 cm across and 1.6 cm long). The
instruction:
"Take an anterior nasal swab from both nostrils of the training head with the swab in the tube: put the whole foam tip in each nostril and rub it round the inside wall at least 4 times, then put the swab back in its tube and push the cap home."

The procedure is the CDC's for an anterior nasal (nares) specimen
([CDC interim guidelines for clinical specimens](https://www.cdc.gov/covid/hcp/clinical-care/clinical-specimen-guidelines.html)):
insert the entire collection tip of the swab inside the nostril (usually 1 to 1.5 cm), firmly sample the nasal wall
by rotating the swab in a circular path against it at least 4 times (about 15 seconds), and repeat in the other
nostril with the same swab. Hologic's
[RespDirect swab collection instructions](https://www.hologic.com/respdirect-swab-collection-instructions-us) warn
that simply twirling the swab against one part of the inside of the nose is not proper technique. Printed nose models
are used to train health-care workers in swab collection (nasopharyngeal simulators: Sananès et al., Eur Arch
Otorhinolaryngol 2021;278:2649-2651, doi 10.1007/s00405-020-06454-1; Koch et al., Infect Dis Now 2022;52:138-144,
doi 10.1016/j.idnow.2022.02.002, 589 participants in 11 French centres).

- **Rub the wall, all the way round, long enough.** A step counts only if the foam tip presses on the nostril's wall
  with at least 0.2 N (about 20 g; real trials log it from load cells under the nose insert; the demo presses at a median 1.0 to 1.2 N;
  published swab contact forces run from 0.1-0.2 N (oropharyngeal) to 0.6-0.9 N peaks (nasopharyngeal);
  Frontiers Robot AI 2025, doi 10.3389/frobt.2025.1520374; arXiv 2408.13100). Circles are the larger of the
  signed angle the tip travels round the nostril while pressed (moves of up to 90 degrees per step) and the full laps
  through all twelve 30-degree sectors. Full credit also needs 10 of the 12 sectors pressed and 10 s of pressed steps
  that move round the wall, so a wiggle, a ratchet on one spot, dabbing the sectors, fast circles then pressing still,
  or circling without touching the wall earn little or nothing: an unpressed return cancels its pressed stroke, and a jump
  across the nostril starts a new lap.
- **Whole tip in, not too deep, touch nothing else.** The tip's centre must be 0.8 to 1.7 cm in. Any touch of the tip
  on the face, lips, the tube's outside or the table, or a finger on the foam voids the swab (score 0); the rims, up
  to 0.8 cm outside the openings, count as inside. A wall force above 5 N is reported, not scored.
- **Cap home, tube held.** The cap counts as home only when seated on the tube's mouth and pushed with at least 2 N
  for 0.25 s while a finger of the other hand is on the tube (the free 100 g tube and stand slide away under a one-hand push). An
  uncapped swab keeps 40% of its sampling credit; a capped but unsampled swab scores 0. The run is a success (and ends)
  once the cap has stayed home 9 s after it is let go.

## Files

| File | What |
|---|---|
| `task.py` | The task: head, swab, tube with stand, `success()`, `score()`, `report()` |
| `kitchenkit.py` | Parts from boxes, spheres and meshes; per-step poses, finger pads, contact points and forces |
| `assets/training_head.obj` | The head's collision mesh (9,660 triangles, metres) |
| `assets/head_upper.obj`, `assets/head_base.obj`, `assets/nose_insert.obj` | The head for printing: upper part with a cavity for two load cells, base plate with a cell riser, and the nose insert holding both bores |
| `assets/rig_corner.obj`, `assets/rig_arm.obj` | Printed load-cell mounts: the block joining the two cells, and the arm from the tilted cell up to the insert |
| `assets/tube_stand.obj` | The printable tube stand (with an end stop) |
| `assets/face_*.obj` | Visual-only face details (sockets, eyelids, brows, lips, ears): no collision, not printed |
| `demo.py`, `democore.py` | The scripted demo and its variants (`democore.py`: runner and planning helpers) |
| `grasp.json` | The grasp found by `demo.py`'s IK search (delete to search again, about 20 min) |
| `demo_results.json` | Each variant's score, end-state report and planned phase times |
| `make_task_json.py` | Writes `task.json` from `task.py`'s constants (stops if they no longer match the text) |
| `setup_shot.py` | Writes the top camera's starting view |
| `real_trial/` | Real-trial force logger (Arduino), log recorder, `score_real_trial.py`, build and calibration (`README.md`), rig cross-sections (`rig_sections.png`), scorer check |

`task.py` registers the swab-head and swab-tube pairs with `kitchenkit.watch_points`, so the scorer reads every
contact point between them and its normal force each step. Standard `yam_arena` embodiment and `task_score` scorer.
Assets: all meshes in `assets/` (head, printable head parts and load-cell mounts, nose insert, tube stand, face details) were made for this
task (procedural); the YAM arms are i2rt's model
(github.com/i2rt-robotics/i2rt, MIT licence); the station scene ships with yam_arena.

## Run a trial

In the Isaac Lab-Arena environment from the simulation walkthrough, from this folder:

```bash
inspect-robots run --embodiment yam_arena --policy dream -P rows_per_request=12 \
  -E task=task.py -E object_jitter=0 -E control_hz=20 -E cam_width=320 -E cam_height=176 \
  --instruction "Take an anterior nasal swab from both nostrils of the training head with the swab in the tube: put the whole foam tip in each nostril and rub it round the inside wall at least 4 times, then put the swab back in its tube and push the cap home." \
  --scorer task_score --max-steps 2400 --store-frames --log-dir logs/nasal-swab-dream
```

`-P rows_per_request=12` asks Dream-1 for a new chunk every 12 steps; with the default 48 rows a simulator slower than
real time lets the Dream session expire between chunks. `task_score` prints 1.0 on success, otherwise `score()` at
the end. **Seeds:** none; the layout is fixed (`object_jitter=0`). **Runtime:** the recorded full demo ran 1,531 control steps (76.55 s simulated at 20 Hz) in 9.7 min of wall-clock time on one NVIDIA RTX PRO 6000 Blackwell GPU shared with a second simulation, start-up and video writing included. The Dream-1 run reached the 2,400-step limit with a score of 0.0 in 9.6 min of wall-clock time, model responses included: in its first 40 s the left arm reached over the head and the right gripper went to the tube's capped end, but the swab never left its tube. A model trial runs up to 2,400 steps plus the policy's response time.

## Scripted demo

```bash
python demo.py task.py demo_out                     # full: demo.mp4, setup.png, result.json
python demo.py task.py out_light --variant light    # any variant below; --no-record skips the video
python demo.py task.py --plan-only                  # inverse-kinematics check of every variant's plan
```

The left arm pinches the tube near its closed end; the right arm takes the swab out by its cap, slides the whole tip
into the patient's left nostril (on the robot's right; tip centre 1.25 cm deep) and moves it round 6 times in 15.6 s
on a circle planned 4 mm into the wall, so that the compliant arm presses the foam on it; then the same in the right
nostril. It lines the swab up 2 cm outside the tube's mouth (a servo also aligns its axis), slides it in and pushes
the cap 2.5 cm past its seat while the left arm, back on the tube, holds it; then both arms let go and move clear.

Timeline of `demo.mp4` (planned phases): the patient's left nostril is sampled from 13.5 to 32.7 s (circling 15.6-31.2 s), the right nostril from 36.2 to 55.4 s (circling 38.3-53.9 s), and the swab goes back into the tube and the cap is pushed home from 61.4 to 67.0 s; the cap counts as home at 66.65 s (step 1,333). Both grippers are off the capped tube from 68.7 s (the left arm is back at its start pose at 70.3 s) until the run ends at 76.55 s (step 1,531): the last 7.8 s (10% of the video), once the cap has stayed home 9 s and the harness's 1 s success hold has passed.

| Variant | What it does | Score | Steps | Left nostril | Right nostril | Cap |
|---|---|---|---|---|---|---|
| `full` | the whole procedure | **1.0** | 1,531 | 6.00 / 0.84 / 225 / 12 / 0.99-2.55 N | 5.95 / 0.91 / 262 / 12 / 1.21-2.11 N | home at 66.7 s |
| `one_spot` | the tip pressed on one part of each wall and rubbed back and forth (+-30 degrees) | 0.021 | 1,573 | 0.25 / 0.92 / 167 / 4 / 0.99-1.70 N | 0.25 / 0.93 / 159 / 4 / 1.11-1.76 N | home at 66.7 s |
| `light` | the circles planned 1 mm inside the wall instead of 4 mm into it (no press) | 0.003 | 1,573 | 1.24 / 0.12 / 23 / 7 / 0.37-0.76 N | 0.17 / 0.22 / 35 / 5 / 0.41-1.12 N | home at 66.7 s |
| `one_nostril` | only the patient's left nostril sampled | 0.5 | 1,118 | 6.00 / 0.84 / 225 / 12 / 0.99-2.55 N | 0.00 / 0.00 / 0 / 0 / 0.00-0.00 N | home at 44.0 s |
| `lip` | the tip's end touches the upper lip on its way to the first nostril | 0 | 1,696 | 5.03 / 0.84 / 229 / 12 / 1.19-2.17 N | 6.50 / 0.92 / 274 / 12 / 1.19-1.89 N | swab voided: tip touched the face |
| `one_arm` | the left arm never holds the tube | 0.4 | 1,573 | 6.50 / 0.90 / 278 / 12 / 0.96-2.24 N | 5.93 / 0.91 / 265 / 12 / 1.10-3.03 N | not home (gap 0.53 cm; 0 step at >= 2 N; stand slid 4.1 cm) |

Per nostril: circles / share of at-depth steps pressed / moving pressed steps / sectors / median and largest pressed
force. From `demo_results.json`.

## Scoring

The rules are in `task.json` (`scoring`) and `score()`'s docstring. `report()` gives each nostril's circles, share,
pressed and moving steps, sectors, median and largest pressed force and depth; what voided the swab; and the cap's
gap, push, home step and how far the stand moved. A real trial applies the same numbers, the share included, to a
force log and the video (six deliberate rule differences: `real_trial/README.md`):

- **Force log:** the nose insert hangs on two load cells inside the head, one along the nostrils' long axis and one
  across the face (below), logged 80 times a second. They read the net side force on the nose, which is the foam's push
  on the wall while the foam is all that touches the nose: a 0.05 s step is pressed at 0.2 N or more, and the force's
  direction gives the tip's angle round the wall (on the ellipse, as in `task.py`). Anything else touching the nose
  while a tip is at depth (a gripper, the tube, a cable, the shaft bearing on a rim) voids that nostril (video).
- **At depth:** from an overhead video: the line 1.6 cm from the tip's end past the opening's rim, the 2.5 cm line
  outside. An LED flashes once when the log starts, which puts the log on the video's clock.
- **Score:** `real_trial/score_real_trial.py` runs `task.py`'s per-nostril tally on the log (share, moving pressed
  steps, sectors, circles): credit = min(circles, 4)/4 x min(1, share/0.7) x min(1, moving/200) x min(1, sectors/10),
  x 0.4 if the cap is not home; 0 if there is green on the foam, a gripper touched the foam, the tip touched the table,
  the 2.5 cm line went in or the swab was dropped. Circles are laps (all twelve sectors, or 10 over a full turn of
  pressed travel; a hop of over 60 degrees starts a new lap), not signed travel: rubbing friction tilts the measured
  force about 22 degrees whenever a stroke starts or turns back. Logs slower than 80 samples/s, not in newtons or not
  at zero at both ends are refused.
- **Checked:** `task.py`'s scorer probes as 80 Hz logs (friction 0.4 to 1.0, 3 mN noise): the same credit for full
  circles, also with up to 45 degrees missed a lap; at most 0.17 above `task.py` (0.44 for 120-degree hops), lower
  for other dabbing, fast circles and larger missed arcs (`real_trial/README.md`).
- **Cap home:** flush on the rim (photo) while the other hand holds the tube. Puritan publishes no push force for its
  plug-style cap: push one cap home on a tube standing on a 5 kg / 1 g kitchen scale before the trials and record it (a
  cap closed by hand is well within the YAM's ~40 N per finger); the real trial needs that full push to make the cap flush.
- **Not scored:** a wall force above 5 N (reported).

## Real-world trials

Per trial (about 5 min): a new swab; start the camera, then the force log with nothing touching the nose insert (it zeroes both
load cells and flashes its LED); run; stop the log 2 s after the swab is out; score from the log and the video.

Print in PLA (0.2 mm layers, 3 walls, 15% infill; the OBJ files are in metres, scale by 1000): the head's upper part
from `assets/head_upper.obj` face up, with supports in its cavity (about 0.55 kg), the base plate `assets/head_base.obj`,
the nose insert `assets/nose_insert.obj` (about 17 g) with the nostril axes vertical (rotate it 60 degrees about its
left-right axis; the bores need no supports), and the mounts `assets/rig_corner.obj` and `assets/rig_arm.obj`. Print
the stand from `assets/tube_stand.obj` and glue washers under it (stand and tube about 100 g). Puritan's tube is 15.4 cm
long (153.975 mm, polypropylene), 1.1 cm shorter than the simulated 16.5 cm tube: put an 11 mm printed spacer between
the stand's end stop and the tube's closed end, so the mouth sits where the simulation puts it. Lay the tube unglued in
the stand; leave the stand loose. One new sterile swab (Puritan 25-1506 1PF BT BL or similar) per trial.

- **Load cells:** two 1 kg bar load cells, two HX711 boards at 80 samples/s and an Arduino running
  `real_trial/force_logger/force_logger.ino`, with an LED in view. One cell lies on the base plate's riser (across the
  face); the other slopes 30 degrees on it (along the nostrils' long axis) and carries the arm into whose seat the
  insert is glued, at least 1.5 mm clear of the head all round. Build and calibration (each cell with 20, 50 and 100 g;
  each session, 20 to 300 g hung from a nostril and a 300 g press on a kitchen scale read within 5%): `real_trial/README.md`.
- **Depth:** lines round the shaft at 1.6 cm from the tip's end (hidden while circling) and at 2.5 cm (stays outside).
- **Camera:** a phone on an overhead holder, lens about 45 cm above the table over the face's centre line, 8 to 12 cm
  toward the chin from the nostrils, looking down into both openings, with both shaft lines, the handle and the LED in
  view (from beside the head the nose hides the openings' edges); check in the first run that no arm passes near it.
- **Contamination:** green washable marker on the upper lip, on the skin beyond each rim (1.6 times the opening's
  half-widths, as `task.py`: 3 mm beyond its sides, 4 mm beyond its ends), on the tube's outside and on the stand; any
  green on the foam voids the swab, as does a gripper touching the foam (video).

Everything is dry, blunt and light (the swab weighs about 5 g). Apart from swabs and a 3D printer, the materials
(filament, washers, markers, a kitchen scale, load cells, amplifier boards, an Arduino and a phone holder) cost under
US$150.

## Simulation fidelity in full

Beyond `task.json`'s fidelity text: the head is kinematic (1.5 kg in simulation, about 0.65 kg printed) and collides
as its exact triangle mesh; the bores are elliptical, 1.4 x 1.0 cm and 2.6 cm deep, axes 30 degrees below horizontal
(real vestibules are irregular and soft); the eyes, brows, lips and ears are visual only. In real trials the nose
insert hangs on the load cells 1.5 mm clear of the rest of the head; the simulated head is one rigid mesh. The swab (5 g, estimated) is
boxes and spheres; the demo plans its circle 4 mm into the wall and the compliant arm turns that into the press.
Foam-on-head friction 0.45 / 0.40 (estimate). The tube (1.4 / 1.12 cm across, estimated; 16.5 cm long) and its stand
are one free 100 g body; the plug slides freely in the bore (no friction fit; the real cap needs its full push,
measured before the trials). Contact points and forces are read once per control step.
