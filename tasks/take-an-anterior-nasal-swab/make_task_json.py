"""Writes task.json from task.py's constants and the texts below (so instruction and numbers cannot drift)."""
import importlib.util
import json
import math
import sys

scores = sys.argv[1] if len(sys.argv) > 1 else "Dream-1 run: pending; demo: 1.0"  # read before argv is cleared
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location("t", "task.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
SRC = open("task.py").read()  # for the few values written inline in task.py rather than as named constants
assert (t.SCORE_OVER, t.F_WALL, t.F_STRAY, t.RIM, "r <= 1.6" in SRC, round(t.DEPTH_MIN, 4), round(t.DEPTH_MAX, 4), t.CIRCLES, t.SHARE,
        t.PUSH_N, t.PUSH_STEPS, t.SEAT_TOL, t.RELEASE, "math.cos(math.radians(6.0))" in SRC, "< 0.003" in SRC,
        "tip_low < 0.0015" in SRC, "float(sp[2]) - TOP < 0.012" in SRC, "push_run\"] >= PUSH_STEPS" in SRC,
        "swab * (1.0 if cap_ok else 0.4)" in SRC, t.F_MAX, t.MIN_PRESSED, t.R_MIN, t.TIP_TOUCH, t.HOME_STEPS,
        "if DEPTH_MIN <= s <= DEPTH_MAX:" in SRC, "if s > DEPTH_MAX:" in SRC, "len(st[\"cur\"]) == 12" in SRC,
        "abs(dlt) <= math.pi / 2" in SRC, round(math.degrees(t.MOVE_MIN), 6), t.SECTORS,
        'veto = _S["stray"] is not None or _S["deep"] or _S["dropped"]  #' in SRC,
        "TIP_R + kk.PAD_OUT + TIP_TOUCH" in SRC, 'st["travel"] += dlt\n                        st["moving"] += abs(dlt) >= MOVE_MIN' in SRC,
        'min(1.0, st["moving"] / MIN_PRESSED) * min(1.0, len(st["sectors"]) / SECTORS)' in SRC,
        'p["moving_steps"] >= MIN_PRESSED' in SRC and 'p["sectors"] >= SECTORS' in SRC, t.TUBE_HOLD,
        'push >= PUSH_N and _tube_held(sp, kp, kR)' in SRC, "TUBE_OD / 2 + kk.PAD_OUT + TUBE_HOLD" in SRC,
        'continue\n                st["sectors"].add(_sector(ang))' in SRC, 'st["ang"] = st["prev"] = ang' in SRC,
        'abs(jump) <= math.pi / 2:\n                        st["travel"] += jump' in SRC,
        'st["cur"] = set()  # a jump across the nostril' in SRC) == (
        "end", 0.20, 0.05, 0.008, True, 0.008, 0.017, 4.0, 0.70, 2.0, 5, 0.0015, 0.015, True, True, True, True, True, True,
        5.0, 200, 0.25, 0.002, 180, True, True, True, True, 1.0, 10, True, True, True, True, True, 0.012, True, True, True,
        True, True, True), \
    "task.py thresholds changed: update the scoring text"
assert (t.SCENE, tuple(round(v, 3) for v in t.HEAD_POS[:2]), round(t.ALPHA, 4), t.A_SEMI, t.B_SEMI,
        t.NOSTRIL_DEPTH, {k: tuple(round(x, 4) for x in v) for k, v in t._O_HEAD.items()}, t.OVERALL,
        round(2 * t.TIP_R, 6), t.TIP_LEN, t.GRIP_L, t.GRIP_W, t.PLUG_W, t.SHAFT_W, t.SWAB_MASS, t.TUBE_X,
        round(t.TUBE_Z - t.TOP, 4), t.TUBE_OD, t.TUBE_ID, t.TUBE_L, t.Y_MOUTH, t.KIT.mass, t.HEAD.mass) == (
        "station", (0.37, -0.05), 0.5236, 0.007, 0.005, 0.026,
        {"left": (-0.04, -0.007, 0.156), "right": (-0.04, 0.007, 0.156)}, 0.15187, 0.004775, 0.016, 0.025, 0.013,
        0.010, 0.0026, 0.005, 0.2, 0.03, 0.014, 0.0112, 0.165, -0.13, 0.10, 1.5), \
    "task.py layout changed: update the setup text"
task = {
    "title": "Take an anterior nasal swab on a training head: whole tip in, 4 pressed circles per nostril, cap home",
    "category": "Impact on jobs",
    "keywords": ["bimanual", "healthcare", "specimen collection", "anterior nasal swab", "training manikin",
                 "circular rubbing", "contact force", "plug-style cap"],
    "instruction": t.INSTRUCTION,
    "context": (
        "CDC guidance for an anterior nasal (nares) specimen: insert the entire collection tip of the swab inside "
        "the nostril (usually 1 to 1.5 cm), firmly sample the nasal wall by rotating the swab in a circular path "
        "against it at least 4 times, about 15 seconds, then repeat in the other nostril with the same swab. "
        "Hologic's swab collection instructions warn that twirling the swab against one part of the inside of the "
        "nose is not proper technique. The swab goes back into its tube and the cap is pushed home while the other "
        "hand holds the tube. Done by: medical assistants (O*NET 31-9092.00, whose tasks include collecting "
        "laboratory specimens; 833,900 US jobs in 2025, BLS Occupational Outlook Handbook) and nurses, who also swab "
        "the anterior nares to screen for MRSA on hospital admission. Most medical assistants work in physicians' "
        "offices (BLS OEWS industry profile), where nasal swabs for flu, COVID-19 and RSV tests are routine; for "
        "send-out PCR the swab goes back into its dry transport tube."),
    "setup": (
        "Positions in cm from the midpoint between the two arm bases, on the table (x forward, y left); heights "
        "above the table. Nasal-swab practice head (printed PLA shell; simplified face, adult-size nose and "
        "nostrils), fixed to the table (1.5 kg in simulation; the printed shell is about 0.65 kg of PLA), lying face "
        "up with the crown away from the robot: 22 cm long (x 26 to 48), 15 cm wide (y -12.5 to 2.5), 17.1 cm high "
        "at the nose tip. The eyes, brows, lips and ears are non-colliding visual details and are not part of the "
        "printable mesh. Two nostrils open on the underside of the nose toward the chin, centred at x 33, y -5.7 "
        "(the patient's left, on the robot's right) and y -4.3, 15.6 cm above the table; each is an elliptical bore "
        "1.4 cm long and 1.0 cm wide, 2.6 cm deep, whose axis runs into the nose toward the crown, 30 degrees below "
        "horizontal. Swab (Puritan 25-1506 1PF BT BL style, blue cap; 5 g): white polystyrene shaft 0.26 cm thick, "
        "foam tip 0.48 cm across and 1.6 cm long, attached to the tube's blue cap (grip 1.3 cm across and 2.5 cm "
        "long, plug 1.0 cm across); 15.19 cm overall. Transport tube with its grey stand (one free 100 g piece): "
        "clear polypropylene tube 1.4 cm across outside and 1.12 cm inside (estimated), 16.5 cm long (Puritan's is "
        "15.4 cm; a spacer at the stand's end stop puts its mouth at the same place, see README), lying along y at x "
        "20 with its axis 3 cm above the table, its mouth at y -13 (toward the robot's right) and its closed end at "
        "y 3.5; the stand is a 5 cm wide plate under it (y -12.5 to 4.6) with two saddles and an end stop. The swab "
        "lies in the tube, tip first, with its plug-style cap in place as shipped: the plug in the mouth and the "
        "grip outside (centred at y -14.25). Real trials add: the head printed in three parts, its nose insert (both "
        "nostrils) hanging on two load cells inside it with a 1.6 mm gap all round; an LED taped beside the head (it "
        "flashes once when the force log starts); and a phone on an overhead holder, lens about 45 cm above the table "
        "over the face's centre line, 8 to 12 cm toward the chin from the nostrils, checked in the first run to be "
        "clear of the arms."),
    "scoring": (
        "Every step, from poses, finger-pad points and the PhysX contact points (with per-point normal forces) "
        "between the swab and the head and between the swab and the tube; the score at the end counts. For each "
        "nostril, the tip is at sampling depth when its centre is 0.8 to 1.7 cm in along the nostril's axis (the "
        "whole 1.6 cm tip inside, its end no deeper than 2.5 cm) and within the opening; a step there is pressed "
        "when the tip's contact force on that nostril's wall is at least 0.2 N (about 20 g). Circles: the larger "
        "of the signed angle the tip's centre travels round the "
        "nostril's axis over consecutive pressed steps (measured on the ellipse, 360 degrees = once round; a move of "
        "more than 90 degrees between steps does not count; when the tip is pressed again after a lift, the angle "
        "from the last pressed step counts too if it is 90 degrees or less, so an unpressed return cancels its "
        "stroke) and the laps, one each time all twelve 30-degree sectors of the wall have been pressed since the "
        "last lap, in either direction (sectors swept between consecutive pressed steps up to 90 degrees apart "
        "count; a jump of more than 90 degrees after a lift starts a new lap); steps with the tip's centre less than "
        "a quarter of the way from the axis to the wall are not used, for circles or sectors. Share: pressed steps "
        "over steps at sampling depth. Moving pressed steps: pressed steps in which the tip moved at least 1 degree "
        "round the wall. Sectors: the twelve 30-degree sectors of the wall pressed at least once. Nostril credit = "
        "min(circles, 4)/4 x min(1, share/0.7) x min(1, moving pressed steps/200) x min(1, sectors/10). Cap home: "
        "after the whole swab has been out of the tube, the cap seated on the mouth (grip within 1.5 mm of it, the "
        "swab within 6 degrees of the tube's axis and its cap within 3 mm of the axis) and pushed with at least 2 N "
        "on 5 consecutive steps (0.25 s) while a finger pad of the other hand is on the tube (within 1.2 cm of its "
        "outside; a free tube slides away, and the compliant simulated arm passes only 2 to 3.5 N through a pinched "
        "tube), then let go (no finger pad within 1.5 cm of the cap). Score: the mean of "
        "the two nostril credits, times 1.0 if the cap is home, else 0.4 (an unsealed specimen). 1.0: both nostrils "
        "with at least 4 circles, a share of at least 0.7 and at least 200 moving pressed steps (10 s) and at least "
        "10 sectors, and the cap home and let go; the run is a success (and ends) once the cap has stayed home 9 s. "
        "0 (voided swab): the foam tip touches anything other than the insides and rims of the nostrils (rims: up to "
        "0.8 cm outside the openings and within 1.6 times their half-widths) and the inside of the tube with at "
        "least 0.05 N (the face, the lips, the tube's or stand's outside, the table); a finger pad comes within 2 mm "
        "of the foam while the tip is outside the tube; the tip's end goes deeper than 2.5 cm; or the swab is "
        "dropped (its cap's centre lower than 1.2 cm while not held and not in the tube). A wall force above 5 N is "
        "reported, not scored. Real trial (README, real_trial/): the nose insert hangs on two load cells logging the net side force on the nose"
        " 80 times a second; real_trial/score_real_trial.py scores the log with these numbers, share included, and six "
        "stated rule differences (real_trial/README.md): a 0.05 s step is pressed at 0.2 N or more, the force's direction"
        " gives the tip's angle, and circles count as laps (all twelve sectors, or 10 over a full turn of pressed travel;"
        " a turn over 60 degrees starts a new lap) because rubbing friction tilts the force about 22 degrees. Anything "
        "but the foam touching the nose while a tip is at depth voids that nostril. An overhead video gives the at-depth "
        "times (the 1.6 cm line past the rim, the 2.5 cm line outside), the voids (green on the foam, a gripper on it, "
        "the tip on the table) and the cap (flush, pushed while the other hand holds the tube). Unusable logs are "
        "refused."),

    "run_limit": "2,400 steps (2 minutes at 20 Hz)",
    "reset_notes": (
        "Nothing is consumed in simulation. Put the swab back in its tube with the cap in place as shipped, and the "
        "stand back with the mouth toward the robot's right. Real trials: a new sterile swab per trial (single use); "
        "with the camera recording, start the force log with nothing touching the nose insert (it zeroes both load "
        "cells and flashes its LED for the video), stop it 2 s after the swab is out, and renew the green marker on the lip, skin, tube and "
        "stand (see README)."),
    "fidelity": (
        "Rigid bodies. The head is one fixed triangle-mesh shell; the face is simplified, while the nostrils have "
        "adult anterior-nares size and angle (each bore's floor opens toward the lip for its first ~1.3 cm). Foam "
        "tip and shaft are rigid (a real 2.5 mm polystyrene shaft bends, so a real press needs more cap travel); the "
        "press comes from the arm's compliance. Cap: seated and pushed >= 2 N for 0.25 s, other hand on the tube (no "
        "friction fit; the real cap needs its full push). Swab mass estimated."),
    "scores": scores,
}
assert len(task["scoring"]) <= 4000, len(task["scoring"])  # the submit bot refuses a longer scoring field
assert len(task["title"]) <= 120 and len(task["context"]) <= 1000 and len(task["fidelity"]) <= 500, \
    (len(task["title"]), len(task["context"]), len(task["fidelity"]))
try:  # keep the media ID that tools/upload_media.py wrote (the uploaded videos and screenshot still match)
    task["media"] = json.load(open("task.json"))["media"]
except (OSError, KeyError, ValueError):
    pass
json.dump(task, open("task.json", "w"), indent=2)
print("task.json written:", len(json.dumps(task)), "chars")
