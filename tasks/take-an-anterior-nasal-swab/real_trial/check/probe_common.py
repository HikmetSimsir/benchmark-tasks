import sys, os, math, importlib.util
import numpy as np
sys.path.insert(0, os.path.abspath("stub"))
sys.path.insert(0, os.path.abspath("../.."))
def load_task(path="../../task.py", name="nasal_task"):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m
def ray_mesh(o, d, V, F):
    """distance along unit d from o to first triangle hit (Moller-Trumbore, vectorised), inf if none"""
    v0, v1, v2 = V[F[:,0]], V[F[:,1]], V[F[:,2]]
    e1, e2 = v1 - v0, v2 - v0
    p = np.cross(d, e2); det = (e1 * p).sum(1)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    t0 = o - v0
    u = (t0 * p).sum(1) * inv
    q = np.cross(t0, e1)
    v = (q * d).sum(1) * inv   # d broadcast
    t = (e2 * q).sum(1) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-7)
    return t[hit].min() if hit.any() else np.inf
