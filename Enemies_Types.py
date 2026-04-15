"""
Defines all enemy types and their base statistics.

Standard keys (all types):
    hp, speed, reward, color, damage

Ability keys (only on types that have abilities):
    ability          — string identifier for the ability
    ability_cooldown — frames between ability triggers

Per-ability extra keys:
    heal_amount, heal_radius  (healer)
    immune_duration           (ghost)
    berserk_speed_mult        (berserker)
    split_type, split_count   (splitter)
"""

ENEMY_TYPES: dict[str, dict] = {
    # ------------------------------------------------------------------
    # Original types
    # ------------------------------------------------------------------
    "basic": {
        "hp": 100, "speed": 2, "reward": 10,
        "color": (200, 50, 50), "damage": 1,
    },
    "fast": {
        "hp": 60, "speed": 4, "reward": 12,
        "color": (50, 200, 50), "damage": 2,
    },
    "scout": {
        "hp": 40, "speed": 5, "reward": 15,
        "color": (150, 255, 150), "damage": 4,
    },
    "tank": {
        "hp": 250, "speed": 1, "reward": 25,
        "color": (50, 50, 200), "damage": 5,
    },
    "heavy": {
        "hp": 600, "speed": 0.8, "reward": 50,
        "color": (100, 100, 100), "damage": 6,
    },
    "glass_cannon": {
        "hp": 20, "speed": 6, "reward": 100,
        "color": (255, 255, 255), "damage": 4,
    },
    "boss": {
        "hp": 1500, "speed": 1, "reward": 250,
        "color": (255, 100, 0), "damage": 15,
    },

    # ------------------------------------------------------------------
    # New ability enemies
    # ------------------------------------------------------------------

    # Healer: slow and fragile but periodically heals nearby allies.
    # Kill it first — it can undo a lot of tower damage.
    "healer": {
        "hp": 90, "speed": 1.2, "reward": 30,
        "color": (0, 220, 120), "damage": 2,
        "ability": "heal",
        "ability_cooldown": 120,   # heals every 2 seconds (at 60 fps)
        "heal_amount": 40,
        "heal_radius": 110,
    },

    # Ghost: cycles between a vulnerable phase and a 60-frame immunity phase.
    # Projectiles pass right through while immune; drawn semi-transparent.
    "ghost": {
        "hp": 130, "speed": 3.0, "reward": 35,
        "color": (180, 180, 255), "damage": 3,
        "ability": "ghost",
        "ability_cooldown": 200,   # enters immunity every 200 frames
        "immune_duration": 60,     # immunity lasts 60 frames (1 second)
    },

    # Berserker: unremarkable until wounded. Dropping below 50 % HP
    # permanently doubles its speed. Changes color to signal the berserk.
    "berserker": {
        "hp": 200, "speed": 1.8, "reward": 40,
        "color": (200, 40, 10), "damage": 5,
        "ability": "berserk",
        "berserk_speed_mult": 2.2,
    },

    # Splitter: spawns two fast enemies when killed.
    # Drawn gold so players know to expect the split.
    "splitter": {
        "hp": 160, "speed": 1.5, "reward": 20,
        "color": (255, 210, 30), "damage": 3,
        "ability": "split",
        "split_type": "fast",
        "split_count": 2,
    },
}

VALID_ENEMY_TYPES: frozenset[str] = frozenset(ENEMY_TYPES.keys())