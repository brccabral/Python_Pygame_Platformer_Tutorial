from __future__ import annotations
from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from game import Game


class Tilemap:
    def __init__(self, game: Game, tile_size=16):
        self.tile_size = tile_size
        self.game = game
        self.tilemap = {}
        self.offgrid_tiles = []

        for i in range(10):
            # the key is str() because the way the tiles are saved
            # we keep "pos" as tuple to handle calculations later
            self.tilemap[str(3 + i) + ";10"] = {
                "type": "grass",
                "variant": 1,
                "pos": (3 + i, 10),
            }
            self.tilemap["10;" + str(5 + i)] = {
                "type": "stone",
                "variant": 1,
                "pos": (10, 5 + i),
            }

    def render(self, surf: pygame.Surface):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile["type"]][tile["variant"]], tile["pos"])
        for loc, tile in self.tilemap.items():
            surf.blit(
                self.game.assets[tile["type"]][tile["variant"]],
                (tile["pos"][0] * self.tile_size, tile["pos"][1] * self.tile_size),
            )
