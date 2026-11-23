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
  with at least 0.2 N (about 20 g, the press the real trial's calibrated ink needs; the demo presses at a median 1.0 to 1.2 N;
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
| `assets/head_shell.obj`, `assets/nose_insert*.obj` | The head for printing: shell, and a nose insert holding both bores (one piece, or two pinned halves) |
| `assets/tube_stand.obj` | The printable tube stand (with an end stop) |
| `assets/face_*.obj` | Visual-only face details (sockets, eyelids, brows, lips, ears): no collision, not printed |
| `demo.py`, `democore.py` | The scripted demo and its variants (`democore.py`: runner and planning helpers) |
| `grasp.json` | The grasp found by `demo.py`'s IK search (delete to search again, about 20 min) |
| `demo_results.json` | Each variant's score, end-state report and planned phase times |
| `make_task_json.py` | Writes `task.json` from `task.py`'s constants (stops if they no longer match the text) |
| `setup_shot.py` | Writes the top camera's starting view |

`task.py` registers the swab-head and swab-tube pairs with `kitchenkit.watch_points`, so the scorer reads every
contact point between them and its normal force each step. Standard `yam_arena` embodiment and `task_score` scorer.
Assets: all meshes in `assets/` (head, printable shell, nose insert and halves, tube stand, face details) were made for this
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

The left arm pinches the tube near its closed end while the right arm takes the swab out by its cap, then lets go. The right arm turns the swab to the patient's left nostril (on the robot's right), holds the tip 1 cm outside it, slides the whole tip in (tip centre 1.25 cm deep) and moves it round the nostril 6 times in 15.6 s on a circle planned 4 mm into the wall, so that the compliant arm presses the foam on it; then the same in the patient's right nostril. It turns the swab back to the tube, lines it up 2 cm outside the mouth (a servo also aligns the swab's axis), slides it in and pushes the cap 2.5 cm past its seat while the left arm, back on the tube, holds it; then both arms let go and move clear.

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
gap, push, home step and how far the stand moved. A real trial scores the same rules, read differently:

- **Pressed and sectors:** wiped ink instead of PhysX force: a sector counts when its ink is wiped (below).
- **Circles and time:** from the video: the turns the handle makes round each nostril, and the seconds it moves round,
  with the 1.6 cm line hidden. Real credit per nostril = min(turns, 4)/4 x min(1, wiped sectors/10) x min(1,
  seconds/10) (the share factor is simulation-only), x 0.4 if the cap is not home; 0 if there is green on the foam or a gripper touched the foam.
- **Cap home:** flush on the rim (photo) while the other hand holds the tube. Puritan publishes no push force for its
  plug-style cap: push one cap home on a tube standing on a 5 kg / 1 g kitchen scale before the trials and record it (a
  cap closed by hand is well within the YAM's ~40 N per finger); the real trial needs that full push to make the cap flush.
- **Not read:** the wall force (the 5 N report is simulation-only).

## Real-world trials

Per trial (about 10 min): a new swab; wipe and re-ink both nostrils (2 coats, 2 min) and pass the 20 g / 5 g stroke
check; run; open the insert and take two photos; score from the video and the photos.

Print in PLA (0.2 mm layers, 3 walls, 15% infill; the OBJ files are in metres, scale by 1000): the shell from
`assets/head_shell.obj` face up (about 0.65 kg), and the nose insert from `assets/nose_insert.obj` (about 17 g) with
the nostril axes vertical (rotate it 60 degrees about its left-right axis; the bores need no supports). Press-fit the
insert into the shell's pocket without glue (sand it until it holds), so it can come out after a trial. Better, print
it as two halves split along the plane through both nostril axes (`assets/nose_insert_half_top.obj`,
`assets/nose_insert_half_floor.obj`, each on its cut face), joined by two 3 x 12 mm pins, so each half-bore can be
photographed flat. Print the stand from `assets/tube_stand.obj` and glue washers under it (stand and tube about
100 g). Puritan's tube is 15.4 cm long (153.975 mm, polypropylene), 1.1 cm shorter than the simulated 16.5 cm tube:
put an 11 mm printed spacer between the stand's end stop and the tube's closed end, so the mouth sits where the
simulation puts it. Lay the tube unglued in the stand; leave the stand loose. Tape the head face up, crown away from
the robot. One new sterile swab (Puritan 25-1506 1PF BT BL or similar) per trial.

- **Ink:** coat the inside of each nostril with black dry-erase marker (e.g. EXPO Low Odor, chisel tip): two coats,
  2 min drying. Check the coat on a printed test strip on a kitchen scale: a swab tip drawn once 1 cm across it at
  20 g (0.2 N) must leave a bare stripe at least 2 mm wide, and at 5 g none. Mark 12 ticks round each opening, one
  every 30 degrees.
- **Depth:** lines round the shaft at 1.6 cm from the tip's end (hidden while circling) and at 2.5 cm (stays outside).
- **Camera:** a phone on a tripod beside the head on the robot's left, lens about 20 cm from the nose at nostril height
  (about 16 cm above the table), aimed at the openings, with both shaft lines and the handle in view. Keep it off the nostril
  axis on the chin side: that is the swab's way in (the gripper passes about 12 cm out along it, 20 to 22 cm up).
- **Contamination:** green washable marker on the upper lip and on the skin beyond 8 mm of each opening; any green on
  the foam voids the swab, as does a gripper touching the foam (video).
- **After each trial:** take the insert out, open the halves and photograph each bore against its ticks (or use a USB
  inspection camera on the one-piece insert); count the wiped sectors (of 12).

Wipe the nostrils clean and re-ink between trials. Everything is dry, blunt and light (the swab weighs about 5 g).
Apart from swabs and a 3D printer, the materials (filament, washers, markers, a kitchen scale) cost well under US$100.

## Simulation fidelity in full

Beyond `task.json`'s fidelity text: the head is kinematic (1.5 kg in simulation, about 0.65 kg printed) and collides
as its exact triangle mesh; the bores are elliptical, 1.4 x 1.0 cm and 2.6 cm deep, axes 30 degrees below horizontal
(real vestibules are irregular and soft); the eyes, brows, lips and ears are visual only. The swab (5 g, estimated) is
boxes and spheres; the demo plans its circle 4 mm into the wall and the compliant arm turns that into the press.
Foam-on-head friction 0.45 / 0.40 (estimate). The tube (1.4 / 1.12 cm across, estimated; 16.5 cm long) and its stand
are one free 100 g body; the plug slides freely in the bore (no friction fit; the real cap needs its full push,
measured before the trials). Contact points and forces are read once per control step.
