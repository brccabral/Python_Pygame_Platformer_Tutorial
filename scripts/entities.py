from __future__ import annotations
from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from game import Game
    from scripts.tilemap import Tilemap


class PhysicsEntity:
    def __init__(self, game: Game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)  # make a copy, if not, will be reference
        self.size = list(size)  # make a copy, if not, will be reference
        self.velocity = [0.0, 0.0]

    def update(self, tilemap: Tilemap, movement=(0, 0)):
        frame_movement = (
            movement[0] + self.velocity[0],
            movement[1] + self.velocity[1],
        )
        self.pos[0] += frame_movement[0]
        # collision on X axis
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                # pygame Rect() only deals with Integers
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]
        # collision on Y axis
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                # pygame Rect() only deals with Integers
                self.pos[1] = entity_rect.y

        self.velocity[1] = min(5.0, self.velocity[1] + 0.1)

    def render(self, surf: pygame.Surface):
        surf.blit(self.game.assets["player"], self.pos)

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
