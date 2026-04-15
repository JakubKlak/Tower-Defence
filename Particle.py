import pygame
import random

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.color = color
        self.vel_x = random.uniform(-2.5, 2.5)
        self.vel_y = random.uniform(-2.5, 2.5)
        self.radius = random.uniform(2, 5)
        self.reached = False

    def move(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.radius -= 0.15
        if self.radius <= 0: self.reached = True

    def draw(self, screen):
        if self.radius > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.radius))
"""
A single short-lived visual particle used for hit effects.
"""

import pygame
import random

# Particle spawn velocity range (pixels per frame)
_VEL_RANGE: float = 2.5
# How fast the radius shrinks each frame
_SHRINK_RATE: float = 0.15


class Particle:
    """Drifting circle that shrinks and disappears over time."""

    def __init__(self, x: float, y: float, color: tuple):
        """
        Args:
            x, y:  Spawn position in pixels.
            color: RGB tuple.
        """
        self.x = x
        self.y = y
        self.color = color
        self.vel_x: float = random.uniform(-_VEL_RANGE, _VEL_RANGE)
        self.vel_y: float = random.uniform(-_VEL_RANGE, _VEL_RANGE)
        self.radius: float = random.uniform(2.0, 5.0)
        self.reached: bool = False  # True once fully faded (matches Projectile naming)

    def move(self) -> None:
        """Drift and shrink the particle by one frame."""
        self.x += self.vel_x
        self.y += self.vel_y
        self.radius -= _SHRINK_RATE
        if self.radius <= 0:
            self.reached = True

    def draw(self, screen: pygame.Surface) -> None:
        if self.radius > 0:
            pygame.draw.circle(
                screen, self.color, (int(self.x), int(self.y)), int(self.radius)
            )