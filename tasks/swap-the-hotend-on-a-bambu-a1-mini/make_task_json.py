"""Writes task.json from task.py's constants and the texts below (so instruction and numbers cannot drift)."""
import importlib.util
import json
import sys

scores = sys.argv[1] if len(sys.argv) > 1 else "Dream-1 run: pending; demo: 1.0"  # read before argv is cleared
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location("t", "task.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
SRC = open("task.py").read()  # for the few values written inline in task.py rather than as named constants


def cm(v):
    s = f"{100 * v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


assert (t.SEAT_TOL, t.SEAT_TILT, t.LOCK_DEG, t.SLOT_TOL, t.SLOT_TILT, t.RELEASE, t.HOLD_STEPS,
        "FallWatch(0.02, 10)" in SRC, "kk.near(arm, *_sink_box(name), 0.015)" in SRC,
        "abs(seat_err[2]) <= SEAT_TOL and float(np.linalg.norm(seat_err[:2])) <= SEAT_TOL + 0.001" in SRC,
        "abs(ps[2] - (STAND_H + SINK[2])) <= 0.003" in SRC, "StillWatch(0.0015, HOLD_STEPS)" in SRC,
        '0.2 * removed + 0.4 * seated + 0.3 * lock_ok + 0.1 * (_S["hold"] >= HOLD_STEPS)' in SRC,
        'veto = _S["dropped"]["hotend_new"]' in SRC, "BED_TOP + 0.004" in SRC, "tip_z < TOP + 0.004" in SRC,
        'done = (not veto) and removed and _S["hold"] >= HOLD_STEPS' in SRC) == (
        0.0015, 4.0, 3.0, 0.003, 8.0, 0.010, 20, True, True, True, True, True, True, True, True, True, True), \
    "task.py thresholds changed: update the scoring text"
assert (tuple(t.POCKET), t.SINK, t.NOZ_R, t.NOZ_H, t.TIP_R, t.TIP_H, t.HOTEND_MASS, t.BAR_LEN, t.STAND_H,
        t.SLOT_W, t.STAND_X, t.STAND_Y, (t.BOSS_X, t.BOSS_Y, t.BOSS_H), t.STAND.mass, t.PRINTER.mass, t.WIN_W, t.WIN_H,
        "limits=(0.0, 90.0)" in SRC, "stiffness=120.0" in SRC, tuple(round(v, 3) for v in t.TH - [0, 0, t.TOP]),
        tuple(round(v, 3) for v in t.STAND_POS[:2]), t.SLOT_Y, tuple(t.LUG["size"]), t.FRONT,
        tuple(round(v, 4) for v in t.HINGE), t.RET_Z) == (
        (0.015, 0.021, 0.012), (0.012, 0.018, 0.046), 0.0035, 0.010, 0.0015, 0.004, 0.022, 0.028, 0.100, 0.009,
        0.040, 0.160, (0.011, 0.018, 0.020), 0.2, 5.5, 0.014, 0.011, True, True, (0.375, 0.0, 0.2), (0.25, 0.03),
        {"new": -0.065, "empty": 0.065}, (0.007, 0.010, 0.004), -0.010, (-0.012, -0.012, 0.0), 0.008), \
    "task.py layout changed: update the setup text"

P0, TH = t.P0, t.TH
thz = TH[2] - t.TOP
hinge = TH + t.HINGE
sy = {k: t.STAND_POS[1] + y for k, y in t.SLOT_Y.items()}
hot_len = t.SINK[2] + t.NOZ_H + t.TIP_H

task = {
    "title": "Swap the hotend on a Bambu Lab A1 mini 3D printer: buckle open, old hotend to its holder, new one seated, locked",
    "category": "Impact on AI timelines",
    "keywords": ["3D printer maintenance", "hotend swap", "tool-free buckle", "overhead blind insertion", "fixed order",
                 "Bambu Lab A1 mini", "printed robot parts"],
    "instruction": t.INSTRUCTION,
    "context": (
        "Low-cost robot arms are built from printed parts: the SO-ARM100 printing guide (LeRobot) lists Bambu Lab "
        "A/P/X-series printers, and XLeRobot's parts were printed on a Bambu Lab A1. The printers that make those parts "
        "need hotend swaps to clear clogs, replace worn or damaged nozzles or change size (0.2 mm for fine detail, "
        "0.4 mm standard, hardened steel for abrasive filament), done by lab and makerspace staff and print-farm "
        "technicians. Bambu's procedure for the A1 series (wiki: Hotend Replacement for A1 Series; the A1 mini takes "
        "the same hotend): with the printer off and cool, the filament cut and the front cover and silicone sock off, "
        "push the nozzle buckle to unlock it and swing it open, hold the heatsink and pull the hotend out, put the new "
        "one in until it sits flush (a magnet aligns it) and close the buckle; if the buckle will not lock, the hotend "
        "is not seated. The hard part: seating a small part overhead, half hidden under the toolhead, between "
        "unlocking and locking."),
    "setup": (
        "Positions in cm from the midpoint between the two arm bases, on the table (x forward, y left); heights above "
        "the table. Bambu Lab A1 mini 3D printer, powered off and cold, front toward the robot; a loose 5.5 kg block "
        f"model: base 28 x 24 x 7 cm (x {cm(P0[0] - 0.14)} to {cm(P0[0] + 0.14)}, y -12 to 12) with an 18 x 18 cm bed "
        f"(top {cm(0.076)} cm up); Z column 6 x 5 x 31 cm at the right rear (x {cm(P0[0] + 0.05)} to "
        f"{cm(P0[0] + 0.11)}, y -17 to -12); X arm 3 x 25 x 3 cm behind the toolhead, {cm(thz + 0.05)} to "
        f"{cm(thz + 0.08)} cm up. Toolhead (front cover and silicone sock off, filament cut): 3.5 x 5.4 x 7.5 cm, x "
        f"{cm(TH[0] + t.FRONT)} to {cm(TH[0] + 0.025)}, y -2.7 to 2.7, underside {cm(thz)} cm up; in it a "
        f"{cm(t.POCKET[0])} x {cm(t.POCKET[1])} cm hotend pocket {cm(t.POCKET[2])} cm deep at x {cm(TH[0])}, y 0, "
        f"with a {cm(t.WIN_W)} cm wide, {cm(t.WIN_H)} cm high window in its front wall, and a sprung catch in its back "
        f"wall that presses the hotend forward with about 0.4 N (for the A1's magnet). Buckle: a {cm(t.BAR_LEN)} cm "
        f"metal bar on a vertical hinge at x {cm(hinge[0])}, y {cm(hinge[1])} (the window's right), "
        f"{cm(thz + t.BAR_Z[0])} to {cm(thz + t.BAR_Z[1])} cm up, with a 1.2 x 1 x 0.7 cm tab at its left end; "
        "closed it lies along the window under the hotend's lug; its left end swings out to the front, up to 90 "
        "degrees. Two Bambu Hotend - A1 Series hotends, each simplified to a "
        f"{cm(t.SINK[0])} x {cm(t.SINK[1])} x {cm(t.SINK[2])} cm heatsink with a 0.7 x 1 x 0.4 cm lug on its front "
        f"just below the top and a {cm(2 * t.NOZ_R)} cm nozzle, {cm(hot_len)} cm overall, 22 g: the old one (0.4 mm, "
        "dark band) seated in the pocket; the new one (0.2 mm, green tag) standing nozzle-down in the holder's right "
        "slot. Holder: printed PLA, 200 g, loose: a 4 x 16 x 8 cm block (x "
        f"{cm(t.STAND_POS[0] - t.STAND_X / 2)} to {cm(t.STAND_POS[0] + t.STAND_X / 2)}, y "
        f"{cm(t.STAND_POS[1] - t.STAND_Y / 2)} to {cm(t.STAND_POS[1] + t.STAND_Y / 2)}) with two 1.1 x 1.8 x 2 cm "
        f"bosses on top (tops {cm(t.STAND_H)} cm up), each with a 0.9 cm square hole: the right slot at y "
        f"{cm(sy['new'])} (new hotend), the left one at y {cm(sy['empty'])} (empty). Real trial: place the A1 mini so "
        f"the installed hotend's axis is at x {cm(TH[0])}, y 0, with the toolhead's underside {cm(thz)} cm up (set Z "
        "before powering off); stand the holder in front of the printer (against its front edge if the real base "
        f"reaches past x {cm(t.STAND_POS[0] + t.STAND_X / 2)}), slots at y {cm(sy['new'])} and {cm(sy['empty'])}."),
    "scoring": (
        "Score = 0.2 x old out + 0.4 x new seated + 0.3 x locked + 0.1 x finished; 0 if the new hotend is dropped. "
        "Old out: the old hotend stands in a holder slot (either; only the left one is free at the start; axis within "
        "0.3 cm of the slot's, heatsink on the boss within 0.3 cm, within 8 degrees of upright) and was not dropped on "
        "the way. Dropped: a hotend falls 2 cm within 0.5 s with no finger pad within 1.5 cm of its heatsink while not "
        "in the pocket or a slot, or its nozzle tip reaches the bed or the table. New seated: the new hotend's top "
        "within 0.15 cm of the pocket's top, its axis within 0.25 cm of the seat and within 4 degrees of vertical. "
        "Locked: the buckle within 3 degrees of its closed stop while the new hotend is seated (closed, its bar lies "
        "0.15 cm under a seated hotend's lug). The catch holds a hotend only once it is pushed fully home: one let go "
        "short of its seat slides out and falls. Finished: seated and locked, no finger pad within 1 cm of the new "
        "hotend's heatsink or the buckle's tab, and the new hotend still (under 0.15 cm of motion) for 20 steps (1 s); "
        "the run is a success, and ends, once that has held 1 s with the old hotend in a slot. Real trial, from photos "
        "and the video: old out = standing upright in either holder slot (end photo); locked = the buckle closed and "
        "latched in the end photo; finished = no part of either gripper touches the new hotend or the buckle in the "
        "last 1 s (video); seated = after the end photo, a strip of printer paper (about 0.1 mm) does not slide "
        "between the heatsink and the heating assembly, and the buckle locks over it (Bambu: it will not lock over an "
        "unseated hotend; if the robot left it open, the scorer closes it by hand without touching the hotend, which "
        "does not earn 'locked'); dropped = the new hotend falls or is set down on the bed, the table or the floor."),
    "run_limit": "2,400 steps (2 minutes at 20 Hz)",
    "reset_notes": (
        "Nothing is consumed. Put the old hotend back in the pocket and close and lock the buckle, stand the new "
        "hotend in the holder's right slot, and put the printer and the holder back on their tape marks. Real trials: "
        "the printer stays off and cool (below 50 C) with the front cover and silicone sock off and the filament cut; "
        "powered off, its toolhead slides along the X arm, so slide it back to its tape mark (hotend axis at y 0) "
        "before each trial; the two hotends may swap roles between trials."),
    "fidelity": (
        "Rigid bodies. The printer is a loose 5.5 kg block model with its toolhead fixed to it (the real carriage "
        "slides along X). The hotend is simplified: 6 cm long (real 4.73 cm), 1.2 x 1.8 cm heatsink, 22 g (est.). The "
        "A1's magnet, which pulls the hotend back flush against the heater, is a 1.2 cm deep pocket with a sprung "
        "catch (about 0.4 N) holding it by friction; the buckle is a hinged bar closing 0.15 cm under the hotend's "
        "lug. Not simulated: the buckle's push to unlock and its right-side lock."),
    "scores": scores,
}
assert len(task["title"]) <= 120 and len(task["context"]) <= 1000 and len(task["fidelity"]) <= 500 \
    and len(task["scores"]) <= 300 and len(task["run_limit"]) <= 200, \
    (len(task["title"]), len(task["context"]), len(task["fidelity"]), len(task["scores"]))
try:  # keep the board media ID written by tools/upload_media.py
    _media = json.load(open("task.json")).get("media")
except (OSError, ValueError):
    _media = None
if _media:
    task["media"] = _media
json.dump(task, open("task.json", "w"), indent=2, ensure_ascii=False)
open("task.json", "a").write("\n")
print("task.json written:", len(json.dumps(task)), "chars; title", len(task["title"]), "context", len(task["context"]),
      "fidelity", len(task["fidelity"]))
