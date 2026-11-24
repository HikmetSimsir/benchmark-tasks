// force_logger.ino: logs the force on the nasal-swab head's nose insert (take-an-anterior-nasal-swab, real trials).
// Two HX711 load-cell amplifiers set to 80 samples/s (RATE pin high: Adafruit's Rate switch at H, or SparkFun's RATE
// jumper cut), one per 1 kg bar load cell; an Arduino Nano or Uno; an LED (with a 220 ohm resistor) in the camera's view.
// Library: "HX711 Arduino Library" by Bogdan Necula (Arduino Library Manager).
//
// Output (115200 baud), one line per sample pair, about 80 a second: t_s,f_u_n,f_v_n,led
//   f_u_n: force on the insert along the nostrils' long axis, toward the nose tip (task.py's UX), newtons
//   f_v_n: force across the face, toward the robot's left (the patient's right; task.py's VX), newtons
// The board zeroes both cells when it starts (opening the serial port restarts it): keep the insert untouched for 2 s.
// The LED is on for the first 0.5 s only (t_s = 0 is the first video frame with it lit): it is the video's sync mark
// and gives the robot no feedback during the trial. Send 'r' to switch to raw counts (for calibration) and back.
#include <HX711.h>

// Calibration (real_trial/README.md): counts per newton, with the sign that makes +u and +v read positive.
const float COUNTS_PER_N_U = 1.0;  // tilted cell, along the nostrils' long axis
const float COUNTS_PER_N_V = 1.0;  // flat cell, across the face
const int PIN_U_DOUT = 2, PIN_U_SCK = 3, PIN_V_DOUT = 4, PIN_V_SCK = 5, PIN_LED = 6;

HX711 cellU, cellV;
long zeroU = 0, zeroV = 0;
unsigned long t0 = 0;
bool rawMode = false;

long averageRaw(HX711 &c, int n) {
  long s = 0;
  for (int i = 0; i < n; i++) {
    while (!c.is_ready()) {}
    s += c.read();
  }
  return s / n;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  cellU.begin(PIN_U_DOUT, PIN_U_SCK);
  cellV.begin(PIN_V_DOUT, PIN_V_SCK);
  delay(500);
  zeroU = averageRaw(cellU, 80);  // 1 s at 80 samples/s, nothing touching the insert
  zeroV = averageRaw(cellV, 80);
  if (COUNTS_PER_N_U == 1.0 || COUNTS_PER_N_V == 1.0) Serial.println("# not calibrated: enter COUNTS_PER_N_U and _V");
  Serial.println("t_s,f_u_n,f_v_n,led");
  t0 = micros();
}

void loop() {
  if (Serial.available() && Serial.read() == 'r') rawMode = !rawMode;
  if (!(cellU.is_ready() && cellV.is_ready())) return;
  long ru = cellU.read() - zeroU, rv = cellV.read() - zeroV;
  float t = (micros() - t0) * 1e-6;
  if (rawMode) {
    Serial.print(ru); Serial.print(','); Serial.println(rv);
    return;
  }
  float fu = ru / COUNTS_PER_N_U, fv = rv / COUNTS_PER_N_V;
  bool led = t < 0.5;  // the start flash only
  digitalWrite(PIN_LED, led ? HIGH : LOW);
  Serial.print(t, 4); Serial.print(',');
  Serial.print(fu, 4); Serial.print(',');
  Serial.print(fv, 4); Serial.print(',');
  Serial.println(led ? 1 : 0);
}
