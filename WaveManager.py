"""
Manages enemy wave progression for the Tower Defence game.
"""

import random
from Enemies_Types import VALID_ENEMY_TYPES

# ---------------------------------------------------------------------------
# Wave composition table
# Each entry: (min_wave, [(enemy_type, weight), ...])
# New types unlock as the wave number increases.
# ---------------------------------------------------------------------------
_WAVE_UNLOCKS: list[tuple[int, list[tuple[str, int]]]] = [
    (1,  [("basic", 8)]),                                    # wave 1-3: basics only
    (4,  [("fast", 3), ("scout", 2)]),                       # wave 4+: faster enemies
    (6,  [("healer", 1)]),                                   # wave 6+: healer (rare)
    (7,  [("tank", 2)]),                                     # wave 7+: first tanks
    (9,  [("heavy", 1), ("berserker", 2)]),                  # wave 9+: beefy
    (12, [("ghost", 2), ("splitter", 2)]),                   # wave 12+: tricky
    (15, [("glass_cannon", 2)]),                             # wave 15+: endgame
]

# Validate at import time — catches typos immediately
for _wave, _entries in _WAVE_UNLOCKS:
    for _etype, _ in _entries:
        assert _etype in VALID_ENEMY_TYPES, (
            f"Unknown enemy type '{_etype}' in _WAVE_UNLOCKS"
        )


class WaveManager:
    """Handles wave sequencing, enemy queuing, and spawn timing."""

    def __init__(self, difficulty: float = 1.0, max_waves: int = 3):
        """
        Args:
            difficulty: Scales enemy count and spawn speed (1.0 = normal).
            max_waves:  Total waves before the level ends.
        """
        self.difficulty = difficulty
        self.max_waves = max_waves

        self.current_wave: int = 0
        self.enemies_to_spawn: list[str] = []
        self.spawn_timer: int = 0
        # spawn_delay is recalculated per wave in start_next_wave()
        self.spawn_delay: int = max(15, int(60 / difficulty))
        self.wave_active: bool = False
        self.wave_finished: bool = False

        # Optional callback: mgr.on_all_waves_done = my_function
        self.on_all_waves_done = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def all_waves_done(self) -> bool:
        return self.wave_finished

    @property
    def waves_remaining(self) -> int:
        return max(0, self.max_waves - self.current_wave)

    @property
    def is_ready_for_next_wave(self) -> bool:
        return not self.enemies_to_spawn and not self.wave_finished

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_next_wave(self) -> bool:
        """Start the next wave. Returns False if all waves are done."""
        if self.current_wave >= self.max_waves:
            return False
        self.current_wave += 1
        self.wave_active = True
        self.wave_finished = False

        # Spawn delay shrinks as waves progress — early waves feel calm,
        # later waves are relentless.  Clamped to a minimum of 12 frames.
        wave_factor = max(0.5, 1.0 - (self.current_wave - 1) * 0.04)
        self.spawn_delay = max(12, int((60 / self.difficulty) * wave_factor))

        self.enemies_to_spawn = self._build_wave_enemies()
        return True

    def update(self) -> str | None:
        """
        Advance one game tick.
        Returns an enemy-type string when it's time to spawn, else None.
        """
        if not self.wave_active:
            return None

        if self.enemies_to_spawn:
            self.spawn_timer += 1
            if self.spawn_timer >= self.spawn_delay:
                self.spawn_timer = 0
                return self.enemies_to_spawn.pop(0)
        else:
            self._finish_wave()

        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_wave_pool(self) -> list[str]:
        pool: list[str] = []
        for min_wave, entries in _WAVE_UNLOCKS:
            if self.current_wave >= min_wave:
                for etype, weight in entries:
                    pool.extend([etype] * weight)
        return pool

    def _build_wave_enemies(self) -> list[str]:
        pool = self._build_wave_pool()

        # Gentler ramp: wave 1 → 4 enemies, growing slowly at first then faster.
        # Formula:  3 + wave + floor(wave² / 6)
        # Wave  1 →  4,  2 →  5,  3 →  6,  4 →  8,  5 → 10,
        #       6 → 12,  8 → 16, 10 → 20, 15 → 30
        base_count = 3 + self.current_wave + (self.current_wave ** 2) // 6
        count = max(3, int(base_count * self.difficulty))

        enemies = [random.choice(pool) for _ in range(count)]
        if self.current_wave % 5 == 0:
            enemies.append("boss")
        return enemies

    def _finish_wave(self) -> None:
        self.wave_active = False
        if self.current_wave >= self.max_waves:
            self.wave_finished = True
            if callable(self.on_all_waves_done):
                self.on_all_waves_done()