# Swap the hotend on a Bambu Lab A1 mini 3D printer: buckle open, old hotend to its holder, new one seated, locked

A Bambu Lab A1 mini 3D printer stands on the table, powered off and cold, its front toward the robot. The toolhead's
front cover and silicone sock are off and the filament is cut, as Bambu's guide asks before a hotend change. Under the
toolhead the installed 0.4 mm hotend sits in its pocket, its front lug just above the closed buckle's bar. In front of the
printer stands a printed holder with two slots: the new 0.2 mm hotend (green tag) stands in the right one, the left one
is empty. The instruction:
"Change the 3D printer's hotend: open the buckle, take the old hotend out and stand it in the empty slot of the holder, then push the new hotend up into the toolhead until it seats and lock the buckle."

The procedure is Bambu Lab's for A1-series printers
([Hotend Replacement for A1 Series](https://wiki.bambulab.com/en/a1/maintenance/replace-hotend); the A1 mini takes
the same hotend): push the nozzle buckle to unlock it and swing its left side outward, hold the heatsink and pull the
hotend out, put the new hotend in until it sits flush (a built-in magnet aligns it), then close the buckle, left side
first. If the buckle will not lock, the hotend is not seated; the wiki's check afterwards is that the hotend is held
with no wobble. Owners swap hotends to clear clogs, replace worn or damaged nozzles, or change nozzle size. What it
tests: seating a small part overhead, half hidden under the toolhead, between unlocking and locking, in a fixed order.

- **Out, and put away.** The old hotend must end up standing in a holder slot (upright, its heatsink on the slot's
  boss). If it is dropped on the way, that part earns nothing.
- **Seated, not just pushed in.** The new hotend counts as seated only with its top within 1.5 mm of the pocket's
  top, its axis within 2.5 mm of the seat and upright to 4 degrees; the buckle counts as locked only over a seated
  hotend. The catch that stands in for the A1's magnet holds a hotend only once it is pushed fully home: one let go
  short of its seat slides out and falls (the `half_in` variant).
- **Locked and let go.** The buckle within 3 degrees of its closed stop, no finger within 1 cm of the new hotend or the
  buckle's tab, and the new hotend still for 1 s. Dropping the new hotend voids the run (score 0).

## Files

| File | What |
|---|---|
| `task.py` | The task: printer (block model) with toolhead, pocket, buckle and sprung catch; two hotends; the holder; `success()`, `score()`, `report()` |
| `kitchenkit.py` | Parts from boxes and cylinders, joints (hinge, sprung slide), per-step poses and finger pads |
| `demo.py`, `democore.py` | The scripted demo and its variants (`democore.py`: runner, planning and object-servo helpers) |
| `demo_results.json` | Each variant's score, end-state report and per-phase tracking error |
| `make_task_json.py` | Writes `task.json` from `task.py`'s constants (stops if they no longer match the text) |
| `setup_shot.py` | Writes the top camera's starting view |

Standard `yam_arena` embodiment and `task_score` scorer. Assets of our own: none; every part is boxes and cylinders
built in `task.py`. Third-party assets and licences: the YAM arm model (i2rt, github.com/i2rt-robotics/i2rt, MIT;
`LICENSE.i2rt` in yam_arena); the `station` scene and the `yam_arena` embodiment
(github.com/kairosiann/yam-isaac-lab-arena; its README states it has no licence yet); Isaac Lab-Arena (Apache-2.0);
Isaac Lab (BSD-3-Clause).

## Run a trial

In the Isaac Lab-Arena environment from the simulation walkthrough, from this folder:

```bash
inspect-robots run --embodiment yam_arena --policy dream -P rows_per_request=12 \
  -E task=task.py -E object_jitter=0 -E control_hz=20 -E cam_width=320 -E cam_height=176 \
  --instruction "Change the 3D printer's hotend: open the buckle, take the old hotend out and stand it in the empty slot of the holder, then push the new hotend up into the toolhead until it seats and lock the buckle." \
  --scorer task_score --max-steps 2400 --store-frames --log-dir logs/hotend-swap-dream
```

`-P rows_per_request=12` asks Dream-1 for a new chunk every 12 steps; with the default 48 rows a simulator slower than
real time lets the Dream session expire between chunks. `task_score` prints 1.0 on success, otherwise `score()` at the
end. **Seeds:** none; the layout is fixed (`object_jitter=0`). **Runtime:** the recorded full demo ran 868 control steps (43.4 s simulated at 20 Hz) in 5.1 min of wall-clock time on one NVIDIA RTX PRO 6000 Blackwell GPU shared with two other simulations, start-up and video writing included. The Dream-1 run reached the 2,400-step limit with a score of 0 in 10.5 min of wall-clock time (mean model response 0.75 s), on the same GPU: its right gripper went to the front of the toolhead and its left arm reached over the printer, but it never opened the buckle; the top camera's last frame shows the printer and the holder as at the start (old hotend in the toolhead, new one in its slot). A model trial runs up to 2,400 steps plus the policy's response time.

## Scripted demo

```bash
python demo.py task.py demo_out                       # full: demo.mp4, setup.png, result.json
python demo.py task.py out_no_lock --variant no_lock  # any variant below; --no-record skips the video
python demo.py task.py --plan-only                    # inverse-kinematics check of every variant's plan
```

The right arm pinches the buckle's tab and swings the buckle open to its 90-degree stop (6.2-9.2 s). The left arm pinches the old hotend's heatsink from the side, 4 cm below its top (the YAM's finger plates are about 4 cm tall there, so a higher pinch would run into the toolhead's underside), pulls it straight down out of the pocket (13.8-15.8 s), carries it to the holder, lowers it into the empty left slot (19.3-20.8 s) and lets go. Meanwhile the right arm takes the new hotend out of the right slot (18.5-21.0 s), brings it under the pocket, raises it to the seat and pushes 6 mm further (26.1-30.1 s; the compliant arm presses the heatsink against the pocket's top), and lets go: the sprung catch holds it (30.7-31.5 s). It then pinches the tab again, swings the buckle shut under the lug and presses it against its stop (37.9-40.9 s), lets go (41.5 s) and moves away. The script reads the hotends' poses each step and steers each held hotend (the old one by its nozzle's tip), not the gripper, along the plan, as any scripted policy with full state may.

Timeline of `demo.mp4` (planned phases): the old hotend is out of the toolhead at 15.8 s and in its slot at 20.8 s; the new hotend is seated at about 29 s; the buckle is shut at 40.4 s. No finger is near the hotend or the tab from 41.5 s, and the run ends at 43.4 s (step 868) once the finished state has held 1 s plus the harness's 1 s success hold. End state: the new hotend's top 0.7 mm below the pocket's top, tilt 1.3 degrees, the buckle at 0.3 degrees, the old hotend in the empty slot.

| Variant | What it does | Score | Steps | End state |
|---|---|---|---|---|
| `full` | the whole procedure | **1.0** | 868 | old hotend in the empty slot; new one seated (top 0.7 mm below the pocket's top, tilt 1.3 deg); buckle at 0.3 deg; success |
| `no_lock` | the buckle is left open | 0.6 | 804 | old hotend in its slot; new one seated; buckle open at 89.9 deg |
| `half_in` | the new hotend is pushed in 2.5 mm short of its seat and let go; then the buckle is swung shut | 0 | 980 | short of the catch's tip, the catch pushes the hotend back down; it falls out of the pocket onto the bed (dropped) |
| `drop_old` | the old hotend is let go over the bed instead of in the holder | 0.8 | 988 | old hotend on the bed (dropped); new one seated, buckle at 0.2 deg, hands off |
| `drop_new` | the new hotend is let go over the bed on its way to the toolhead | 0 | 689 | new hotend on the bed (dropped); old one in its slot; buckle left open |

From `demo_results.json`.

## Scoring

The rules are in `task.json` (`scoring`) and `score()`'s docstring; `report()` gives the buckle's angle, each
hotend's pose relative to the toolhead and the holder, whether it was dropped, and the hands-off and hold counters.

Score = 0.2 (old hotend standing in a holder slot, not dropped on the way) + 0.4 (new hotend seated) + 0.3 (buckle
locked with the new hotend seated) + 0.1 (that finished state held 1 s with both hands off and the new hotend still); 0 if
the new hotend is dropped. The run is a success, and ends, once the finished state with the old hotend in a slot has
held for 1 s.

A real trial scores the same rules from photos and the video:

- **Old hotend in a slot:** a photo of it standing upright in either slot (not lying, not on the bed or table).
- **Locked:** the buckle closed and latched in the end photo.
- **Finished:** no part of either gripper touches the new hotend or the buckle in the last second (video).
- **Seated:** after the end photo, a strip of printer paper (about 0.1 mm) does not slide between the heatsink and the
  heating assembly, and the buckle locks over the hotend (Bambu: it will not lock over an unseated one). If the robot
  left the buckle open, the scorer closes it by hand without touching the hotend; that does not earn 'locked'.
- **Dropped:** the new hotend falling or set down on the bed, the table or the floor voids the run.

## Real-world trials

Per trial (about 5 min): put the old hotend back and lock the buckle, stand the new one in the holder's right slot,
check the printer is off and cool, run, then photograph the end state and do the wiggle check.

- **Printer:** a Bambu Lab A1 mini (US$199 on sale, US$219 list at Bambu's US store, Nov 2026). Before the trials,
  with the printer on, raise Z so the toolhead's underside is 20 cm above the table and park the toolhead over the
  bed's centre, then cut and unload the filament with the toolhead's lever, take off the front cover and the silicone
  sock (Bambu's guide), and switch the printer off. Let the nozzle cool below 50 C. Place the printer so the installed
  hotend's axis is 37.5 cm in front of the arm bases' midpoint, on their midline (y 0); the block model's base
  coordinates in `task.json` are for the simulation only. Mark the printer's feet on the table with tape; it stands
  loose (5.5 kg). Powered off, the toolhead slides along the X arm: tape its parked position on the arm and slide it
  back before each trial.
- **Hotends:** two Bambu Hotend - A1 Series units (about US$10-13 each): a 0.4 mm one installed and locked, a 0.2 mm
  one as the new hotend with a strip of green tape on its heatsink's front. Swap their roles freely between trials.
- **Holder:** print it in PLA (0.2 mm layers, 15% infill, about 200 g): a 4 x 16 x 8 cm block with two bosses on top,
  each 1.1 x 1.8 x 2 cm with a 0.9 cm square hole down its middle, 13 cm apart (positions in `task.json`'s setup). It
  stands loose on the table, its front face 23 cm in front of the arm bases' midpoint (against the printer's front
  edge if the real base reaches further forward), slots at y -3.5 (new) and 9.5 (empty). Check that a real A1 hotend
  stands in the 0.9 cm hole with its heatsink resting on the boss; widen the hole if needed.
- **Camera:** a phone on a tripod at the front left, at the toolhead's height (about 20 cm), aimed at the buckle and
  the heatsink, plus the station's top camera.
- **Safety:** the printer is off and cold, nothing is heated; a hotend weighs about 20-30 g; nothing is sharp. The
  YAM's ~40 N per finger is far above what the buckle and the magnet need.

## Simulation fidelity in full

Beyond `task.json`'s fidelity text: every part is a rigid body built from boxes and cylinders. The printer (one loose 5.5 kg body, friction 0.8) keeps what the job touches: base and bed, the Z column at the right rear, the X arm and carriage behind the toolhead, and the toolhead with its pocket, window, catch and buckle. The toolhead is part of the printer body; with the power off the real carriage can be slid along X by hand. The hotend (22 g, estimated; friction 0.8 for the finned heatsink) is a 1.2 x 1.8 x 4.6 cm heatsink with a 0.7 x 1 x 0.4 cm lug and a 0.7 cm nozzle, 6 cm overall; the real A1 hotend is 4.73 cm long (Bambu's listing) with a shorter, wider heatsink. On the A1 the hotend's top goes up into the extruder and its magnet pulls it back against the heating assembly; here its top goes 1.2 cm up into a pocket with 1.5 mm of side clearance, and a sprung wedge in the pocket's back wall (a 120 N/m slide, about 0.4 N on a seated hotend) presses it against the front wall so that friction holds it. The A1's buckle is unlocked by pushing it to the right and then swung open; here it is a 6 g bar on a damped vertical hinge (0 to 90 degrees) whose closed position lies 1.5 mm under the lug of a seated hotend. The holder is a block with a 1.1 cm wide boss under each slot, so the gripper's finger plates pass either side of it. Not simulated: the push to the right that unlocks the real buckle and the lock of its right side; the
real hotend goes in tilted slightly back and its magnet pulls it back flush against the heating assembly (here the
catch presses it forward). Finger pads and part poses are read once per control step.
