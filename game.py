import sys
import pygame
import random
import math

from typing import Union

from scripts.entities import Player, Enemy
from scripts.utils import load_image, load_images, Animation
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Ninja Game")

        self.screen = pygame.display.set_mode((640, 480))
        # the game will draw in half resolution and then scaled up
        # to give more impression of a pixel art game
        self.display = pygame.Surface((320, 240))
        self.clock = pygame.time.Clock()

        self.movement = [False, False]

        self.assets = {
            "player": load_image("entities/player.png"),
            "decor": load_images("tiles/decor"),
            "grass": load_images("tiles/grass"),
            "large_decor": load_images("tiles/large_decor"),
            "stone": load_images("tiles/stone"),
            "background": load_image("background.png"),
            "gun": load_image("gun.png"),
            "projectile": load_image("projectile.png"),
            "clouds": load_images("clouds"),
            "player/idle": Animation(load_images("entities/player/idle"), 6),
            "player/jump": Animation(load_images("entities/player/jump")),
            "player/run": Animation(load_images("entities/player/run"), 4),
            "player/slide": Animation(load_images("entities/player/slide")),
            "player/wall_slide": Animation(load_images("entities/player/wall_slide")),
            "enemy/idle": Animation(load_images("entities/enemy/idle"), 6),
            "enemy/run": Animation(load_images("entities/enemy/run"), 4),
            # at the end of the animation loop, stop looping. Particles are marked for
            # deleting at the end of Animation
            "particle/leaf": Animation(load_images("particles/leaf"), 20, False),
            "particle/particle": Animation(load_images("particles/particle"), 6, False),
        }
        self.player = Player(self, (50, 50), (8, 15))
        self.dead = 0

        self.tilemap = Tilemap(self)

        # camera
        self.scroll = [0.0, 0.0]
        self.screenshake = 0

        self.clouds = Clouds(self.assets["clouds"], 1)

        self.leaf_spawners = []
        self.enemies = []
        self.particles: list[Particle] = []
        self.sparks: list[Spark] = []
        # [[x, y], direction, timer]
        self.projectiles: list[list[Union[tuple[float, float], float]]] = []

        self.level = 0
        # transition < 0 - black to clear
        # transition > 0 - clear to black
        self.transition = 0
        self.load_level(self.level)

        self.font = pygame.font.SysFont("comicsans", 30)

    def run(self):
        while True:
            # clear screen
            self.display.blit(self.assets["background"], (0, 0))

            self.screenshake = max(0, self.screenshake - 1)

            if not len(self.enemies):
                self.transition += 1
                # load new level when it is complete black
                if self.transition > 30:
                    self.level += 1
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1

            # gives 40 frames to player disapear before reload level
            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(self.transition + 1, 30)
                if self.dead > 40:
                    self.load_level(self.level)

            # update camera to follow player with delay
            self.scroll[0] += (
                self.player.rect().centerx
                - self.display.get_width() / 2
                - self.scroll[0]
            ) / 30
            self.scroll[1] += (
                self.player.rect().centery
                - self.display.get_height() / 2
                - self.scroll[1]
            ) / 30
            render_scroll = int(self.scroll[0]), int(self.scroll[1])

            for rect in self.leaf_spawners:
                # probability of spawning
                # larger spawners will spawn more
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (
                        rect.x + random.random() * rect.width,
                        rect.y + random.random() * rect.height,
                    )
                    # spawn a leaf moving down and a little left
                    # starts in a random frame variant
                    self.particles.append(
                        Particle(
                            self,
                            "leaf",
                            pos,
                            velocity=[-0.1, 0.3],
                            frame=random.randint(0, 20),
                        )
                    )

            self.clouds.update()
            self.clouds.render(self.display, render_scroll)

            self.tilemap.render(self.display, offset=render_scroll)

            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            if not self.dead:
                self.player.update(
                    self.tilemap, (self.movement[1] - self.movement[0], 0)
                )
                self.player.render(self.display, offset=render_scroll)

            # [[x, y], direction, timer]
            for projectile in self.projectiles:
                projectile[0] = projectile[0][0] + projectile[1], projectile[0][1]
                projectile[2] += 1.0
                img = self.assets["projectile"]
                self.display.blit(
                    img,
                    (
                        projectile[0][0] - img.get_width() / 2 - render_scroll[0],
                        projectile[0][1] - img.get_height() / 2 - render_scroll[1],
                    ),
                )
                # projectile hits wall
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(
                            Spark(
                                projectile[0],
                                # check if wall is left or right
                                random.random()
                                - 0.5
                                + (math.pi if projectile[1] > 0 else 0),
                                2 + random.random(),
                            )
                        )
                # projectile timeout
                elif projectile[2] > 360.0:
                    self.projectiles.remove(projectile)
                # projectile hits player when player is not invencible
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.screenshake = max(16, self.screenshake)
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(
                                Spark(
                                    self.player.rect().center,
                                    angle,
                                    speed,
                                )
                            )
                            self.particles.append(
                                Particle(
                                    self,
                                    "particle",
                                    self.player.rect().center,
                                    velocity=[
                                        math.cos(angle + math.pi) * speed * 0.5,
                                        math.sin(angle + math.pi) * speed * 0.5,
                                    ],
                                    frame=random.randint(0, 7),
                                )
                            )

            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, render_scroll)
                if kill:
                    self.sparks.remove(spark)

            for particle in self.particles.copy():
                particle.render(self.display, render_scroll)
                # move leaf left/right, although the velocity is a little to the left
                if particle.type == "leaf":
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if particle.update():
                    self.particles.remove(particle)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # keyboard events
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.player.jump()
                    if event.key == pygame.K_l:
                        self.player.dash()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False

            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(
                    transition_surf,
                    "white",
                    self.display.get_rect().center,
                    (30 - abs(self.transition)) * 8,
                )
                transition_surf.set_colorkey("white")
                self.display.blit(transition_surf, (0, 0))

            screenshake_offset = (
                random.random() * self.screenshake - self.screenshake / 2,
                random.random() * self.screenshake - self.screenshake / 2,
            )
            self.screen.blit(
                pygame.transform.scale(self.display, self.screen.get_size()),
                screenshake_offset,
            )

            # debug = self.font.render("Dash " + str(self.player.dashing), 1, "black")
            # self.screen.blit(debug, (10, 10))

            pygame.display.update()
            self.clock.tick(60)

    def load_level(self, map_id):
        self.tilemap.load("data/maps/" + str(map_id) + ".json")

        self.dead = 0

        self.leaf_spawners = []
        for tree in self.tilemap.extract([("large_decor", 2)], keep=True):
            self.leaf_spawners.append(
                pygame.Rect(4 + tree["pos"][0], 4 + tree["pos"][1], 23, 13)
            )

        self.enemies = []
        for spawner in self.tilemap.extract([("spawners", 0), ("spawners", 1)]):
            if spawner["variant"] == 0:
                self.player.pos = spawner["pos"]
                self.player.air_time = 0
                self.player.velocity = [0.0, 0.0]
                self.player.flip = False
            else:
                self.enemies.append(Enemy(self, spawner["pos"], (8, 15)))

        self.particles: list[Particle] = []
        # [[x, y], direction, timer]
        self.projectiles: list[list[Union[tuple[float, float], float]]] = []

        # camera
        self.scroll = [0.0, 0.0]

        self.clouds = Clouds(self.assets["clouds"], 16)

        self.transition = -30


Game().run()
