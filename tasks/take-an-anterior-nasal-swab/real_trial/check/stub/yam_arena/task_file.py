from dataclasses import dataclass
TABLE_TOP = {"station": 0.7475}
@dataclass(frozen=True)
class Box:
    name: str
    pos: tuple
    size: tuple = (0.05, 0.05, 0.05)
    color: tuple = (0.7, 0.7, 0.7)
    mass: object = None
    yaw: float = 0.0
    def _check(self):
        pass
