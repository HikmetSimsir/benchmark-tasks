import os, sys, math
sys.path.append(os.getcwd())
from probe_common import load_task
import numpy as np

def quat_from_R(R):
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2; w = 0.25 * s
        x = (R[2,1]-R[1,2])/s; y = (R[0,2]-R[2,0])/s; z = (R[1,0]-R[0,1])/s
    else:
        i = int(np.argmax(np.diag(R)))
        if i == 0:
            s = math.sqrt(1 + R[0,0]-R[1,1]-R[2,2])*2; x = 0.25*s; w=(R[2,1]-R[1,2])/s; y=(R[0,1]+R[1,0])/s; z=(R[0,2]+R[2,0])/s
        elif i == 1:
            s = math.sqrt(1 + R[1,1]-R[0,0]-R[2,2])*2; y = 0.25*s; w=(R[0,2]-R[2,0])/s; x=(R[0,1]+R[1,0])/s; z=(R[1,2]+R[2,1])/s
        else:
            s = math.sqrt(1 + R[2,2]-R[0,0]-R[1,1])*2; z = 0.25*s; w=(R[1,0]-R[0,1])/s; x=(R[0,2]+R[2,0])/s; y=(R[1,2]+R[2,1])/s
    return np.array([x,y,z,w])

def frame_from_axis(ax):
    ax = np.asarray(ax, float); ax = ax/np.linalg.norm(ax)
    up = np.array([0,0,1.0]) if abs(ax[2]) < 0.9 else np.array([1.0,0,0])
    y = np.cross(up, ax); y /= np.linalg.norm(y); z = np.cross(ax, y)
    return np.column_stack([ax, y, z])

FAR = np.full((24,3), 5.0)

class Sim:
    def __init__(self, path="../../task.py"):
        self.m = load_task(path, name=f"t{np.random.randint(1e9)}")
        self.kk = self.m.kk
        self.kk.STATE.clear()
        for cb in self.kk.RESET_CALLBACKS: cb()
        self.m._reset()
        self.step_i = -1
        self.kit_pos = self.m.KIT_POS.copy()
    def step(self, sp, R, head_pts=(), kit_pts=(), push=0.0, fingers_right=None, fingers_left=None):
        m, kk = self.m, self.kk
        self.step_i += 1
        kk.STATE.step = self.step_i
        I = np.array([0,0,0,1.0])
        kk.STATE.poses = {"head": (m.HEAD_POS.copy(), I), "kit": (self.kit_pos.copy(), I), "swab": (np.asarray(sp,float), quat_from_R(R))}
        hp = np.array([p for p,_ in head_pts]).reshape(-1,3); hf = np.array([f for _,f in head_pts], float)
        kp = np.array([p for p,_ in kit_pts]).reshape(-1,3); kf = np.array([f for _,f in kit_pts], float)
        kk.STATE.points = {("swab","head"): (hp, hf), ("swab","kit"): (kp, kf)}
        kk.STATE.contacts = {("swab","kit"): float(push), ("swab","head"): float(hf.sum()) if len(hf) else 0.0}
        kk.STATE.fingers = {"left_robot": FAR if fingers_left is None else fingers_left,
                            "right_robot": FAR if fingers_right is None else fingers_right}
        return m._update(None)
    # helpers -----------------------------------------------------------
    def tip_pose(self, k, depth, uv=(0.0,0.0), ax=None):
        """swab origin and R with the tip centre at depth (m) along nostril k's axis, offset uv (m) in (UX, VX)."""
        m = self.m
        O = m.NOSTRILS[k]
        tip = O + depth*m.AX + uv[0]*m.UX + uv[1]*m.VX
        ax = m.AX if ax is None else np.asarray(ax,float)/np.linalg.norm(ax)
        R = frame_from_axis(ax)
        sp = tip - m.TIP_X*R[:,0]
        return sp, R, tip
    def holding(self, sp):
        return np.tile(np.asarray(sp,float), (24,1)) + 0.005  # finger pads within 15 mm of the cap
    def out_of_tube(self, n=5):
        m = self.m
        for i in range(n):
            R = frame_from_axis([0,1.0,0]) if False else None
        # swab lifted above the tube, axis along +y, fully out
        R = frame_from_axis(np.array([0.0,1.0,0.0]))
        sp = np.array([m.TUBE_X, m.Y_MOUTH - 0.20, m.TUBE_Z + 0.10])
        for i in range(n):
            self.step(sp, R, fingers_right=self.holding(sp))
        return sp, R
    def press_at(self, k, depth, ang, rad_frac, f, extra_pts=()):
        """tip centre at elliptical angle ang (rad), elliptical radius rad_frac (1 = wall), pressing force f on the wall."""
        m = self.m
        u, v = rad_frac*m.A_SEMI*math.cos(ang), rad_frac*m.B_SEMI*math.sin(ang)
        sp, R, tip = self.tip_pose(k, depth, (u, v))
        n = math.cos(ang)*m.UX/m.A_SEMI + math.sin(ang)*m.VX/m.B_SEMI  # outward normal of the ellipse (approx)
        n = n/np.linalg.norm(n)
        pts = [(tip + m.TIP_R*n, f)] if f > 0 else []
        pts += list(extra_pts)
        return self.step(sp, R, head_pts=pts, fingers_right=self.holding(sp))
    def cap_home(self, push=3.0, push_steps=10, release_steps=70, held_tube=True):
        m = self.m
        R = frame_from_axis(np.array([0.0,1.0,0.0]))
        sp = np.array([m.TUBE_X, m.Y_MOUTH - m.GRIP_L/2 + 0.0002, m.TUBE_Z])  # gap 0.2 mm
        last=None
        for i in range(push_steps):
            last = self.step(sp, R, push=push, fingers_right=self.holding(sp))
        for i in range(release_steps):
            last = self.step(sp, R, push=0.05)
        return last
    def report(self):
        return self.m.report()

def summary(sim, res):
    r = sim.report()
    n = r['nostrils']
    return (f"score={res[0]} success={res[1]} | L circles {n['left']['circles']} share {n['left']['share']} pressed {n['left']['contact_steps']} sectors {n['left']['sectors']} credit {n['left']['credit']}"
            f" | R circles {n['right']['circles']} share {n['right']['share']} pressed {n['right']['contact_steps']} sectors {n['right']['sectors']} credit {n['right']['credit']}"
            f" | stray={r['tip_touched']} hard={r['too_hard']} deep={r['too_deep']} latched={r['cap_latched']} home_steps={r['cap_home_steps']}")
