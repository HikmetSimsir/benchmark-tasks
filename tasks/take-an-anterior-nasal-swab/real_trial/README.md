# Real trials: the load-cell nose insert, the force log and the real-trial score

The simulation decides from PhysX contact forces whether the foam tip is pressed on a nostril's wall (at least 0.2 N)
and where round the wall it is. In a real trial the printed nose insert, which holds both nostrils, hangs on two load
cells inside the head, so the same two things are logged 80 times a second for the whole trial:

- **pressed:** the force across the nostrils (perpendicular to their common axis) is at least 0.2 N;
- **where:** a tip pressing the wall pushes it outward along the wall's normal at the contact point, so the force's
  direction gives the tip's angle round the elliptical bore (task.py's angle: theta = atan2(B sin phi, A cos phi)).

The cells read the net force on the insert, which is the foam's push on the wall while the foam is the only thing
touching the nose; anything else touching the nose while a tip is at depth (a gripper or finger, the tube, a cable, the
shaft bearing on a rim) voids that nostril, from the video. `score_real_trial.py` runs `task.py`'s per-nostril tally on
the log (share, moving pressed steps, sectors, circles) with the same numbers and the at-depth times read from the
video; its docstring lists the six deliberate differences (below: 'Check against task.py').

## Parts

| Part | Notes |
|---|---|
| 2 x 1 kg straight-bar load cell | 80 x 12.7 x 12.7 mm, tapped M4 and M5 end holes, 1.0 mV/V (TAL220-style; about US$5 each); rated 9.8 N, so a collision can overload one: `score_real_trial.py` flags a log peak above 9 N (`recheck_rig`) |
| 2 x HX711 amplifier board | set to 80 samples/s: Adafruit HX711 (Rate switch at H) or SparkFun HX711 (cut the RATE jumper) |
| Arduino Nano or Uno, USB cable | runs `force_logger/force_logger.ino` ("HX711 Arduino Library" by Bogdan Necula) |
| LED + 220 ohm resistor | flashes once, when the log starts (the video's sync mark); tape it beside the head, facing the phone |
| Phone and overhead holder | 4K video; a clamp-on gooseneck or boom phone holder reaching about 45 cm above the table |
| Screws | 4 x M3 x 12 self-tapping (base plate), M4 and M5 screws for the cells' end holes (length: part thickness + 6 mm) |
| Printed parts | `assets/head_upper.obj`, `assets/head_base.obj`, `assets/rig_corner.obj`, `assets/rig_arm.obj`, `assets/nose_insert.obj` |
| Checks | 20, 50, 100 and 300 g weights (or coins weighed on the kitchen scale), the kitchen scale (5 kg / 1 g), thread, a paper clip, a pencil, a block 8.4 cm high, a strip of thin card (about 0.5 mm) |

## Build

Cross-sections of the assembled rig: `rig_sections.png` (a: centre line, the insert's arm on the tilted cell;
b: 10 mm off centre, the flat cell).

1. Print in PLA (0.2 mm layers, 3 walls, 15% infill; OBJ files in metres, scale by 1000). The head's upper part goes
   face up with supports inside its cavity; the base plate flat; the nose insert with its nostril axes vertical.
2. Flat cell (across the face): lay it on its side against the base plate's riser and screw its fixed end through the
   riser's slots into its end holes. It sits 2.6 mm above the plate; nothing may touch its middle.
3. Tilted cell (along the nostrils' long axis): screw its fixed end through the corner block's pad (the screw-access
   slot is under the pad), then screw the corner block's side plate to the flat cell's free end. The tilted cell now
   slopes 30 degrees, free end up toward the chin.
4. Screw the arm's foot onto the tilted cell's free end (from above). The arm's post ends in a seat shaped like the
   insert's underside: glue the insert into it (CA glue) with the nostril openings toward the chin.
5. Wire each cell to its HX711 (red E+, black E-, white A-, green A+), the U board (tilted cell) to pins 2 (data) and 3
   (clock), the V board (flat cell) to pins 4 and 5, both boards' VCC to 5 V and GND to GND, the LED from pin 6 through
   the resistor to GND. Tape the tilted cell's leads to the corner block with a slack loop of about 3 cm (a taut lead
   would carry force past the flat cell), then run both cables along the base plate's groove, out at the crown end.
6. Lower the upper part over the stack: the post rises through the channel and the insert enters its pocket, at least
   1.5 mm clear of the head all round (1.6 mm in the model). Slide the card strip all the way round the insert: it must
   not catch anywhere. Screw the base plate on (4 x M3). Tap the head anywhere but the insert: the log must
   not move. Tape the head to the table face up, crown away from the robot, as in the simulation.

## Calibrate (once) and check (each session)

- **Each cell, before assembly**, like a kitchen scale: clamp its fixed end with the cell horizontal and its end holes
  vertical; connect it as the U board; open a serial monitor at 115200 baud and send `r` for raw counts (zeroed at
  start). Note the mean count with nothing, then with 20, 50 and 100 g hung by a thread from the free end's outer hole.
  Counts per newton = count change / (mass in kg x 9.81) from a straight-line fit; enter it in `COUNTS_PER_N_U` or
  `COUNTS_PER_N_V`. Then the signs: with the head assembled, press the insert lightly toward the nose tip; `f_u_n` must
  rise. Press it toward the robot's left (the patient's right); `f_v_n` must rise. Flip a sign if not.
- **In place, each session and after any knock.** Restart the log before each part (it re-zeroes in that position,
  with the insert's own 17 g); the other reading must stay within 2% of a hung load and 5% of a pencil press (a pencil
  1 degree off vertical already puts 1.7% of the press on the other cell).
  - across the face: lay the head on its patient's-right side (the robot's left side down) with the base plate's
    underside held flat against an upright box side, so +v points straight down (on its curved side alone the head
    rests on a facet 1.8 to 9 degrees off and up to 14% of the load shows on `f_u_n`); set the foot of an L-bent paper clip inside the lower nostril (the bores are blind, 26 mm deep) and hang 20, 50 and 300 g
    from the clip by a thread over the opening's lower rim, where it touches only the nose: `f_v_n` reads 0.196, 0.49
    and 2.94 N within 5% (300 g is above the demo's largest press, 2.55 N).
  - along the long axis: put the head on the kitchen scale with its crown end on a block 8.4 cm high (block and head on
    the scale; the base tilts 30 degrees and the nostrils' axis is level), tare, and press straight down on the nose
    with a pencil's eraser until the scale reads 300 g; hold 3 s: `f_u_n` reads -2.94 N within 5%.
  - with a load along the nostrils: the same press with the head flat on the scale: `f_u_n` reads -2.55 N within 5%
    (the press is 30 degrees off -u; its 1.47 N along the nostrils' axis must not show in either reading).
  - noise: untouched for 10 s, both readings stay within 0.01 N.

## Run and score a trial

1. New swab. Phone recording from overhead: lens about 45 cm above the table over the face's centre line, 8 to 12 cm
   toward the chin from the nostrils, looking down into both openings, with both shaft lines, the handle and the LED in
   view (from beside the head the nose hides the openings' edges). In the first run, check that no arm passes near it.
2. Start `python record_log.py <port> trial_NN.csv` with nothing touching the nose: the board zeroes both cells, prints
   the header and lights the LED for 0.5 s (the only time it lights).
3. Run the trial. Keep logging until the swab is out of the nose (take it out by hand if the robot left it in) and
   nothing has touched the nose for 2 s, then press Ctrl-C.
4. From the video note: the LED's first lit frame (`--sync`); for each nostril, the times the line 1.6 cm from the tip's
   end passes the opening's rim going in and coming back out (a glimpse of it through the nostril's open floor while
   the tip circles is not 'out'), with the 2.5 cm line still outside (`--left`, `--right`; several pairs are
   allowed); a voided swab (`--void`): green on the foam, a gripper on the foam, the tip touching the table, the 2.5 cm
   line inside a nostril or the swab dropped; a voided nostril (`--void-nostril left` or `right`): anything but the foam touching the nose while that
   nostril's tip is at depth (a gripper or finger, the tube, a cable, the shaft bearing on a rim); and the cap
   (`--cap-home`: flush on the rim in a photo, pushed while the other hand held the tube).
5. `python score_real_trial.py trial_NN.csv --sync 12.40 --left 15.2 33.0 --right 37.1 55.6 --cap-home`. It refuses a
   log slower than 80 samples/s, not in newtons, or not at zero in its first and last second, and prints each
   nostril's circles, share, moving pressed time, sectors, median and largest force, its credit and the score.
   A log refused at its end because the robot left the insert loaded or knocked it off zero scores 0 (both
   nostrils); after it, or after `recheck_rig`, repeat the in-place check before the next trial.

The rules and numbers are task.py's: a 0.05 s step (the mean of its 4 samples) is pressed at 0.2 N or more; moves of
more than 60 degrees between pressed steps do not count and start a new lap (difference 5); share = pressed steps / at-depth steps (at least 0.7); at least 200
moving pressed steps (10 s; a move of at least 1 degree); at least 10 of the 12 sectors; credit = min(circles, 4)/4 x
min(1, share/0.7) x min(1, moving/200) x min(1, sectors/10); score = the mean of the two nostrils' credits, x 0.4 if
the cap is not home, 0 if voided.

## Check against task.py

Six rules differ, on purpose (`score_real_trial.py`'s docstring):

1. Circles are laps: all twelve sectors pressed since the last lap, or at least 10 of them over a full turn of
   continuous pressed travel. `task.py` takes the larger of the signed travel and the laps, but rubbing friction (about
   0.4) tilts the measured force about 22 degrees toward the direction of travel, and that lead jumps whenever a stroke
   starts, pauses or turns back, which would add or remove apparent travel.
2. For the same reason a pressed step moving the other way from the last second's turning does not count as moving.
3. While the tip slides, friction adds to the measured force (8% at 0.4), so a sliding step counts as pressed from
   about 0.19 N of wall force; a still one from 0.20 N, as in `task.py`.
4. The log holds one net force, so `task.py`'s exclusion of a tip wedged across the nostril's axis has no counterpart:
   a wedged swab loads the insert only as hard as the robot pushes it sideways.
5. A turn of more than 60 degrees between pressed steps starts a new lap, as a lift does (`task.py` ignores a turn of
   more than 90 degrees): the HX711's 50 ms settling, or steps half a step off the robot's, can hide a one-step lift
   between dabs, and star-order dabbing would then sweep laps.
6. Anything but the foam touching the nose while a tip is at depth voids that nostril (video); `task.py` reads only the
   foam's own contact points.

`check/check_real_scorer.py` feeds the scorer probes used on `task.py` (stubbed simulator state, no Isaac Sim) to
`task.py` and, as synthetic 80 Hz logs of the same presses (friction 0.4 along the travel unless stated, 3 mN noise per
axis, a wedged tip's opposite-wall forces cancelling, 2 s untouched before and 1.5 s after; also with the HX711's 50 ms settling and with the steps half a step off the
robot's), to `score_real_trial.py`.
Nostril credit:

| Probe | task.py | real log |
|---|---|---|
| 5 pressed circles in 16 s | 1.000 | 1.000 |
| 2 circles one way, 2 the other | 1.000 | 1.000 |
| 6 circles, sticking 15% / force below 0.2 N on 12% of steps | 1.000 | 1.000 |
| 6 circles, sticking 25% / below 0.2 N on 15% | 0.915 | 0.925 |
| one-spot ratchet (pressed strokes, unpressed returns) | 0.002 | 0.009 |
| ratchet, then one circle | 0.250 | 0.292 |
| ratchet, then 12 wedged near-axis steps | 0.002 | 0.012 |
| star-order dabs, 6 x 2 degrees each | 0.472 | 0.021 |
| star-order dabs, 6 x 1.2 degrees each | 0.250 | 0.000 |
| 4 fast circles (37 steps), then a +-1.5 degree wiggle | 1.000 | 0.680 |
| forward ratchet: 3 strokes on, 1 back off, x80 | 0.517 | 0.587 |
| side to side across the nostril | 0.000 | 0.000 |
| +-30 degree wiggle at one spot | 0.004 | 0.019 |
| 4 circles in 0.8 s, then still | 0.008 | 0.000 |
| tip wedged across the axis | 0.000 | 0.000 |
| pressed in one spot | 0.000 | 0.000 |
| circles at 0.1 N (not pressed) | 0.000 | 0.000 |
| 6 circles, unpressed 30 or 45 degree arc each lap, 36 starting angles, friction 0.4 and 0.8 | 1.000 | 1.000 at every angle |
| 6 circles, unpressed 60 degree arc each lap, 36 angles | 1.000 | 1.000 at 0.4; 4 of 36 below 0.9 at 0.8 |
| 6 circles, unpressed 75 degree arc each lap, 36 angles | 1.000 | 11 (0.4) and 14 (0.8) of 36 below 0.9, down to 0.037 |
| 6 circles, unpressed 90 degree arc each lap, 36 angles | 0.900-1.000 | 22 of 36 below 0.9, median 0.188 (0.4) and 0.302 (0.8) |
| 6 circles, unpressed 120 degree arc each lap | 0.819 | 0.018 |
| star-order dabs, 6 x 1.2 and 6 x 2 degrees, one-step lifts hidden by the HX711's settling | 0.250, 0.472 | 0.000, 0.021 |
| the same dabs, steps half a step off the robot's | 0.250, 0.472 | 0.000, 0.021 |
| the same dabs with no lift (the tip hops across in one step) | 1.000, 1.000 | 0.000, 0.021 |
| dabs hopping 120 degrees at a time, one-step lifts, settling and half-step offset (friction 0.8) | 0.125 | 0.562 |
| 5 circles in 16 s, friction 0.8 | 1.000 | 1.000 |
| 6 circles, sticking 15% / below 0.2 N 12%, friction 0.8 | 1.000 | 1.000 |
| 5 circles in 16 s, friction 1.0 | 1.000 | 1.000 |
| 6 circles, sticking 15% / below 0.2 N 12%, friction 1.0 | 1.000 | 1.000 |

Full circles score the same, also with an unpressed arc of up to 45 degrees a lap at any starting angle (60 at friction
0.4) and at friction 0.8 and 1.0; a 75 to 90 degree arc missed at the same place every lap can drop the real credit as low as
0.02 (median 0.19-0.30 at 90 degrees) where `task.py` keeps 0.9-1.0. The real log is at most 0.07 above `task.py` (forward ratchet 0.587 vs 0.517),
0.17 with the HX711's settling and the steps half a step off (forward ratchet), except dabs that hop about 120 degrees
at a time, which then reach 0.562 (task.py 0.125); it is lower for star-order dabbing, fast circles and
larger missed arcs (120 degrees: 0.018 vs 0.819). The check also shows
what the log cannot do alone: a 1.0 N contact by something else from 8 s into five good circles gives 0.542, and a
shaft rolled round a rim with the foam touching nothing gives 1.000 (`task.py`: 0); both are voided from the video. It
refuses logs at 10 samples/s, in raw counts, or loaded at their start or end, and at-depth times outside the log, and a logger clock running 0.5% slow
(an Uno's resonator) is corrected from the PC's times (share 1.00; 0.96 uncorrected). Run from `real_trial/check`:
`python check_real_scorer.py` (results in `check_real_scorer_results.json`).
