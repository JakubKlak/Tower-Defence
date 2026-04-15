"""
Tower Defence: Strategic Command
Main entry point — initialises pygame and runs the game loop.

Game states:
    MENU      — level-select world map
    UPGRADES  — persistent upgrade tree screen
    PLAYING   — active gameplay
"""

import pygame
import sys
import math
import random
from Enemy import Enemy
from Tower import Tower, TOWER_TYPES
from WaveManager import WaveManager
from Projectile import Projectile
from Particle import Particle
from PlayerAbilities import AbilityManager, ABILITY_DEFS, ABILITY_ORDER
from UpgradeTree import (
    GlobalUpgrades, UPGRADE_TREE, BRANCH_META,
    UPGRADE_POINTS_PER_WIN,
)

# ---------------------------------------------------------------------------
# Level definitions
# ---------------------------------------------------------------------------
# Balance notes:
#   Levels 1-3:  Learning curve. Generous money, high HP, only basic enemies.
#   Levels 4-6:  Mid-game. Ability enemies start appearing, paths get complex.
#   Levels 7-8:  Hard. Tight money, fast spawn, long winding paths.
#   Levels 9-10: Endgame. Maximum complexity, brutal difficulty, extra money
#                to compensate for the sheer number of enemies.
#
# menu_pos lays out a winding world-map road:
#   bottom row (L1→L5) sweeps right, then the path climbs left to L10.
# ---------------------------------------------------------------------------
LEVELS: dict[int, dict] = {
    # ── TIER 1 — Tutorial / Easy ─────────────────────────────────────────
    1: {
        "name": "Spokojna Polana",
        "path": [(0, 7), (5, 7), (5, 2), (12, 2), (12, 10), (19, 10)],
        "money": 400, "hp": 20, "difficulty": 0.8, "waves": 3,
        "menu_pos": (80, 510),
    },
    2: {
        "name": "Zygzak Zagłady",
        "path": [(0, 3), (4, 3), (4, 12), (9, 12), (9, 3), (15, 3), (15, 10), (19, 10)],
        "money": 360, "hp": 17, "difficulty": 1.0, "waves": 5,
        "menu_pos": (220, 460),
    },
    3: {
        "name": "Inwazja z Północy",
        "path": [(10, 0), (10, 5), (3, 5), (3, 12), (16, 12), (16, 7), (19, 7)],
        "money": 320, "hp": 14, "difficulty": 1.2, "waves": 6,
        "menu_pos": (370, 510),
    },
    # ── TIER 2 — Mid-game ────────────────────────────────────────────────
    4: {
        "name": "Spirala Śmierci",
        "path": [(0, 13), (17, 13), (17, 2), (3, 2), (3, 9), (12, 9), (12, 6), (7, 6)],
        "money": 400, "hp": 12, "difficulty": 1.4, "waves": 7,
        "menu_pos": (520, 450),
    },
    5: {
        "name": "Wrota Piekieł",
        "path": [(0, 7), (8, 7), (8, 2), (12, 2), (12, 12), (16, 12), (16, 7), (19, 7)],
        "money": 430, "hp": 9, "difficulty": 1.6, "waves": 8,
        "menu_pos": (660, 490),
    },
    6: {
        "name": "Labirynt Śmierci",
        "path": [
            (0, 5), (4, 5), (4, 1), (9, 1), (9, 8),
            (6, 8), (6, 13), (13, 13), (13, 5),
            (17, 5), (17, 10), (19, 10),
        ],
        "money": 450, "hp": 18, "difficulty": 1.5, "waves": 7,
        "menu_pos": (720, 360),
        # HP resets higher here — this is a "breather" level after tier 1
        # before things get seriously hard. Path is longer so enemies take
        # more tower fire before reaching the base.
    },
    # ── TIER 3 — Hard ────────────────────────────────────────────────────
    7: {
        "name": "Pułapka",
        "path": [
            (0, 1), (3, 1), (3, 13), (7, 13),
            (7, 3), (11, 3), (11, 13),
            (15, 13), (15, 3), (19, 3),
        ],
        "money": 420, "hp": 13, "difficulty": 1.8, "waves": 9,
        "menu_pos": (600, 240),
        # Comb pattern — enemies walk the full height 4 times.
        # Very long path means sustained DPS is rewarded over burst.
    },
    8: {
        "name": "Cmentarz Bohaterów",
        "path": [
            (0, 6), (2, 6), (2, 1), (8, 1), (8, 11),
            (5, 11), (5, 13), (12, 13), (12, 6),
            (16, 6), (16, 1), (19, 1),
        ],
        "money": 400, "hp": 9, "difficulty": 2.0, "waves": 10,
        "menu_pos": (440, 170),
    },
    # ── TIER 4 — Endgame ─────────────────────────────────────────────────
    9: {
        "name": "Forteca Zła",
        "path": [
            (10, 0), (10, 4), (2, 4), (2, 11),
            (8, 11), (8, 7), (5, 7), (5, 13),
            (13, 13), (13, 8), (17, 8), (17, 3), (19, 3),
        ],
        "money": 480, "hp": 7, "difficulty": 2.3, "waves": 12,
        "menu_pos": (270, 240),
        # Enters from the top — unusual for the player. Extra money because
        # the enemy pool at wave 9+ is brutal (ghosts, splitters, berserkers).
    },
    10: {
        "name": "Apokalipsa",
        "path": [
            (0, 2), (4, 2), (4, 7), (1, 7), (1, 12),
            (6, 12), (6, 8), (10, 8), (10, 12),
            (15, 12), (15, 5), (11, 5), (11, 2),
            (17, 2), (17, 8), (19, 8),
        ],
        "money": 550, "hp": 5, "difficulty": 2.8, "waves": 15,
        "menu_pos": (110, 160),
        # Final level. Longest path in the game (16 waypoints).
        # Enemies reach 15 full waves before the level ends.
        # Generous starting money — you'll need every tower you can afford.
    },
}

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
GAME_WIDTH: int = 800
UI_WIDTH: int = 240
HEIGHT: int = 600
TOTAL_WIDTH: int = GAME_WIDTH + UI_WIDTH
TILE: int = 40
TOWER_CLICK_RADIUS: int = 25
PATH_CLEARANCE: int = 30
TOWER_SPACING: int = 35

# ---------------------------------------------------------------------------
# Ability button layout — used by BOTH draw and click, defined once here
# so they can never get out of sync.
# ---------------------------------------------------------------------------
_UTIL_X      = GAME_WIDTH + 14   # left edge of both columns
_UTIL_Y      = 147               # top edge of row 0 (right below wave button)
_UTIL_BTN_W  = 106
_UTIL_BTN_H  = 26
_UTIL_BTN_GAP = 4                # gap between columns and rows
# Column 0 left: _UTIL_X,  Column 1 left: _UTIL_X + _UTIL_BTN_W + _UTIL_BTN_GAP
# Row 0 top: _UTIL_Y,      Row 1 top: _UTIL_Y + _UTIL_BTN_H + _UTIL_BTN_GAP
# Shop / tower panel starts below abilities:
_SHOP_START_Y = _UTIL_Y + 2 * (_UTIL_BTN_H + _UTIL_BTN_GAP) + 10  # ≈ 217

# Upgrade tree screen layout
_TREE_NODE_W: int = 180
_TREE_NODE_H: int = 64
_TREE_COL_GAP: int = 50
_TREE_ROW_GAP: int = 30
_TREE_START_X: int = 30
_TREE_START_Y: int = 110


class Game:
    """Top-level game controller."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((TOTAL_WIDTH, HEIGHT))
        pygame.display.set_caption("Tower Defense: Strategic Command")
        self.clock = pygame.time.Clock()

        self.font_big   = pygame.font.SysFont("Segoe UI", 40, bold=True)
        self.font_med   = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI", 16)
        self.font_tiny  = pygame.font.SysFont("Segoe UI", 12)

        # ---- Persistent session state ----
        self.upgrades = GlobalUpgrades()
        self.unlocked_levels: set[int] = {1}   # only level 1 starts open

        self.state: str = "MENU"
        self.selected_tower_type: str | None = "basic"
        self.selected_tower_obj: Tower | None = None

        # ---- Runtime (initialised in start_level) ----
        self.current_level_id: int = 1
        self.path: list = []
        self.money: int = 0
        self.base_hp: int = 0
        self.max_base_hp: int = 0
        self.enemies: list[Enemy] = []
        self.towers: list[Tower] = []
        self.projectiles: list[Projectile] = []
        self.particles: list[Particle] = []
        self.wave_mgr: WaveManager | None = None
        self.abilities: AbilityManager | None = None
        self.valid_grid: list[list[bool]] = []
        self.game_over: bool = False
        self.victory: bool = False
        self._victory_processed: bool = False   # prevent double-awarding points

    # ==================================================================
    # Level setup
    # ==================================================================

    def start_level(self, level_id: int) -> None:
        """Reset all per-level state and start playing."""
        self.current_level_id = level_id
        lvl = LEVELS[level_id]
        self.path = lvl["path"]

        # Apply global upgrade bonuses
        gu = self.upgrades
        self.money     = lvl["money"] + gu.start_gold_bonus
        self.base_hp   = lvl["hp"]    + gu.base_hp_bonus
        self.max_base_hp = self.base_hp

        self.enemies = []
        self.towers = []
        self.projectiles = []
        self.particles = []
        self.selected_tower_obj = None
        self.selected_tower_type = None
        self.game_over = False
        self.victory = False
        self._victory_processed = False

        self.wave_mgr = WaveManager(difficulty=lvl["difficulty"], max_waves=lvl["waves"])

        self.abilities = AbilityManager(max_base_hp=self.base_hp)
        self.abilities.set_cooldown_reduction(gu.cooldown_reduction)

        self._precompute_valid_positions()
        self.state = "PLAYING"

    # ==================================================================
    # Per-frame update (PLAYING state)
    # ==================================================================

    def _update_playing(self) -> None:
        if self.game_over or self.victory:
            return
        self.abilities.update()
        etype = self.wave_mgr.update()
        if etype:
            self.enemies.append(Enemy(self.path, TILE, etype))
        self._update_particles()
        self._update_projectiles()
        self._update_enemies()
        self._update_towers()

    def _update_particles(self) -> None:
        for p in self.particles:
            p.move()
        self.particles = [p for p in self.particles if not p.reached]

    def _update_projectiles(self) -> None:
        surviving = []
        for proj in self.projectiles:
            hit = proj.move()
            if hit:
                proj.target.take_damage(proj.damage)
                if proj.effect == "slow":
                    proj.target.apply_slow()
                cx, cy = proj.target.center
                for _ in range(5):
                    self.particles.append(Particle(cx, cy, proj.color))
            if not proj.reached:
                surviving.append(proj)
        self.projectiles = surviving

    def _update_enemies(self) -> None:
        gu = self.upgrades
        surviving, new_enemies = [], []
        for enemy in self.enemies:
            enemy.move()
            enemy.tick_ability(self.enemies)
            if not enemy.is_alive:
                if enemy.will_split:
                    for _ in range(enemy.split_count):
                        child = Enemy(self.path, TILE, enemy.split_type)
                        child.pos_index = enemy.pos_index
                        child.x, child.y = enemy.x, enemy.y
                        child.exact_progress = enemy.exact_progress
                        new_enemies.append(child)
                base_reward = enemy.reward * self.abilities.reward_multiplier
                # Economy upgrades stack on top of Gold Rush multiplier
                self.money += int(base_reward * (1.0 + gu.reward_mult_bonus))
            elif enemy.has_reached_end:
                dmg = max(1, enemy.damage - gu.base_damage_reduce)
                self.base_hp -= dmg
                if self.base_hp <= 0:
                    self.base_hp = 0
                    self.game_over = True
            else:
                surviving.append(enemy)
        self.enemies = surviving + new_enemies

    def _update_towers(self) -> None:
        for tower in self.towers:
            tower.find_target(self.enemies)
            tower.attack(self.projectiles)

    # ==================================================================
    # Player ability execution
    # ==================================================================

    def _execute_ability(self, key: str, mx: int = 0, my: int = 0) -> None:
        gu = self.upgrades
        if key == "meteor":
            self._apply_meteor(mx, my, gu)
        elif key == "freeze":
            for enemy in self.enemies:
                enemy.slow_timer = ABILITY_DEFS["freeze"]["slow_frames"]
        elif key == "gold_rush":
            pass   # timer started in AbilityManager.activate_instant
        elif key == "repair":
            heal = ABILITY_DEFS["repair"]["heal_hp"] + gu.repair_bonus
            self.base_hp = min(self.max_base_hp, self.base_hp + heal)

    def _apply_meteor(self, cx: int, cy: int, gu: GlobalUpgrades) -> None:
        defn = ABILITY_DEFS["meteor"]
        radius = defn["radius"]
        damage = defn["damage"] * (1.0 + gu.meteor_damage_bonus)
        for enemy in self.enemies:
            ex, ey = enemy.center
            if math.hypot(ex - cx, ey - cy) <= radius:
                enemy.take_damage(damage)
        for _ in range(defn["particle_count"]):
            sx = cx + random.uniform(-radius * 0.8, radius * 0.8)
            sy = cy + random.uniform(-radius * 0.8, radius * 0.8)
            self.particles.append(Particle(sx, sy, (255, random.randint(60, 160), 0)))
        for angle in range(0, 360, 12):
            rad = math.radians(angle)
            self.particles.append(Particle(cx + math.cos(rad) * radius,
                                            cy + math.sin(rad) * radius,
                                            (255, 200, 50)))

    # ==================================================================
    # DRAWING — MENU
    # ==================================================================

    def _draw_menu(self) -> None:
        # ── Background terrain ─────────────────────────────────────────
        self.screen.fill((18, 28, 18))

        # Hex-grid terrain overlay
        HEX_R = 28
        for row in range(-1, HEIGHT // (HEX_R * 2) + 2):
            for col in range(-1, GAME_WIDTH // (HEX_R * 2) + 2):
                hx = col * HEX_R * 2 + (HEX_R if row % 2 else 0)
                hy = row * int(HEX_R * 1.73)
                shade = 26 + ((row * 7 + col * 5) % 10)
                pts = []
                for i in range(6):
                    a = math.pi / 6 + i * math.pi / 3
                    pts.append((hx + HEX_R * 0.9 * math.cos(a),
                                hy + HEX_R * 0.9 * math.sin(a)))
                pygame.draw.polygon(self.screen, (shade, shade + 4, shade), pts)
                pygame.draw.polygon(self.screen, (30, 38, 30), pts, 1)

        # ── Animated title ─────────────────────────────────────────────
        t = pygame.time.get_ticks()
        # Glow pulse
        glow_alpha = 60 + int(40 * math.sin(t * 0.003))
        glow_surf = pygame.Surface((500, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (0, 255, 120, glow_alpha), (0, 0, 500, 60))
        self.screen.blit(glow_surf, (GAME_WIDTH // 2 - 250, 14))

        title = self.font_big.render("TOWER DEFENSE", True, (0, 255, 150))
        sub   = self.font_small.render("STRATEGIC COMMAND", True, (100, 200, 120))
        self.screen.blit(title, (GAME_WIDTH // 2 - title.get_width() // 2, 18))
        self.screen.blit(sub,   (GAME_WIDTH // 2 - sub.get_width() // 2,   64))

        # ── Road between level nodes ────────────────────────────────────
        pts_all = [LEVELS[i]["menu_pos"] for i in sorted(LEVELS.keys())]
        # Road shadow
        pygame.draw.lines(self.screen, (10, 18, 10), False, pts_all, 10)
        # Road surface (dashed tan line)
        pygame.draw.lines(self.screen, (55, 68, 45), False, pts_all, 6)
        # Centre dashes
        for i in range(len(pts_all) - 1):
            ax, ay = pts_all[i]
            bx, by = pts_all[i + 1]
            seg_len = math.hypot(bx - ax, by - ay)
            steps = int(seg_len / 14)
            for s in range(steps):
                frac0 = s / steps
                frac1 = (s + 0.45) / steps
                x0 = int(ax + (bx - ax) * frac0)
                y0 = int(ay + (by - ay) * frac0)
                x1 = int(ax + (bx - ax) * frac1)
                y1 = int(ay + (by - ay) * frac1)
                pygame.draw.line(self.screen, (100, 140, 80), (x0, y0), (x1, y1), 2)

        # ── Level nodes ─────────────────────────────────────────────────
        mx, my = pygame.mouse.get_pos()
        hovered_lvl  = None
        hovered_lid  = None

        tier_colors = {
            1: (80, 180, 100),   # green   — easy
            2: (80, 180, 100),
            3: (80, 180, 100),
            4: (220, 180, 40),   # yellow  — medium
            5: (220, 180, 40),
            6: (220, 180, 40),
            7: (220, 100, 40),   # orange  — hard
            8: (220, 100, 40),
            9: (200, 50,  50),   # red     — brutal
            10:(200, 50,  50),
        }
        tier_labels = {1:"I", 2:"I", 3:"I", 4:"II", 5:"II", 6:"II",
                       7:"III", 8:"III", 9:"IV", 10:"IV"}

        for lid, data in LEVELS.items():
            pos       = data["menu_pos"]
            unlocked  = lid in self.unlocked_levels
            is_hover  = math.hypot(mx - pos[0], my - pos[1]) < 26 and unlocked
            tc        = tier_colors[lid]

            if is_hover:
                hovered_lvl = data
                hovered_lid = lid

            # Outer glow for hovered / unlocked
            if is_hover:
                glow = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*tc, 60), (40, 40), 38)
                self.screen.blit(glow, (pos[0] - 40, pos[1] - 40))

            # Node shadow
            pygame.draw.circle(self.screen, (8, 12, 8), (pos[0]+3, pos[1]+3), 26)

            if not unlocked:
                # Locked: dark with padlock glyph
                pygame.draw.circle(self.screen, (30, 35, 30), pos, 26)
                pygame.draw.circle(self.screen, (45, 55, 45), pos, 26, 2)
                pygame.draw.rect(self.screen, (60, 70, 60),
                                 (pos[0]-8, pos[1]-4, 16, 12))
                pygame.draw.arc(self.screen, (60, 70, 60),
                                (pos[0]-6, pos[1]-12, 12, 14),
                                0, math.pi, 2)
                num = self.font_tiny.render(str(lid), True, (55, 65, 55))
                self.screen.blit(num, (pos[0] - num.get_width()//2, pos[1]+10))
            else:
                # Unlocked ring + fill
                ring_col = (255, 255, 255) if is_hover else tc
                pygame.draw.circle(self.screen, (20, 30, 20), pos, 26)
                pygame.draw.circle(self.screen, tc,       pos, 22)
                pygame.draw.circle(self.screen, ring_col, pos, 26, 3)
                # Level number
                num_col = (255, 255, 255) if is_hover else (220, 240, 220)
                num = self.font_med.render(str(lid), True, num_col)
                self.screen.blit(num, (pos[0] - num.get_width()//2,
                                       pos[1] - num.get_height()//2))
                # Tiny tier badge (top-right of node)
                badge_x = pos[0] + 16
                badge_y = pos[1] - 22
                pygame.draw.circle(self.screen, (20, 20, 20), (badge_x, badge_y), 9)
                pygame.draw.circle(self.screen, (tc[0]//2+30, tc[1]//2+30, tc[2]//2+30),
                                   (badge_x, badge_y), 8)
                bl = self.font_tiny.render(tier_labels[lid], True, (220, 220, 220))
                self.screen.blit(bl, (badge_x - bl.get_width()//2,
                                      badge_y - bl.get_height()//2))

        # ── Side panel ─────────────────────────────────────────────────
        sx = GAME_WIDTH
        # Panel background with subtle gradient effect via rects
        for i in range(UI_WIDTH):
            shade = max(12, 20 - i // 20)
            pygame.draw.line(self.screen, (shade, shade, shade + 3),
                             (sx + i, 0), (sx + i, HEIGHT))
        pygame.draw.line(self.screen, (0, 200, 100), (sx, 0), (sx, HEIGHT), 2)

        # Title
        self.screen.blit(
            self.font_med.render("MAPA OPERACJI", True, (0, 230, 110)),
            (sx + 20, 20),
        )
        pygame.draw.line(self.screen, (0, 100, 60),
                         (sx + 10, 46), (sx + UI_WIDTH - 10, 46), 1)

        # Upgrade points
        pts_label = self.font_small.render(
            f"Punkty: {self.upgrades.points}", True, (255, 215, 0)
        )
        self.screen.blit(pts_label, (sx + 20, 55))

        # Upgrade tree button
        ub_active = self.upgrades.points > 0
        ub_col    = (0, 200, 255) if ub_active else (50, 70, 50)
        pygame.draw.rect(self.screen, (15, 18, 15), (sx + 15, 78, 210, 34))
        pygame.draw.rect(self.screen, ub_col,       (sx + 15, 78, 210, 34), 2)
        self.screen.blit(
            self.font_small.render("[U] DRZEWO ULEPSZEŃ", True, ub_col),
            (sx + 25, 87),
        )

        pygame.draw.line(self.screen, (30, 40, 30),
                         (sx + 10, 120), (sx + UI_WIDTH - 10, 120), 1)

        # Hovered level stats
        if hovered_lvl and hovered_lid:
            tc = tier_colors[hovered_lid]
            name_surf = self.font_med.render(hovered_lvl["name"].upper(), True, tc)
            self.screen.blit(name_surf, (sx + 20, 130))

            tier_name = {1:"TIER I — ŁATWY", 2:"TIER I — ŁATWY",
                         3:"TIER I — ŁATWY", 4:"TIER II — ŚREDNI",
                         5:"TIER II — ŚREDNI", 6:"TIER II — ŚREDNI",
                         7:"TIER III — TRUDNY", 8:"TIER III — TRUDNY",
                         9:"TIER IV — EKSTREMALNY", 10:"TIER IV — EKSTREMALNY"}
            tier_surf = self.font_tiny.render(tier_name[hovered_lid], True,
                                              (tc[0]//2+80, tc[1]//2+80, tc[2]//2+80))
            self.screen.blit(tier_surf, (sx + 20, 156))

            y_stat = 178
            for lbl, val, color in [
                ("KASA",      hovered_lvl["money"],      (255, 215, 0)),
                ("HP BAZY",   hovered_lvl["hp"],          (255, 80,  80)),
                ("FALE",      hovered_lvl["waves"],       (100, 160, 255)),
                ("TRUDNOŚĆ",  f"{hovered_lvl['difficulty']:.1f}x", (200, 140, 255)),
            ]:
                self.screen.blit(self.font_tiny.render(lbl,    True, (120, 130, 120)),
                                 (sx + 20, y_stat))
                self.screen.blit(self.font_small.render(str(val), True, color),
                                 (sx + 20, y_stat + 14))
                y_stat += 44

        # Tier legend at bottom
        legend_y = HEIGHT - 105
        pygame.draw.line(self.screen, (30, 40, 30),
                         (sx + 10, legend_y - 8), (sx + UI_WIDTH - 10, legend_y - 8), 1)
        self.screen.blit(self.font_tiny.render("LEGENDA POZIOMÓW", True, (80, 100, 80)),
                         (sx + 20, legend_y))
        for i, (label, col) in enumerate([
            ("I   — Łatwy",         (80, 180, 100)),
            ("II  — Średni",        (220, 180, 40)),
            ("III — Trudny",        (220, 100, 40)),
            ("IV  — Ekstremalny",   (200, 50,  50)),
        ]):
            pygame.draw.circle(self.screen, col,
                               (sx + 26, legend_y + 18 + i * 20), 5)
            self.screen.blit(
                self.font_tiny.render(label, True, (150, 160, 150)),
                (sx + 36, legend_y + 10 + i * 20),
            )

        pygame.display.update()

    # ==================================================================
    # DRAWING — UPGRADE TREE
    # ==================================================================

    def _draw_upgrades(self) -> None:
        self.screen.fill((12, 12, 18))

        # Title bar
        pygame.draw.rect(self.screen, (20, 20, 30), (0, 0, TOTAL_WIDTH, 80))
        pygame.draw.line(self.screen, (0, 255, 150), (0, 80), (TOTAL_WIDTH, 80), 1)
        self.screen.blit(
            self.font_big.render("DRZEWO ULEPSZEŃ", True, (0, 255, 150)),
            (30, 20),
        )
        pts_label = self.font_med.render(
            f"Dostępne punkty:  {self.upgrades.points}", True, (255, 215, 0)
        )
        self.screen.blit(pts_label, (TOTAL_WIDTH - pts_label.get_width() - 30, 25))

        # Back button
        pygame.draw.rect(self.screen, (50, 50, 60), (TOTAL_WIDTH - 140, HEIGHT - 50, 120, 36), 2)
        self.screen.blit(
            self.font_small.render("[ESC] POWRÓT", True, (200, 200, 200)),
            (TOTAL_WIDTH - 128, HEIGHT - 42),
        )

        # Branch column headers
        for col_idx, meta in BRANCH_META.items():
            x = _TREE_START_X + col_idx * (_TREE_NODE_W + _TREE_COL_GAP)
            self.screen.blit(
                self.font_small.render(meta["name"], True, meta["color"]),
                (x, _TREE_START_Y - 24),
            )

        # Draw connector lines first (under nodes)
        for key, node in UPGRADE_TREE.items():
            req = node["requires"]
            if req:
                nx, ny = self._node_pos(node["col"], node["row"])
                rx, ry = self._node_pos(
                    UPGRADE_TREE[req]["col"], UPGRADE_TREE[req]["row"]
                )
                # line from bottom-centre of parent to top-centre of child
                start = (rx + _TREE_NODE_W // 2, ry + _TREE_NODE_H)
                end   = (nx + _TREE_NODE_W // 2, ny)
                col_meta = BRANCH_META[node["col"]]
                line_col = col_meta["color"] if req in self.upgrades.purchased else (50, 50, 60)
                pygame.draw.line(self.screen, line_col, start, end, 2)

        # Draw nodes
        mx, my = pygame.mouse.get_pos()
        for key, node in UPGRADE_TREE.items():
            self._draw_upgrade_node(key, node, mx, my)

        pygame.display.update()

    def _node_pos(self, col: int, row: int) -> tuple[int, int]:
        x = _TREE_START_X + col * (_TREE_NODE_W + _TREE_COL_GAP)
        y = _TREE_START_Y + row * (_TREE_NODE_H + _TREE_ROW_GAP)
        return x, y

    def _draw_upgrade_node(self, key: str, node: dict, mx: int, my: int) -> None:
        x, y = self._node_pos(node["col"], node["row"])
        purchased = key in self.upgrades.purchased
        can_buy   = self.upgrades.can_purchase(key)
        hover     = x < mx < x + _TREE_NODE_W and y < my < y + _TREE_NODE_H
        col_meta  = BRANCH_META[node["col"]]

        # Background + border
        bg  = (22, 28, 22) if purchased else (18, 18, 24)
        if purchased:
            border = col_meta["color"]
            border_w = 2
        elif can_buy:
            border = (255, 215, 0) if hover else col_meta["color"]
            border_w = 2 if hover else 1
        else:
            border = (40, 40, 50)
            border_w = 1

        pygame.draw.rect(self.screen, bg, (x, y, _TREE_NODE_W, _TREE_NODE_H))
        pygame.draw.rect(self.screen, border, (x, y, _TREE_NODE_W, _TREE_NODE_H), border_w)

        # Cost badge (top-right corner)
        cost_col = (255, 215, 0) if can_buy or purchased else (80, 80, 80)
        badge = self.font_tiny.render(
            "✓" if purchased else f"{node['cost']}pt",
            True, cost_col,
        )
        self.screen.blit(badge, (x + _TREE_NODE_W - badge.get_width() - 6, y + 5))

        # Name
        name_col = col_meta["color"] if (purchased or can_buy) else (70, 70, 80)
        self.screen.blit(
            self.font_small.render(node["name"], True, name_col),
            (x + 8, y + 8),
        )

        # Description (word-wrapped to two short lines)
        desc_col = (160, 160, 160) if (purchased or can_buy) else (60, 60, 70)
        desc = node["desc"]
        self.screen.blit(self.font_tiny.render(desc, True, desc_col), (x + 8, y + 30))

        # "Click to buy" hint on hover
        if can_buy and hover:
            hint = self.font_tiny.render("Kliknij aby kupić", True, (255, 230, 100))
            self.screen.blit(hint, (x + 8, y + _TREE_NODE_H - 16))

    # ==================================================================
    # DRAWING — PLAYING
    # ==================================================================

    def _draw_playing(self) -> None:
        mx, my = pygame.mouse.get_pos()

        # Textured ground — alternating dark-green tile shading
        for row in range(HEIGHT // TILE + 1):
            for col in range(GAME_WIDTH // TILE + 1):
                shade = 14 + ((row + col) % 2) * 4
                pygame.draw.rect(self.screen,
                    (shade, shade + 4, shade),
                    (col * TILE, row * TILE, TILE, TILE))

        # Path — thick dark road with lighter centre line
        pts_path = [(p[0] * TILE + TILE // 2, p[1] * TILE + TILE // 2) for p in self.path]
        if len(pts_path) > 1:
            pygame.draw.lines(self.screen, (30, 36, 28), False, pts_path, 26)
            pygame.draw.lines(self.screen, (42, 52, 38), False, pts_path, 20)
            # Dashed centre
            for i in range(len(pts_path) - 1):
                ax, ay = pts_path[i]
                bx, by = pts_path[i + 1]
                seg_len = math.hypot(bx - ax, by - ay)
                steps = int(seg_len / 12)
                for s in range(steps):
                    f0 = s / steps
                    f1 = (s + 0.4) / steps
                    pygame.draw.line(self.screen, (55, 70, 50),
                        (int(ax + (bx-ax)*f0), int(ay + (by-ay)*f0)),
                        (int(ax + (bx-ax)*f1), int(ay + (by-ay)*f1)), 2)

        for tower in self.towers:   tower.draw(self.screen)
        for enemy in self.enemies:  enemy.draw(self.screen)
        for proj  in self.projectiles: proj.draw(self.screen)
        for part  in self.particles:   part.draw(self.screen)

        # Meteor targeting overlay
        if self.abilities and self.abilities.pending == "meteor" and mx < GAME_WIDTH:
            r = ABILITY_DEFS["meteor"]["radius"]
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 120, 0, 60), (r, r), r)
            self.screen.blit(surf, (mx - r, my - r))
            pygame.draw.circle(self.screen, (255, 120, 0), (mx, my), r, 2)
        elif mx < GAME_WIDTH and not self.selected_tower_obj and self.selected_tower_type:
            self._draw_placement_preview(mx, my)

        self._draw_ui_panel(mx, my)

        if self.game_over or self.victory:
            self._draw_end_overlay()

        pygame.display.update()

    def _draw_placement_preview(self, mx: int, my: int) -> None:
        t_data = TOWER_TYPES[self.selected_tower_type]
        r = t_data["range"]
        can_place = self._is_position_valid(mx, my) and self.money >= t_data["cost"]
        col = (0, 255, 150) if can_place else (255, 50, 50)
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA).convert_alpha()
        pygame.draw.circle(surf, (*col, 40), (r, r), r)
        self.screen.blit(surf, (mx - r, my - r))
        pygame.draw.circle(self.screen, t_data["color"], (mx, my), 15)
        pygame.draw.circle(self.screen, col, (mx, my), 17, 2)

    def _draw_ui_panel(self, mx: int, my: int) -> None:
        sx = GAME_WIDTH
        pygame.draw.rect(self.screen, (15, 15, 18), (sx, 0, UI_WIDTH, HEIGHT))
        pygame.draw.line(self.screen, (0, 255, 150), (sx, 0), (sx, HEIGHT), 2)

        # Stats
        self.screen.blit(self.font_med.render(f"${self.money}", True, (255, 215, 0)), (sx + 20, 20))
        if self.abilities.gold_rush_active:
            self.screen.blit(self.font_tiny.render("x2 GOLD", True, (255, 215, 0)), (sx + 110, 27))
        self.screen.blit(self.font_small.render(f"HP: {self.base_hp}", True, (255, 50, 50)), (sx + 20, 50))
        self.screen.blit(
            self.font_small.render(
                f"FALA: {self.wave_mgr.current_wave}/{self.wave_mgr.max_waves}",
                True, (100, 150, 255),
            ),
            (sx + 20, 70),
        )

        # Wave button
        can_start = self.wave_mgr.is_ready_for_next_wave and not self.game_over and not self.victory
        btn_col = (0, 200, 100) if can_start else (60, 60, 60)
        pygame.draw.rect(self.screen, btn_col, (sx + 20, 94, 200, 34))
        msg = "START FALI (SPACE)" if can_start else "FALA WYCHODZI..."
        self.screen.blit(self.font_small.render(msg, True, (255, 255, 255)), (sx + 35, 103))

        # ── Ability buttons (always visible, fixed position) ──────────
        self.screen.blit(
            self.font_tiny.render("ZDOLNOŚCI [M/F/G/H]", True, (120, 120, 130)),
            (sx + 14, 135),
        )
        for i, key in enumerate(ABILITY_ORDER):
            col_i = i % 2
            row_i = i // 2
            bx = _UTIL_X + col_i * (_UTIL_BTN_W + _UTIL_BTN_GAP)
            by = _UTIL_Y + row_i * (_UTIL_BTN_H + _UTIL_BTN_GAP)

            defn       = ABILITY_DEFS[key]
            available  = self.abilities.can_use(key, self.money)
            is_pending = self.abilities.pending == key

            if is_pending:
                border = (255, 200, 0)
            elif available:
                border = defn["color"]
            else:
                border = (50, 50, 55)

            pygame.draw.rect(self.screen, (20, 20, 24), (bx, by, _UTIL_BTN_W, _UTIL_BTN_H))
            pygame.draw.rect(self.screen, border,       (bx, by, _UTIL_BTN_W, _UTIL_BTN_H), 1)

            # Cooldown overlay — fills from left, shrinks as cooldown drains
            frac = self.abilities.cooldown_fraction(key)
            if frac > 0:
                ov_w = max(1, int(_UTIL_BTN_W * frac))
                ov = pygame.Surface((ov_w, _UTIL_BTN_H), pygame.SRCALPHA)
                ov.fill((0, 0, 0, 160))
                self.screen.blit(ov, (bx, by))
                secs = self.abilities.cooldown_seconds_remaining(key)
                cd = self.font_tiny.render(f"{secs:.0f}s", True, (200, 200, 200))
                self.screen.blit(cd, (bx + _UTIL_BTN_W - cd.get_width() - 3, by + _UTIL_BTN_H - 13))

            txt_col = border if (available or is_pending) else (60, 60, 65)
            self.screen.blit(
                self.font_tiny.render(f"[{defn['key_hint']}] {defn['name']}", True, txt_col),
                (bx + 4, by + 8),
            )

        pygame.draw.line(self.screen, (40, 40, 50),
                         (sx + 10, _SHOP_START_Y - 5),
                         (sx + UI_WIDTH - 10, _SHOP_START_Y - 5), 1)

        if self.selected_tower_obj:
            self._draw_tower_panel(sx)
        else:
            self._draw_shop_panel(sx)

        # Victory check (once only)
        if not self._victory_processed and self.wave_mgr.all_waves_done and not self.enemies:
            self.victory = True
            self._victory_processed = True
            self.upgrades.points += UPGRADE_POINTS_PER_WIN
            next_lvl = self.current_level_id + 1
            if next_lvl in LEVELS:
                self.unlocked_levels.add(next_lvl)

    def _draw_tower_panel(self, sx: int) -> None:
        t = self.selected_tower_obj
        y0 = _SHOP_START_Y
        self.screen.blit(self.font_med.render("ULEPSZENIA", True, (0, 255, 150)), (sx + 20, y0))
        self.screen.blit(self.font_small.render(f"Typ: {t.type.upper()}", True, (200, 200, 200)), (sx + 20, y0 + 26))
        self.screen.blit(self.font_small.render(f"LVL: {t.level}", True, (200, 200, 200)), (sx + 20, y0 + 46))

        u_cost = int(TOWER_TYPES[t.type]["cost"] * 0.9 * t.level)
        can_up = t.level < (self.current_level_id + 1) and t.level < 4

        if t.level < 3:
            u_col = (0, 255, 150) if (self.money >= u_cost and can_up) else (80, 80, 80)
            pygame.draw.rect(self.screen, u_col, (sx + 20, y0 + 74, 200, 38), 2)
            txt = f"ULEPSZ (${u_cost})" if can_up else "MAX MAPY"
            self.screen.blit(self.font_small.render(txt, True, u_col), (sx + 35, y0 + 86))
        elif t.level == 3 and self.current_level_id >= 3:
            for i, lab in enumerate(["A: MOC ($200)", "B: SPEED ($200)", "C: RANGE ($200)"]):
                y = y0 + 80 + i * 44
                pygame.draw.rect(self.screen, (0, 200, 255), (sx + 20, y, 200, 36), 1)
                self.screen.blit(self.font_small.render(lab, True, (0, 200, 255)), (sx + 35, y + 9))

        desel_y = y0 + 210
        pygame.draw.rect(self.screen, (255, 50, 50), (sx + 20, desel_y, 200, 32), 1)
        self.screen.blit(self.font_small.render("ODZNACZ WIEŻĘ", True, (255, 50, 50)), (sx + 50, desel_y + 8))

    def _draw_shop_panel(self, sx: int) -> None:
        self.screen.blit(self.font_small.render("SKLEP:", True, (150, 150, 150)), (sx + 20, _SHOP_START_Y))
        y_off = _SHOP_START_Y + 20
        for t_name, data in TOWER_TYPES.items():
            is_sel = self.selected_tower_type == t_name
            pygame.draw.rect(self.screen,
                (0, 255, 150) if is_sel else (40, 40, 40),
                (sx + 15, y_off, 210, 36),
                1 if not is_sel else 2)
            self.screen.blit(
                self.font_small.render(f"{t_name.upper()} (${data['cost']})", True, (255, 255, 255)),
                (sx + 28, y_off + 9))
            y_off += 40

        is_none = self.selected_tower_type is None
        pygame.draw.rect(self.screen,
            (255, 100, 100) if is_none else (40, 40, 40),
            (sx + 15, y_off, 210, 30), 1 if not is_none else 2)
        self.screen.blit(self.font_small.render("0. BRAK WYBORU", True, (255, 100, 100)), (sx + 28, y_off + 7))

    def _draw_end_overlay(self) -> None:
        overlay = pygame.Surface((TOTAL_WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        cx = TOTAL_WIDTH // 2
        if self.victory:
            txt1 = self.font_big.render("MISJA ZAKOŃCZONA SUKCESEM!", True, (0, 255, 150))
            pts_notice = self.font_med.render(
                f"+{UPGRADE_POINTS_PER_WIN} punkty ulepszeń", True, (255, 215, 0)
            )
            txt2 = self.font_small.render("[ENTER] → Mapa   [U] → Ulepszenia", True, (200, 200, 200))
            self.screen.blit(txt1, (cx - txt1.get_width() // 2, HEIGHT // 2 - 70))
            self.screen.blit(pts_notice, (cx - pts_notice.get_width() // 2, HEIGHT // 2 - 20))
            self.screen.blit(txt2, (cx - txt2.get_width() // 2, HEIGHT // 2 + 25))
        else:
            txt1 = self.font_big.render("OPERACJA NIEUDANA", True, (255, 50, 50))
            txt2 = self.font_small.render("[R] powtórz   [ESC] mapa", True, (200, 200, 200))
            self.screen.blit(txt1, (cx - txt1.get_width() // 2, HEIGHT // 2 - 50))
            self.screen.blit(txt2, (cx - txt2.get_width() // 2, HEIGHT // 2 + 20))

    # ==================================================================
    # INPUT HANDLING
    # ==================================================================

    def _handle_menu_click(self, mx: int, my: int) -> None:
        # Upgrade tree button
        sx = GAME_WIDTH
        if sx + 20 < mx < sx + 220 and 90 < my < 126:
            self.state = "UPGRADES"
            return
        # Level node
        for lid, data in LEVELS.items():
            if math.hypot(mx - data["menu_pos"][0], my - data["menu_pos"][1]) < 30:
                if lid in self.unlocked_levels:
                    self.start_level(lid)

    def _handle_menu_keydown(self, key: int) -> None:
        if key == pygame.K_u:
            self.state = "UPGRADES"

    def _handle_upgrades_click(self, mx: int, my: int) -> None:
        for key, node in UPGRADE_TREE.items():
            nx, ny = self._node_pos(node["col"], node["row"])
            if nx < mx < nx + _TREE_NODE_W and ny < my < ny + _TREE_NODE_H:
                self.upgrades.purchase(key)
                return

    def _handle_playing_keydown(self, key: int) -> None:
        if self.victory:
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.state = "MENU"
            elif key == pygame.K_u:
                self.state = "UPGRADES"
            return

        if self.game_over:
            if key == pygame.K_r:
                self.start_level(self.current_level_id)
            elif key == pygame.K_ESCAPE:
                self.state = "MENU"
            return

        if key == pygame.K_SPACE and self.wave_mgr.is_ready_for_next_wave:
            self.wave_mgr.start_next_wave()

        if key == pygame.K_ESCAPE:
            if self.abilities.pending:
                self.abilities.pending = None
            else:
                self.state = "MENU"

        tower_keys = {
            pygame.K_1: "basic",   pygame.K_2: "sniper",
            pygame.K_3: "rapid",   pygame.K_4: "artillery",
            pygame.K_5: "laser",   pygame.K_6: "frost",
            pygame.K_0: None,
        }
        if key in tower_keys:
            self.selected_tower_type = tower_keys[key]
            self.abilities.pending = None

        utility_keys = {
            pygame.K_m: "meteor", pygame.K_f: "freeze",
            pygame.K_g: "gold_rush", pygame.K_h: "repair",
        }
        if key in utility_keys:
            ability_key = utility_keys[key]
            if self.abilities.can_use(ability_key, self.money):
                if ability_key == "meteor":
                    self.abilities.activate_targeted(ability_key)
                else:
                    self.abilities.activate_instant(ability_key)
                    self._execute_ability(ability_key)

    def _handle_playing_click(self, mx: int, my: int) -> None:
        if self.game_over or self.victory:
            return
        if mx < GAME_WIDTH:
            self._handle_game_area_click(mx, my)
        else:
            self._handle_ui_click(mx, my, GAME_WIDTH)

    def _handle_game_area_click(self, mx: int, my: int) -> None:
        pending = self.abilities.consume_pending()
        if pending == "meteor":
            self._execute_ability("meteor", mx, my)
            return
        for tower in self.towers:
            tower.selected = False
        clicked = next(
            (t for t in self.towers if math.hypot(mx - t.x, my - t.y) < TOWER_CLICK_RADIUS),
            None,
        )
        if clicked:
            clicked.selected = True
            self.selected_tower_obj = clicked
        else:
            self.selected_tower_obj = None
            if self.selected_tower_type:
                cost = TOWER_TYPES[self.selected_tower_type]["cost"]
                if self._is_position_valid(mx, my) and self.money >= cost:
                    # Apply global damage & fire rate bonuses to new towers
                    t = Tower(mx, my, self.selected_tower_type)
                    gu = self.upgrades
                    t.damage    *= (1.0 + gu.tower_damage_mult_bonus)
                    t.fire_rate  = max(1, int(t.fire_rate * (1.0 - gu.fire_rate_reduction)))
                    self.towers.append(t)
                    self.money -= cost

    def _handle_ui_click(self, mx: int, my: int, sx: int) -> None:
        # Wave button: y 94-128
        if sx + 20 <= mx <= sx + 220 and 94 <= my <= 128:
            if self.wave_mgr.is_ready_for_next_wave:
                self.wave_mgr.start_next_wave()
            return

        # Ability buttons: always checked first, fixed position
        if self._handle_utility_click(mx, my, sx):
            return

        # Shop or tower upgrade panel below abilities
        if self.selected_tower_obj:
            self._handle_upgrade_click(mx, my, sx)
        else:
            self._handle_shop_click(mx, my, sx)

    def _handle_upgrade_click(self, mx: int, my: int, sx: int) -> None:
        y0 = _SHOP_START_Y
        t = self.selected_tower_obj
        u_cost = int(TOWER_TYPES[t.type]["cost"] * 0.9 * t.level)

        if t.level < 3 and sx + 20 <= mx <= sx + 220 and y0 + 74 <= my <= y0 + 112:
            if self.money >= u_cost and t.level < self.current_level_id + 1:
                self.money -= u_cost
                t.upgrade()
        elif t.level == 3:
            for i, branch in enumerate(["A", "B", "C"]):
                y = y0 + 80 + i * 44
                if sx + 20 <= mx <= sx + 220 and y <= my <= y + 36:
                    if self.money >= 200:
                        self.money -= 200
                        t.upgrade(branch)

        desel_y = y0 + 210
        if sx + 20 <= mx <= sx + 220 and desel_y <= my <= desel_y + 32:
            self.selected_tower_obj = None

    def _handle_shop_click(self, mx: int, my: int, sx: int) -> None:
        y_off = _SHOP_START_Y + 20
        for t_name in TOWER_TYPES:
            if sx + 15 <= mx <= sx + 225 and y_off <= my <= y_off + 36:
                self.selected_tower_type = t_name
                return
            y_off += 40
        if sx + 15 <= mx <= sx + 225 and y_off <= my <= y_off + 30:
            self.selected_tower_type = None

    def _handle_utility_click(self, mx: int, my: int, sx: int) -> bool:
        """
        Check if the click lands on an ability button.
        Returns True if a button was hit (so caller can stop processing).
        Uses only module-level constants — identical to draw code.
        """
        for i, key in enumerate(ABILITY_ORDER):
            col_i = i % 2
            row_i = i // 2
            bx = _UTIL_X + col_i * (_UTIL_BTN_W + _UTIL_BTN_GAP)
            by = _UTIL_Y + row_i * (_UTIL_BTN_H + _UTIL_BTN_GAP)

            if bx <= mx <= bx + _UTIL_BTN_W and by <= my <= by + _UTIL_BTN_H:
                if self.abilities.can_use(key, self.money):
                    if key == "meteor":
                        self.abilities.activate_targeted(key)
                    else:
                        self.abilities.activate_instant(key)
                        self._execute_ability(key)
                return True   # consumed, even if can't afford — don't fall through
        return False

    # ==================================================================
    # Placement validation
    # ==================================================================

    def _precompute_valid_positions(self) -> None:
        self.valid_grid = [[True] * HEIGHT for _ in range(GAME_WIDTH)]
        for x in range(GAME_WIDTH):
            for y in range(HEIGHT):
                if x >= GAME_WIDTH - 20 or x < 20 or y < 20 or y > HEIGHT - 20:
                    self.valid_grid[x][y] = False
                    continue
                for i in range(len(self.path) - 1):
                    p1 = (self.path[i][0]     * TILE + TILE // 2,
                          self.path[i][1]     * TILE + TILE // 2)
                    p2 = (self.path[i + 1][0] * TILE + TILE // 2,
                          self.path[i + 1][1] * TILE + TILE // 2)
                    if self._dist_to_segment((x, y), p1, p2) < PATH_CLEARANCE:
                        self.valid_grid[x][y] = False

    def _is_position_valid(self, x: float, y: float) -> bool:
        ix, iy = int(x), int(y)
        if ix < 0 or ix >= GAME_WIDTH or iy < 0 or iy >= HEIGHT:
            return False
        if not self.valid_grid[ix][iy]:
            return False
        return all(
            (x - t.x) ** 2 + (y - t.y) ** 2 >= TOWER_SPACING ** 2
            for t in self.towers
        )

    @staticmethod
    def _dist_to_segment(p: tuple, a: tuple, b: tuple) -> float:
        px, py = p
        ax, ay = a
        bx, by = b
        seg_sq = (ax - bx) ** 2 + (ay - by) ** 2
        if seg_sq == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / seg_sq))
        return math.hypot(px - (ax + t * (bx - ax)), py - (ay + t * (by - ay)))

    # ==================================================================
    # Main loop
    # ==================================================================

    def run(self) -> None:
        while True:
            mx, my = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.state == "MENU":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self._handle_menu_click(mx, my)
                    if event.type == pygame.KEYDOWN:
                        self._handle_menu_keydown(event.key)

                elif self.state == "UPGRADES":
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self._handle_upgrades_click(mx, my)

                elif self.state == "PLAYING":
                    if event.type == pygame.KEYDOWN:
                        self._handle_playing_keydown(event.key)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self._handle_playing_click(mx, my)

            if self.state == "MENU":
                self._draw_menu()
            elif self.state == "UPGRADES":
                self._draw_upgrades()
            else:
                self._update_playing()
                self._draw_playing()

            self.clock.tick(60)


if __name__ == "__main__":
    Game().run()