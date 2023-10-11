from __future__ import annotations
from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from game import Game


class PhysicsEntity:
    def __init__(self, game: Game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)  # make a copy, if not, will be reference
        self.size = list(size)  # make a copy, if not, will be reference
        self.velocity = [0.0, 0.0]

    def update(self, movement=(0, 0)):
        frame_movement = (
            movement[0] + self.velocity[0],
            movement[1] + self.velocity[1],
        )
        self.pos[0] += frame_movement[0]
        self.pos[1] += frame_movement[1]

        self.velocity[1] = min(5.0, self.velocity[1] + 0.1)

    def render(self, surf: pygame.Surface):
        surf.blit(self.game.assets["player"], self.pos)
