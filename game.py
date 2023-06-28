#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Author      : Bluzy
Date        : 2023/06/26 14:28:59
Contact     : zoe4896@outlook.com
Description : 
'''
import pygame
import random
import numpy as np
from world import World
from entity import EntityManager
from component import PositionComponent, ShapeComponent, ColorComponent, SpeedComponent, StateComponent, MapComponent
from system import InputSystem, MovementSystem, CollisionSystem, ClearLinesSystem, RenderSystem, MapSystem

# 游戏常量
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
BLOCK_SIZE = 30
PLAYFIELD_WIDTH = 10
PLAYFIELD_HEIGHT = 20
SCOREBOARD_WIDTH = 100
SCOREBOARD_HEIGHT = 250
FPS = 60
FALL_SPEED = 1000   # ms

# 游戏类
class Game:
    def __init__(self):
        pygame.init()
        world = World(PLAYFIELD_WIDTH, PLAYFIELD_HEIGHT)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), vsync=True)
        self.play_field = pygame.Surface((PLAYFIELD_WIDTH, PLAYFIELD_HEIGHT))
        self.score_board = pygame.Surface((SCOREBOARD_WIDTH, SCOREBOARD_HEIGHT))
        pygame.display.set_caption("The Cube")
        self.clock = pygame.time.Clock()
        self.running = True
        self.fall_time = 0
        self.entity_manager = EntityManager()

        self.systems = [
            InputSystem(),
            MovementSystem(),
            CollisionSystem(world.playfield_width, world.playfield_height),
            ClearLinesSystem(),
            RenderSystem(self.screen, self.play_field, self.score_board, BLOCK_SIZE),
            MapSystem(world.mat)
        ]

        self.shapes = [
            [[1, 1, 1, 1]],
            [[1, 1], [1, 1]],
            [[1, 0, 0], [1, 1, 1]],
            [[0, 0, 1], [1, 1, 1]],
            [[0, 1, 1], [1, 1, 0]],
            [[1, 1, 0], [0, 1, 1]],
            [[0, 1, 0], [1, 1, 1]]
        ]
        self.init_map()
        self.spawn_block()

    def spawn_block(self):
        # shape = random.choice(self.shapes)
        shape = self.shapes[0]

        entity = self.entity_manager.create_entity()
        entity.add_component(PositionComponent(PLAYFIELD_WIDTH // 2 - len(shape[0]) // 2, 0))
        entity.add_component(SpeedComponent(0, 5))
        entity.add_component(ShapeComponent(shape))
        entity.add_component(ColorComponent())
        entity.add_component(StateComponent())
    
    def init_map(self):
        map_entity = self.entity_manager.create_entity()
        map_entity.add_component(MapComponent(np.zeros((PLAYFIELD_HEIGHT, PLAYFIELD_WIDTH), dtype=np.int0)))

    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT or event.type == pygame.USEREVENT + 2:
                self.running = False
            if event.type == pygame.USEREVENT + 1:
                self.systems[5].process(self.entity_manager.entities)
                self.systems[3].process(self.entity_manager.entities)

                self.spawn_block()
            else:
                continue

        self.systems[0].process(events, self.entity_manager.entities)

    def update(self):
        self.systems[2].process(self.entity_manager.entities)
        current_time = pygame.time.get_ticks()
        if current_time - self.fall_time >= FALL_SPEED:
            self.systems[1].process(self.entity_manager.entities)
            self.fall_time = current_time

    def render(self):
        self.systems[4].process(self.entity_manager.entities)

        pygame.display.flip()
        self.clock.tick(FPS)

    def run(self):
        # self.running = True
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        pygame.quit()