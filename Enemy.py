"""
Enemy class — movement, abilities, and per-type artwork.

Each enemy type has a distinct silhouette drawn from pygame primitives.
All art is drawn within the tile_size × tile_size bounding box.
"""

import pygame
import math
from Enemies_Types import ENEMY_TYPES, VALID_ENEMY_TYPES

SLOW_DURATION:   int   = 90
SLOW_MULTIPLIER: float = 0.5
_BERSERK_TINT         = (255, 60, 0)


# ── Drawing helpers ────────────────────────────────────────────────────────

def _poly(cx, cy, n, r, offset=0.0):
    pts = []
    for i in range(n):
        a = offset + 2 * math.pi * i / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


class Enemy:
    """A single enemy that follows a tile-based path and may have a special ability."""

    def __init__(self, path: list[tuple[int, int]], tile_size: int, enemy_type: str = "basic"):
        if enemy_type not in VALID_ENEMY_TYPES:
            raise ValueError(f"Unknown enemy type: '{enemy_type}'")

        stats = ENEMY_TYPES[enemy_type]
        self.type      = enemy_type
        self.max_hp:   int   = stats["hp"]
        self.hp:       float = float(stats["hp"])
        self.speed:    float = stats["speed"]
        self.reward:   int   = stats["reward"]
        self.color:    tuple = stats["color"]
        self.damage:   int   = stats.get("damage", 1)

        self.path      = path
        self.tile_size = tile_size
        self.pos_index:       int   = 0
        self.x:               float = float(path[0][0] * tile_size)
        self.y:               float = float(path[0][1] * tile_size)
        self.slow_timer:      int   = 0
        self.exact_progress:  float = 0.0

        ability = stats.get("ability")
        self.ability:          str | None = ability
        self.ability_timer:    int        = 0
        self.ability_cooldown: int        = stats.get("ability_cooldown", 0)

        self.heal_amount:    int   = stats.get("heal_amount", 0)
        self.heal_radius:    float = stats.get("heal_radius", 0.0)
        self.heal_flash_timer: int = 0

        self.immune_timer:    int = 0
        self.immune_duration: int = stats.get("immune_duration", 0)

        self.berserk_speed_mult: float = stats.get("berserk_speed_mult", 1.0)
        self.is_berserk:         bool  = False

        self.will_split:  bool = ability == "split"
        self.split_type:  str  = stats.get("split_type", "basic")
        self.split_count: int  = stats.get("split_count", 0)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    @property
    def has_reached_end(self) -> bool:
        return self.pos_index + 1 >= len(self.path)

    @property
    def is_immune(self) -> bool:
        return self.immune_timer > 0

    @property
    def center(self) -> tuple[int, int]:
        half = self.tile_size // 2
        return (int(self.x) + half, int(self.y) + half)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_slow(self) -> None:
        self.slow_timer = SLOW_DURATION

    def take_damage(self, amount: float) -> float:
        if self.is_immune:
            return 0.0
        self.hp -= amount
        return amount

    def move(self) -> None:
        if self.has_reached_end:
            return
        current_speed = self.speed * SLOW_MULTIPLIER if self.slow_timer > 0 else self.speed
        if self.slow_timer > 0:
            self.slow_timer -= 1
        target_col, target_row = self.path[self.pos_index + 1]
        target_x = float(target_col * self.tile_size)
        target_y = float(target_row * self.tile_size)
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        if dist <= current_speed:
            self.x, self.y = target_x, target_y
            self.pos_index += 1
        else:
            self.x += (dx / dist) * current_speed
            self.y += (dy / dist) * current_speed
        if dist > 0:
            self.exact_progress = self.pos_index + (1.0 - dist / self.tile_size)
        else:
            self.exact_progress = float(self.pos_index)

    def tick_ability(self, all_enemies: list) -> None:
        if self.ability is None:
            return
        if self.ability == "heal":
            self._tick_heal(all_enemies)
        elif self.ability == "ghost":
            self._tick_ghost()
        elif self.ability == "berserk":
            self._tick_berserk()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        cx, cy = self.center
        ts = self.tile_size
        r  = ts // 2 - 3   # inner drawing radius

        # Healer aura pulse (behind body)
        if self.heal_flash_timer > 0:
            self.heal_flash_timer -= 1
            alpha = int(160 * self.heal_flash_timer / 20)
            aura_r = int(self.heal_radius)
            aura = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura, (0, 255, 140, min(alpha, 70)), (aura_r, aura_r), aura_r)
            screen.blit(aura, (cx - aura_r, cy - aura_r))

        # Per-type body
        draw_fn = {
            "basic":       self._draw_basic,
            "fast":        self._draw_fast,
            "scout":       self._draw_scout,
            "tank":        self._draw_tank,
            "heavy":       self._draw_heavy,
            "glass_cannon":self._draw_glass_cannon,
            "boss":        self._draw_boss,
            "healer":      self._draw_healer,
            "ghost":       self._draw_ghost,
            "berserker":   self._draw_berserker,
            "splitter":    self._draw_splitter,
        }.get(self.type, self._draw_basic)

        if self.is_immune:
            # Draw ghost-translucent version
            tmp = pygame.Surface((ts, ts), pygame.SRCALPHA)
            draw_fn(tmp, ts // 2, ts // 2, r)
            tmp.set_alpha(90)
            screen.blit(tmp, (int(self.x), int(self.y)))
        else:
            draw_fn(screen, cx, cy, r)

        # Slow ice overlay
        if self.slow_timer > 0:
            ix, iy = int(self.x), int(self.y)
            ice = pygame.Surface((ts, ts), pygame.SRCALPHA)
            ice.fill((100, 200, 255, 50))
            pygame.draw.rect(ice, (100, 200, 255, 180), (0, 0, ts, ts), 2)
            screen.blit(ice, (ix, iy))

        # Berserk ring
        if self.is_berserk:
            pygame.draw.circle(screen, _BERSERK_TINT, (cx, cy), r + 4, 2)

        self._draw_hp_bar(screen, int(self.x), int(self.y), ts)

    # ------------------------------------------------------------------
    # Per-type body draw methods (cx, cy = pixel centre, r = radius)
    # ------------------------------------------------------------------

    def _draw_basic(self, s, cx, cy, r):
        """Red diamond soldier with a dark visor."""
        c = self.color
        dark = (max(0, c[0]-60), max(0, c[1]-60), max(0, c[2]-60))
        # Shadow
        pygame.draw.polygon(s, (10,10,10), _poly(cx+2, cy+2, 4, r, 0))
        # Body diamond
        pygame.draw.polygon(s, dark,  _poly(cx, cy, 4, r, 0))
        pygame.draw.polygon(s, c,     _poly(cx, cy, 4, r-3, 0))
        # Visor
        pygame.draw.polygon(s, (20, 20, 20), _poly(cx, cy - r//3, 4, r//3, math.pi/4))

    def _draw_fast(self, s, cx, cy, r):
        """Green elongated oval — lean and aerodynamic."""
        c = self.color
        dark = (max(0, c[0]-60), max(0, c[1]-60), max(0, c[2]-60))
        pygame.draw.ellipse(s, (10,10,10), (cx - r//2 + 2, cy - r + 2, r, r*2))
        pygame.draw.ellipse(s, dark,  (cx - r//2,     cy - r,     r,   r*2))
        pygame.draw.ellipse(s, c,     (cx - r//2 + 2, cy - r + 3, r-4, r*2-6))
        # Speed lines
        for i in range(3):
            lx = cx - r//2 - 4 - i*4
            pygame.draw.line(s, (180, 255, 180), (lx, cy - 3 + i*3), (lx - 5, cy - 3 + i*3), 1)

    def _draw_scout(self, s, cx, cy, r):
        """Light green nimble circle with two small legs."""
        c = self.color
        dark = (max(0, c[0]-60), max(0, c[1]-60), max(0, c[2]-60))
        # Legs
        pygame.draw.line(s, dark, (cx - 5, cy + r - 3), (cx - 8, cy + r + 5), 2)
        pygame.draw.line(s, dark, (cx + 5, cy + r - 3), (cx + 8, cy + r + 5), 2)
        # Body
        pygame.draw.circle(s, (10,10,10), (cx+2, cy+2), r-1)
        pygame.draw.circle(s, dark, (cx, cy), r-1)
        pygame.draw.circle(s, c,    (cx, cy), r-4)
        # Eye
        pygame.draw.circle(s, (20,20,20), (cx, cy - 3), 3)
        pygame.draw.circle(s, (255,255,255), (cx-1, cy-4), 1)

    def _draw_tank(self, s, cx, cy, r):
        """Blue armoured box with thick riveted border."""
        c = self.color
        dark = (max(0, c[0]-60), max(0, c[1]-60), max(0, c[2]-60))
        hw = r - 1
        # Shadow
        pygame.draw.rect(s, (10,10,10), (cx - hw + 3, cy - hw + 3, hw*2, hw*2))
        # Armour plate
        pygame.draw.rect(s, dark, (cx - hw,     cy - hw,     hw*2, hw*2))
        pygame.draw.rect(s, c,    (cx - hw + 3, cy - hw + 3, hw*2-6, hw*2-6))
        # Rivets
        for bx, by in [(-hw+2, -hw+2), (hw-2, -hw+2), (-hw+2, hw-2), (hw-2, hw-2)]:
            pygame.draw.circle(s, dark, (cx+bx, cy+by), 2)
        # Viewport slit
        pygame.draw.rect(s, (20,20,20), (cx - hw//2, cy - 3, hw, 5))

    def _draw_heavy(self, s, cx, cy, r):
        """Massive grey rectangle that nearly fills the tile."""
        c = self.color
        dark = (max(0, c[0]-50), max(0, c[1]-50), max(0, c[2]-50))
        hw = r + 1
        pygame.draw.rect(s, (10,10,10), (cx - hw + 3, cy - hw + 3, hw*2, hw*2))
        pygame.draw.rect(s, dark, (cx - hw,   cy - hw,   hw*2,   hw*2))
        pygame.draw.rect(s, c,    (cx - hw+2, cy - hw+2, hw*2-4, hw*2-4))
        # Armour stripes
        for i in range(3):
            stripe_y = cy - hw + 6 + i * (hw*2 - 8) // 2
            pygame.draw.line(s, dark, (cx - hw+3, stripe_y), (cx + hw-3, stripe_y), 2)
        # Thick border
        pygame.draw.rect(s, dark, (cx - hw, cy - hw, hw*2, hw*2), 3)

    def _draw_glass_cannon(self, s, cx, cy, r):
        """Thin white vertical shard — fragile but dangerous."""
        c = self.color
        # Thin tall shard
        shard_pts = [
            (cx,      cy - r),
            (cx + 5,  cy - r//2),
            (cx + 4,  cy + r),
            (cx - 4,  cy + r),
            (cx - 5,  cy - r//2),
        ]
        pygame.draw.polygon(s, (180,180,180), [(x+2,y+2) for x,y in shard_pts])
        pygame.draw.polygon(s, (160,160,160), shard_pts)
        pygame.draw.polygon(s, c, [(cx,cy-r), (cx+3,cy-r//3), (cx+3,cy+r-4), (cx-3,cy+r-4), (cx-3,cy-r//3)])
        # Glint
        pygame.draw.line(s, (255,255,255), (cx-1, cy-r+2), (cx-1, cy-r//2), 1)

    def _draw_boss(self, s, cx, cy, r):
        """Large orange shape with a 5-pointed crown."""
        c = self.color
        dark = (max(0, c[0]-80), max(0, c[1]-40), 0)
        # Shadow
        pygame.draw.circle(s, (10,10,10), (cx+3, cy+3), r+1)
        # Main body
        pygame.draw.circle(s, dark, (cx, cy), r+1)
        pygame.draw.circle(s, c,    (cx, cy), r-1)
        # Crown spikes
        for i in range(5):
            a = -math.pi/2 + 2*math.pi*i/5
            sx1 = int(cx + math.cos(a) * (r-2))
            sy1 = int(cy + math.sin(a) * (r-2))
            sx2 = int(cx + math.cos(a) * (r+6))
            sy2 = int(cy + math.sin(a) * (r+6))
            pygame.draw.line(s, (255, 215, 0), (sx1, sy1), (sx2, sy2), 3)
            pygame.draw.circle(s, (255, 240, 100), (sx2, sy2), 3)
        # Face
        pygame.draw.circle(s, (255,200,100), (cx, cy), r-5)
        pygame.draw.circle(s, dark, (cx-5, cy-3), 3)
        pygame.draw.circle(s, dark, (cx+5, cy-3), 3)
        pygame.draw.arc(s, dark, (cx-5, cy, 10, 7), math.pi, 2*math.pi, 2)

    def _draw_healer(self, s, cx, cy, r):
        """Green cross/plus medical shape."""
        c = self.color
        dark = (0, max(0, c[1]-80), max(0, c[2]-40))
        arm = r - 2
        t   = 5        # arm thickness half-width
        cross_pts = [
            (cx-t, cy-arm), (cx+t, cy-arm),
            (cx+t, cy-t),   (cx+arm, cy-t),
            (cx+arm, cy+t), (cx+t, cy+t),
            (cx+t, cy+arm), (cx-t, cy+arm),
            (cx-t, cy+t),   (cx-arm, cy+t),
            (cx-arm, cy-t), (cx-t, cy-t),
        ]
        pygame.draw.polygon(s, dark,  [(x+2,y+2) for x,y in cross_pts])
        pygame.draw.polygon(s, dark,  cross_pts)
        pygame.draw.polygon(s, c,     [(x,y) for x,y in cross_pts])
        # White shine
        pygame.draw.rect(s, (200,255,220), (cx-t+2, cy-arm+2, (t-2)*2, arm-t-2))
        # Pulse ring when healing
        if self.heal_flash_timer > 0:
            pygame.draw.circle(s, (100,255,180), (cx,cy), r+3, 2)

    def _draw_ghost(self, s, cx, cy, r):
        """Translucent purple wispy shape with wavy bottom."""
        c = self.color
        # Wispy top (semicircle)
        pygame.draw.circle(s, (80,80,120), (cx+2, cy+2), r)
        if self.is_immune:
            ghost_col = (*c, 110)
        else:
            ghost_col = c
        pygame.draw.circle(s, ghost_col if not self.is_immune else c, (cx, cy-2), r)
        # Wavy bottom (3 bumps)
        wave_pts = [(cx - r, cy + r//2)]
        for i in range(7):
            wx = cx - r + i * (r*2//6)
            wy = cy + r//2 + (4 if i % 2 == 0 else -4)
            wave_pts.append((wx, wy))
        wave_pts.append((cx + r, cy + r//2))
        pygame.draw.polygon(s, (15,10,25), wave_pts + [(cx+r, cy-r), (cx-r, cy-r)])
        pygame.draw.polygon(s, c, wave_pts + [(cx+r, cy-r), (cx-r, cy-r)])
        # Eyes
        pygame.draw.circle(s, (255,255,255), (cx-5, cy-4), 4)
        pygame.draw.circle(s, (255,255,255), (cx+5, cy-4), 4)
        pygame.draw.circle(s, (20,0,40),    (cx-5, cy-4), 2)
        pygame.draw.circle(s, (20,0,40),    (cx+5, cy-4), 2)

    def _draw_berserker(self, s, cx, cy, r):
        """Dark red angular body with outer rage spikes."""
        c = self.color
        dark = (max(0,c[0]-80), 0, 0)
        # Rage spikes
        spike_col = (255, 80, 0) if self.is_berserk else (120, 30, 10)
        for i in range(8):
            a = i * math.pi / 4
            sx1 = int(cx + math.cos(a) * (r-2))
            sy1 = int(cy + math.sin(a) * (r-2))
            sx2 = int(cx + math.cos(a) * (r + (7 if self.is_berserk else 4)))
            sy2 = int(cy + math.sin(a) * (r + (7 if self.is_berserk else 4)))
            pygame.draw.line(s, spike_col, (sx1,sy1), (sx2,sy2), 2)
        # Body
        pygame.draw.polygon(s, (10,10,10), _poly(cx+2, cy+2, 6, r-1, 0))
        pygame.draw.polygon(s, dark, _poly(cx, cy, 6, r-1, 0))
        pygame.draw.polygon(s, c,    _poly(cx, cy, 6, r-4, 0))
        # Angry eyes
        pygame.draw.line(s, (255,150,0), (cx-7, cy-4), (cx-2, cy-2), 2)
        pygame.draw.line(s, (255,150,0), (cx+7, cy-4), (cx+2, cy-2), 2)
        pygame.draw.circle(s, (255,50,0), (cx-5, cy-1), 2)
        pygame.draw.circle(s, (255,50,0), (cx+5, cy-1), 2)

    def _draw_splitter(self, s, cx, cy, r):
        """Gold shape with a dashed split line down the middle."""
        c = self.color
        dark = (max(0,c[0]-80), max(0,c[1]-80), 0)
        # Two half-circles (showing it will split)
        pygame.draw.circle(s, (10,10,10), (cx+2, cy+2), r)
        # Left half
        left_rect  = pygame.Rect(cx - r, cy - r, r, r*2)
        right_rect = pygame.Rect(cx,     cy - r, r, r*2)
        pygame.draw.ellipse(s, dark,            (cx-r+2, cy-r+2, r*2-4, r*2-4))
        pygame.draw.ellipse(s, c,               (cx-r+3, cy-r+3, r*2-6, r*2-6))
        # Left/right tinted halves
        lhalf = pygame.Surface((r, r*2), pygame.SRCALPHA)
        pygame.draw.ellipse(lhalf, (255,230,50,180), (0, 0, r*2, r*2))
        rhalf = pygame.Surface((r, r*2), pygame.SRCALPHA)
        pygame.draw.ellipse(rhalf, (255,200,20,180), (-r, 0, r*2, r*2))
        s.blit(lhalf, (cx-r, cy-r))
        s.blit(rhalf, (cx,   cy-r))
        # Split line
        for i in range(0, r*2, 5):
            pygame.draw.line(s, dark, (cx, cy - r + i), (cx, cy - r + i + 2), 2)
        # Arrow hints pointing outward
        pygame.draw.polygon(s, (255,240,80), [(cx-r-5,cy), (cx-r,cy-4), (cx-r,cy+4)])
        pygame.draw.polygon(s, (255,240,80), [(cx+r+5,cy), (cx+r,cy-4), (cx+r,cy+4)])

    # ------------------------------------------------------------------
    # Private ability ticks
    # ------------------------------------------------------------------

    def _tick_heal(self, all_enemies: list) -> None:
        self.ability_timer += 1
        if self.ability_timer >= self.ability_cooldown:
            self.ability_timer = 0
            self.heal_flash_timer = 20
            my_cx, my_cy = self.center
            for other in all_enemies:
                if other is not self and other.is_alive:
                    cx, cy = other.center
                    if math.hypot(cx - my_cx, cy - my_cy) <= self.heal_radius:
                        other.hp = min(other.max_hp, other.hp + self.heal_amount)

    def _tick_ghost(self) -> None:
        if self.immune_timer > 0:
            self.immune_timer -= 1
        else:
            self.ability_timer += 1
            if self.ability_timer >= self.ability_cooldown:
                self.ability_timer = 0
                self.immune_timer = self.immune_duration

    def _tick_berserk(self) -> None:
        if not self.is_berserk and self.hp < self.max_hp * 0.5:
            self.is_berserk = True
            self.speed *= self.berserk_speed_mult

    # ------------------------------------------------------------------
    # HP bar
    # ------------------------------------------------------------------

    def _draw_hp_bar(self, screen, ix, iy, ts):
        ratio    = max(0.0, self.hp / self.max_hp)
        hp_width = int(ts * ratio)
        bar_y    = iy - 8
        # Background track
        pygame.draw.rect(screen, (40, 0, 0),   (ix,  bar_y, ts, 4))
        # Green fill — turns yellow/red when low
        if ratio > 0.5:
            bar_col = (0, 200, 0)
        elif ratio > 0.25:
            bar_col = (220, 200, 0)
        else:
            bar_col = (220, 40, 0)
        pygame.draw.rect(screen, bar_col, (ix, bar_y, hp_width, 4))
        # Thin white highlight
        pygame.draw.line(screen, (200, 255, 200), (ix, bar_y), (ix + hp_width, bar_y), 1)