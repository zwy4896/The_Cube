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

# 游戏类
class Game:
    def __init__(self, cfg):
        pygame.init()
        self.cfg = cfg
        self.get_params()
        world = World(self.PLAYFIELD_WIDTH, self.PLAYFIELD_HEIGHT)
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), vsync=True)
        self.play_field = pygame.Surface((self.PLAYFIELD_WIDTH, self.PLAYFIELD_HEIGHT))
        self.score_board = pygame.Surface((self.SCOREBOARD_WIDTH, self.SCOREBOARD_HEIGHT))
        pygame.display.set_caption("The Cube")
        self.clock = pygame.time.Clock()
        self.running = True
        self.fall_time = 0
        self.entity_manager = EntityManager()

        self.systems = {
            'InputSystem': InputSystem(),
            'MovementSystem': MovementSystem(),
            'CollisionSystem': CollisionSystem(world.playfield_width, world.playfield_height),
            'ClearLinesSystem': ClearLinesSystem(),
            'RenderSystem': RenderSystem(self.screen, self.play_field, self.score_board, self.BLOCK_SIZE),
            'MapSystem': MapSystem(world.mat)
        }

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

    def get_params(self):
        # 游戏常量
        self.SCREEN_WIDTH = self.cfg['SCREEN_WIDTH']
        self.SCREEN_HEIGHT = self.cfg['SCREEN_HEIGHT']
        self.BLOCK_SIZE = self.cfg['BLOCK_SIZE']
        self.PLAYFIELD_WIDTH = self.cfg['PLAYFIELD_WIDTH']
        self.PLAYFIELD_HEIGHT = self.cfg['PLAYFIELD_HEIGHT']
        self.SCOREBOARD_WIDTH = self.cfg['SCOREBOARD_WIDTH']
        self.SCOREBOARD_HEIGHT = self.cfg['SCOREBOARD_HEIGHT']
        self.FPS = self.cfg['FPS']
        self.FALL_SPEED = self.cfg['FALL_SPEED']   # ms

    def spawn_block(self):
        shape = random.choice(self.shapes)
        # shape = self.shapes[1]

        entity = self.entity_manager.create_entity('block')
        entity.add_component(PositionComponent(self.PLAYFIELD_WIDTH // 2 - len(shape[0]) // 2, 0))
        entity.add_component(SpeedComponent(0, 5))
        entity.add_component(ShapeComponent(shape))
        entity.add_component(ColorComponent())
        entity.add_component(StateComponent())
    
    def init_map(self):
        map_entity = self.entity_manager.create_entity('map')
        map_entity.add_component(MapComponent(np.zeros((self.PLAYFIELD_HEIGHT, self.PLAYFIELD_WIDTH), dtype=int)))

    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT or event.type == pygame.USEREVENT + 2:
                self.running = False
            if event.type == pygame.USEREVENT + 1:
                self.systems['MapSystem'].process(self.entity_manager.entities)
                self.systems['ClearLinesSystem'].process(self.entity_manager.entities)

                self.spawn_block()
            else:
                continue

        self.systems['InputSystem'].process(events, self.entity_manager.entities)

    def update(self):
        self.systems['CollisionSystem'].process(self.entity_manager.entities)
        current_time = pygame.time.get_ticks()
        if current_time - self.fall_time >= self.FALL_SPEED:
            self.systems['MovementSystem'].process(self.entity_manager.entities)
            self.fall_time = current_time

    def render(self):
        self.systems['RenderSystem'].process(self.entity_manager.entities)

        pygame.display.flip()
        # self.clock.tick(self.FPS)

    def run(self):
        # self.running = True
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(self.FPS)
        pygame.quit()