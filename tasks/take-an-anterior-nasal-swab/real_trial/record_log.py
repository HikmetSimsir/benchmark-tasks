"""Save the force logger's serial stream to a CSV file for score_real_trial.py.

    pip install pyserial
    python record_log.py /dev/ttyUSB0 trial_01.csv      (Windows: COM3)   ... Ctrl-C to stop

Opening the port restarts the board, which zeroes both load cells: keep the nose insert untouched until the header
line appears (about 2 s). The log starts with the LED's 0.5 s flash; note that frame's time in the trial video. Each
line also gets pc_s, the PC's clock when the line arrived (seconds from the first sample), which score_real_trial.py
uses to correct the board's clock. Stop the log 2 s after the swab is out of the nose, with nothing touching it.
"""
import sys
import time

import serial  # pyserial

port, out = sys.argv[1], sys.argv[2]
n = 0
with serial.Serial(port, 115200, timeout=3) as s, open(out, "w") as fh:
    started, pc0 = False, None
    try:
        while True:
            line = s.readline().decode(errors="ignore").strip()
            now = time.monotonic()
            if not line:
                continue
            if line.startswith("#"):
                print(line)  # a warning from the board (e.g. not calibrated)
                continue
            if line.startswith("t_s,"):
                started = True
                fh.write(line + ",pc_s\n")
                print("zeroed; logging (Ctrl-C to stop)")
                continue
            if started and line.count(",") == 3:
                pc0 = now if pc0 is None else pc0
                fh.write(f"{line},{now - pc0:.4f}\n")
                n += 1
    except KeyboardInterrupt:
        pass
print(f"{n} samples -> {out}")
