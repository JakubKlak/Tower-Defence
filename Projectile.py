"""
Represents a projectile fired by a tower at a target enemy.
"""

import pygame
import math

PROJECTILE_RADIUS: int = 5


class Projectile:
    """A homing projectile that disappears on impact or when the target dies."""

    def __init__(self, x: float, y: float, target, damage: float,
                 speed: float, color: tuple, effect: str | None = None):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.speed = speed
        self.color = color
        self.effect = effect
        self.reached: bool = False

    def move(self) -> bool:
        """
        Advance one frame toward the target.

        Returns:
            True  — hit the target (apply damage).
            False — still in flight, or target already dead.
        """
        if not self.target.is_alive:
            self.reached = True
            return False

        tx, ty = self.target.center
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)

        if dist < self.speed:
            self.reached = True
            return True

        self.x += self.speed * dx / dist
        self.y += self.speed * dy / dist
        return False

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, self.color,
                           (int(self.x), int(self.y)), PROJECTILE_RADIUS)