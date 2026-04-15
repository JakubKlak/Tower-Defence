"""
Player-activated abilities (utilities / power-ups).

All four abilities now have cooldowns so they can't be spammed.
The GlobalUpgrades cooldown_reduction bonus is respected via
AbilityManager.set_cooldown_reduction().

Cooldown values (at base, no upgrades):
  Meteor    — 25 s  (1500 frames)
  Freeze    — 20 s  (1200 frames)
  Gold Rush — 15 s  (900  frames)  + 6 s active window
  Repair    — 30 s  (1800 frames)
"""

ABILITY_DEFS: dict[str, dict] = {
    "meteor": {
        "name": "Meteor Rain",
        "key_hint": "M",
        "cost": 0,
        "base_cooldown": 1500,
        "radius": 90,
        "damage": 300,
        "particle_count": 45,
        "color": (255, 120, 0),
        "description": "Click to deal 300 AoE dmg  (25 s CD)",
    },
    "freeze": {
        "name": "Freeze Bomb",
        "key_hint": "F",
        "cost": 0,
        "base_cooldown": 1200,
        "slow_frames": 240,
        "color": (100, 200, 255),
        "description": "Slow ALL enemies 4 s  (20 s CD)",
    },
    "gold_rush": {
        "name": "Gold Rush",
        "key_hint": "G",
        "cost": 0,
        "base_cooldown": 900,
        "active_frames": 360,
        "reward_mult": 2,
        "color": (255, 215, 0),
        "description": "x2 rewards 6 s  (15 s CD)",
    },
    "repair": {
        "name": "Repair",
        "key_hint": "H",
        "cost": 0,
        "base_cooldown": 1800,
        "heal_hp": 5,
        "color": (0, 255, 100),
        "description": "Restore 5 HP  (30 s CD)",
    },
}

ABILITY_ORDER: list[str] = ["meteor", "freeze", "gold_rush", "repair"]
FPS: int = 60


class AbilityManager:
    """
    Tracks cooldowns and active-effect timers for all player abilities.

    Call set_cooldown_reduction(fraction) once after creating the instance
    to apply the GlobalUpgrades "Quick Reload" bonus.

    Attributes:
        pending (str | None): Ability waiting for a click-to-target (meteor).
    """

    def __init__(self, max_base_hp: int):
        self.max_base_hp = max_base_hp
        self._reduction: float = 0.0   # set by set_cooldown_reduction()
        self.cooldowns: dict[str, int] = {k: 0 for k in ABILITY_DEFS}
        self._gold_rush_timer: int = 0
        self.pending: str | None = None

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def set_cooldown_reduction(self, reduction: float) -> None:
        """
        Apply a persistent cooldown reduction (0.0–0.60).
        Call once after __init__ with GlobalUpgrades.cooldown_reduction.
        """
        self._reduction = max(0.0, min(0.60, reduction))

    def _effective_cooldown(self, key: str) -> int:
        """Return the actual cooldown in frames after applying reduction."""
        base = ABILITY_DEFS[key]["base_cooldown"]
        return max(1, int(base * (1.0 - self._reduction)))

    # ------------------------------------------------------------------
    # Per-frame update
    # ------------------------------------------------------------------

    def update(self) -> None:
        for key in self.cooldowns:
            if self.cooldowns[key] > 0:
                self.cooldowns[key] -= 1
        if self._gold_rush_timer > 0:
            self._gold_rush_timer -= 1

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    @property
    def gold_rush_active(self) -> bool:
        return self._gold_rush_timer > 0

    @property
    def reward_multiplier(self) -> int:
        return ABILITY_DEFS["gold_rush"]["reward_mult"] if self.gold_rush_active else 1

    def cost(self, key: str) -> int:
        return ABILITY_DEFS[key]["cost"]

    def can_use(self, key: str, money: int) -> bool:
        if self.cooldowns[key] > 0:
            return False
        if money < ABILITY_DEFS[key]["cost"]:
            return False
        if key == "gold_rush" and self.gold_rush_active:
            return False
        return True

    def cooldown_fraction(self, key: str) -> float:
        """0.0 = ready, 1.0 = just started cooldown.  Used for the overlay bar."""
        total = self._effective_cooldown(key)
        if total == 0:
            return 0.0
        return self.cooldowns[key] / total

    def cooldown_seconds_remaining(self, key: str) -> float:
        """Remaining cooldown expressed in seconds (for display)."""
        return self.cooldowns[key] / FPS

    # ------------------------------------------------------------------
    # Activation
    # ------------------------------------------------------------------

    def activate_instant(self, key: str) -> None:
        """Start cooldown for a non-targeted ability."""
        self.cooldowns[key] = self._effective_cooldown(key)
        if key == "gold_rush":
            self._gold_rush_timer = ABILITY_DEFS["gold_rush"]["active_frames"]

    def activate_targeted(self, key: str) -> None:
        """Mark ability as pending — fires when player clicks the map."""
        self.pending = key

    def consume_pending(self) -> str | None:
        """Called when the player clicks the game area.  Returns key or None."""
        key = self.pending
        if key:
            self.pending = None
            self.cooldowns[key] = self._effective_cooldown(key)
        return key