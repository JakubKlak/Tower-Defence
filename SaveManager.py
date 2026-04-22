"""
SaveManager — persistent save/load for Tower Defence.

Save file location:  ./save.json  (next to the game files)

What is saved (only the session-persistent data — not mid-level state):
    - unlocked_levels  (set of ints)
    - upgrades.points  (int)
    - upgrades.purchased (set of strings)
    - save_version     (int, for future compatibility)

Mid-level state (towers, enemies, wave progress) is intentionally NOT
saved — the save represents campaign progress, not a mid-game snapshot.
If the player quits mid-level they restart that level from scratch.
"""

import json
import os

SAVE_FILE    = "save.json"
SAVE_VERSION = 2   # bumped because we added completed_levels


def save_game(unlocked_levels: set, upgrades, completed_levels: set) -> bool:
    """
    Write campaign progress to save.json.

    Args:
        unlocked_levels:  set of level IDs the player has access to.
        upgrades:         GlobalUpgrades instance.
        completed_levels: set of level IDs finished at least once (used to
                          prevent earning upgrade points more than once per level).

    Returns:
        True on success, False if the file could not be written.
    """
    data = {
        "save_version":      SAVE_VERSION,
        "unlocked_levels":   sorted(unlocked_levels),
        "completed_levels":  sorted(completed_levels),
        "upgrade_points":    upgrades.points,
        "upgrades_bought":   sorted(upgrades.purchased),
    }
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except OSError:
        return False


def load_game(upgrades) -> dict | None:
    """
    Read campaign progress from save.json.

    Args:
        upgrades: GlobalUpgrades instance — will be mutated in-place.

    Returns:
        dict with keys 'unlocked' (set[int]) and 'completed' (set[int])
        on success, or None if no save file exists / file is corrupted.
    """
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("save_version", 0) != SAVE_VERSION:
            return None

        unlocked  = set(int(x) for x in data.get("unlocked_levels", [1]))
        unlocked.add(1)
        completed = set(int(x) for x in data.get("completed_levels", []))

        upgrades.points    = int(data.get("upgrade_points", 0))
        upgrades.purchased = set(data.get("upgrades_bought", []))

        return {"unlocked": unlocked, "completed": completed}

    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def delete_save() -> bool:
    """
    Delete the save file (used by the 'New Game' button).

    Returns True if the file was deleted or didn't exist.
    """
    try:
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
        return True
    except OSError:
        return False


def save_exists() -> bool:
    """True if a save file is present on disk."""
    return os.path.exists(SAVE_FILE)