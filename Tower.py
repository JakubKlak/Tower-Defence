"""
Tower class — gameplay logic + rich per-type visuals.

Each tower type has a unique silhouette drawn from pygame primitives:
  basic      — square platform, single barrel
  sniper     — tall narrow platform, long thin barrel
  rapid      — hexagonal platform, three short barrels
  artillery  — heavy platform, thick short cannon
  laser      — diamond platform, crystal emitter
  frost      — star platform, ice crystal array
"""

import pygame
import math
from Projectile import Projectile

TOWER_TYPES: dict[str, dict] = {
    "basic": {
        "range": 130, "fire_rate": 35, "damage": 8,
        "cost": 50,  "color": (220, 200, 50),  "p_speed": 7,  "effect": None,
    },
    "sniper": {
        "range": 260, "fire_rate": 120, "damage": 45,
        "cost": 150, "color": (60, 220, 220),  "p_speed": 18, "effect": None,
    },
    "rapid": {
        "range": 110, "fire_rate": 15,  "damage": 3,
        "cost": 100, "color": (210, 80, 220),  "p_speed": 10, "effect": None,
    },
    "artillery": {
        "range": 220, "fire_rate": 160, "damage": 110,
        "cost": 250, "color": (220, 130, 40),  "p_speed": 5,  "effect": None,
    },
    "laser": {
        "range": 160, "fire_rate": 2,   "damage": 0.3,
        "cost": 125, "color": (160, 60, 240),  "p_speed": 0,  "effect": None,
    },
    "frost": {
        "range": 130, "fire_rate": 50,  "damage": 4,
        "cost": 90,  "color": (100, 180, 255),  "p_speed": 8, "effect": "slow",
    },
}

_LEVEL_DAMAGE_MULT: float = 1.5
_LEVEL_RATE_MULT:   float = 0.8
_LEVEL_RANGE_BONUS: int   = 25
_MIN_FIRE_RATE:     int   = 1


# ── Helpers ────────────────────────────────────────────────────────────────

def _polygon(cx: int, cy: int, n: int, r: float, angle_offset: float = 0.0) -> list:
    """Return vertices of a regular n-gon centred at (cx, cy)."""
    pts = []
    for i in range(n):
        a = angle_offset + 2 * math.pi * i / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _draw_barrel(screen, cx, cy, angle, length, width, color, shadow=(20, 20, 20)):
    """Draw a filled barrel rectangle from centre toward angle."""
    ca, sa = math.cos(angle), math.sin(angle)
    px, py = -sa * width / 2, ca * width / 2
    tip_x  = cx + ca * length
    tip_y  = cy + sa * length
    pts = [
        (cx + px,       cy + py),
        (cx - px,       cy - py),
        (tip_x - px,    tip_y - py),
        (tip_x + px,    tip_y + py),
    ]
    # shadow offset
    shadow_pts = [(x + 2, y + 2) for x, y in pts]
    pygame.draw.polygon(screen, shadow, shadow_pts)
    pygame.draw.polygon(screen, color, pts)


# ── Tower class ───────────────────────────────────────────────────────────

class Tower:
    """A placeable defensive tower with per-type artwork."""

    def __init__(self, x: float, y: float, tower_type: str = "basic"):
        if tower_type not in TOWER_TYPES:
            raise ValueError(f"Unknown tower type: '{tower_type}'")

        stats = TOWER_TYPES[tower_type]
        self.x = x
        self.y = y
        self.type = tower_type
        self.range:     float        = stats["range"]
        self.fire_rate: int          = stats["fire_rate"]
        self.damage:    float        = stats["damage"]
        self.color:     tuple        = stats["color"]
        self.p_speed:   float        = stats["p_speed"]
        self.effect:    str | None   = stats["effect"]

        self.level:    int        = 1
        self.branch:   str | None = None
        self.cooldown: int        = 0
        self.target               = None
        self.selected: bool       = False
        self._angle:   float      = -math.pi / 2   # barrel faces up by default

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upgrade(self, branch: str | None = None) -> bool:
        if self.level < 3:
            self.level    += 1
            self.damage   *= _LEVEL_DAMAGE_MULT
            self.range    += _LEVEL_RANGE_BONUS
            self.fire_rate = max(_MIN_FIRE_RATE, int(self.fire_rate * _LEVEL_RATE_MULT))
            return True
        if self.level == 3 and branch in ("A", "B", "C"):
            self.level  = 4
            self.branch = branch
            self._apply_branch_upgrade(branch)
            return True
        return False

    def find_target(self, enemies: list) -> None:
        self.target = None
        best = -1.0
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            cx, cy = enemy.center
            if math.hypot(cx - self.x, cy - self.y) <= self.range:
                if enemy.exact_progress > best:
                    best = enemy.exact_progress
                    self.target = enemy
        # Track barrel toward target
        if self.target:
            tx, ty = self.target.center
            self._angle = math.atan2(ty - self.y, tx - self.x)

    def attack(self, projectiles: list) -> None:
        if self.cooldown > 0:
            self.cooldown -= 1
            return
        if self.target is None or not self.target.is_alive:
            return
        if self.type == "laser":
            self.target.take_damage(self.damage)
        else:
            projectiles.append(
                Projectile(self.x, self.y, self.target, self.damage,
                           self.p_speed, self.color, self.effect)
            )
        self.cooldown = self.fire_rate

    def draw(self, screen: pygame.Surface) -> None:
        ix, iy = int(self.x), int(self.y)
        if self.selected:
            self._draw_range_circle(screen, ix, iy)
            # Selection ring
            pygame.draw.circle(screen, (0, 255, 150), (ix, iy), 22, 2)
        # Dispatch per-type art
        draw_fn = {
            "basic":     self._draw_basic,
            "sniper":    self._draw_sniper,
            "rapid":     self._draw_rapid,
            "artillery": self._draw_artillery,
            "laser":     self._draw_laser,
            "frost":     self._draw_frost,
        }.get(self.type, self._draw_basic)
        draw_fn(screen, ix, iy)
        self._draw_level_gems(screen, ix, iy)
        # Laser beam
        if self.type == "laser" and self.target and self.target.is_alive:
            tx, ty = self.target.center
            for w, a in [(4, 60), (2, 120), (1, 200)]:
                col = (*self.color[:2], min(255, self.color[2]))
                pygame.draw.line(screen, (*self.color, a), (ix, iy), (tx, ty), w)
            pygame.draw.circle(screen, (255, 255, 255), (tx, ty), 4)

    # ------------------------------------------------------------------
    # Per-type draw methods
    # ------------------------------------------------------------------

    def _draw_basic(self, screen, cx, cy):
        r, g, b = self.color
        dark = (r // 3, g // 3, b // 3)
        # Shadow
        pygame.draw.circle(screen, (15, 15, 15), (cx + 3, cy + 3), 16)
        # Base: square rotated 45° (diamond)
        base_pts = _polygon(cx, cy, 4, 16, math.pi / 4)
        pygame.draw.polygon(screen, dark, base_pts)
        base_pts2 = _polygon(cx, cy, 4, 13, math.pi / 4)
        pygame.draw.polygon(screen, self.color, base_pts2)
        # Barrel
        _draw_barrel(screen, cx, cy, self._angle, 16, 6, (r, g, b), (20, 20, 20))
        # Centre dot
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 4)
        pygame.draw.circle(screen, dark, (cx, cy), 2)

    def _draw_sniper(self, screen, cx, cy):
        r, g, b = self.color
        dark = (r // 3, g // 3, b // 3)
        # Shadow
        pygame.draw.circle(screen, (15, 15, 15), (cx + 3, cy + 3), 15)
        # Octagonal base
        base_pts = _polygon(cx, cy, 8, 16, 0)
        pygame.draw.polygon(screen, dark, base_pts)
        base_pts2 = _polygon(cx, cy, 8, 13, 0)
        pygame.draw.polygon(screen, self.color, base_pts2)
        # Long thin barrel
        _draw_barrel(screen, cx, cy, self._angle, 22, 4, (r, g, b), (20, 20, 20))
        # Scope ring at tip
        tip_x = int(cx + math.cos(self._angle) * 20)
        tip_y = int(cy + math.sin(self._angle) * 20)
        pygame.draw.circle(screen, (200, 255, 255), (tip_x, tip_y), 4, 1)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 3)

    def _draw_rapid(self, screen, cx, cy):
        r, g, b = self.color
        dark = (r // 3, g // 3, b // 3)
        pygame.draw.circle(screen, (15, 15, 15), (cx + 3, cy + 3), 15)
        # Hexagonal base
        base_pts = _polygon(cx, cy, 6, 16, 0)
        pygame.draw.polygon(screen, dark, base_pts)
        base_pts2 = _polygon(cx, cy, 6, 13, 0)
        pygame.draw.polygon(screen, self.color, base_pts2)
        # Three barrels splayed ±20°
        for offset in (-0.35, 0, 0.35):
            a = self._angle + offset
            _draw_barrel(screen, cx, cy, a, 14, 3, (r, g, b), (20, 20, 20))
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 4)
        pygame.draw.circle(screen, dark, (cx, cy), 2)

    def _draw_artillery(self, screen, cx, cy):
        r, g, b = self.color
        dark = (r // 3, g // 3, b // 3)
        pygame.draw.circle(screen, (15, 15, 15), (cx + 3, cy + 3), 18)
        # Heavy square base
        pygame.draw.rect(screen, dark,        (cx - 16, cy - 16, 32, 32))
        pygame.draw.rect(screen, self.color,  (cx - 13, cy - 13, 26, 26))
        # Corner bolts
        for bx, by in [(-11, -11), (11, -11), (-11, 11), (11, 11)]:
            pygame.draw.circle(screen, dark, (cx + bx, cy + by), 3)
        # Thick short cannon
        _draw_barrel(screen, cx, cy, self._angle, 14, 10, (r // 2 + 40, g // 2 + 20, b // 2), (20, 20, 20))
        # Muzzle ring
        tip_x = int(cx + math.cos(self._angle) * 14)
        tip_y = int(cy + math.sin(self._angle) * 14)
        pygame.draw.circle(screen, (255, 200, 80), (tip_x, tip_y), 5)
        pygame.draw.circle(screen, dark, (tip_x, tip_y), 3)

    def _draw_laser(self, screen, cx, cy):
        r, g, b = self.color
        dark = (r // 4, g // 4, b // 4)
        pygame.draw.circle(screen, (15, 15, 15), (cx + 3, cy + 3), 16)
        # Diamond base rotated
        base_pts = _polygon(cx, cy, 4, 17, 0)
        pygame.draw.polygon(screen, dark, base_pts)
        base_pts2 = _polygon(cx, cy, 4, 14, 0)
        pygame.draw.polygon(screen, self.color, base_pts2)
        # Inner glow crystal
        inner = _polygon(cx, cy, 4, 8, math.pi / 4)
        pygame.draw.polygon(screen, (min(255, r + 60), min(255, g + 40), 255), inner)
        # Pulse ring (always animated)
        pulse_r = 6 + int(4 * abs(math.sin(pygame.time.get_ticks() * 0.005)))
        pygame.draw.circle(screen, (200, 150, 255), (cx, cy), pulse_r, 1)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 3)

    def _draw_frost(self, screen, cx, cy):
        r, g, b = self.color
        dark = (r // 3, g // 3, b // 4)
        pygame.draw.circle(screen, (15, 15, 15), (cx + 3, cy + 3), 16)
        # Circular base
        pygame.draw.circle(screen, dark, (cx, cy), 16)
        pygame.draw.circle(screen, self.color, (cx, cy), 13)
        # 6 ice spikes
        for i in range(6):
            a = i * math.pi / 3
            x1 = int(cx + math.cos(a) * 6)
            y1 = int(cy + math.sin(a) * 6)
            x2 = int(cx + math.cos(a) * 16)
            y2 = int(cy + math.sin(a) * 16)
            pygame.draw.line(screen, (200, 240, 255), (x1, y1), (x2, y2), 2)
            pygame.draw.circle(screen, (255, 255, 255), (x2, y2), 2)
        # Centre crystal
        inner = _polygon(cx, cy, 6, 6, 0)
        pygame.draw.polygon(screen, (220, 240, 255), inner)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 3)

    # ------------------------------------------------------------------
    # Shared drawing helpers
    # ------------------------------------------------------------------

    def _draw_level_gems(self, screen, cx, cy):
        """Small coloured dots below the tower showing its upgrade level."""
        if self.level <= 1:
            return
        gem_colors = {
            2: (100, 255, 180),
            3: (255, 215, 0),
            4: (255, 80, 80),
        }
        gc = gem_colors.get(min(self.level, 4), (255, 255, 255))
        n = min(self.level, 4)
        spacing = 7
        start_x = cx - (n - 1) * spacing // 2
        for i in range(n):
            gx = start_x + i * spacing
            gy = cy + 20
            pygame.draw.circle(screen, (20, 20, 20), (gx + 1, gy + 1), 3)
            pygame.draw.circle(screen, gc, (gx, gy), 3)

    def _draw_range_circle(self, screen, cx, cy):
        r = int(self.range)
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA).convert_alpha()
        pygame.draw.circle(surf, (*self.color, 25), (r, r), r)
        pygame.draw.circle(surf, (*self.color, 80), (r, r), r, 1)
        screen.blit(surf, (cx - r, cy - r))

    def _apply_branch_upgrade(self, branch: str) -> None:
        rv, gv, bv = self.color
        if branch == "A":
            self.damage *= 3.0
            self.color = (min(255, rv + 60), 40, 40)
        elif branch == "B":
            self.fire_rate = max(_MIN_FIRE_RATE, int(self.fire_rate * 0.4))
            self.color = (40, min(255, gv + 60), 255)
        elif branch == "C":
            self.range += 120
            self.color = (240, 240, 255)