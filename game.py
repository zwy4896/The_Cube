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
from system import InputSystem, MovementSystem, CollisionSystem, ClearLinesSystem, RenderSystem, MapSystem, SpawnSystem

# 游戏类
class Game:
    def __init__(self, cfg):
        pygame.init()
        self.cfg = cfg
        self.get_params()
        self.world = World(self.PLAYFIELD_WIDTH, self.PLAYFIELD_HEIGHT)
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), vsync=True)
        self.play_field = pygame.Surface((self.PLAYFIELD_WIDTH, self.PLAYFIELD_HEIGHT))
        self.score_board = pygame.Surface((self.SCOREBOARD_WIDTH, self.SCOREBOARD_HEIGHT))
        pygame.display.set_caption("The Cube")
        self.clock = pygame.time.Clock()
        self.running = True
        self.fall_time = 0
        self.entity_manager = EntityManager()
        self.shapes = [
            [[1, 1, 1, 1]],
            [[1, 1], [1, 1]],
            [[1, 0, 0], [1, 1, 1]],
            [[0, 0, 1], [1, 1, 1]],
            [[0, 1, 1], [1, 1, 0]],
            [[1, 1, 0], [0, 1, 1]],
            [[0, 1, 0], [1, 1, 1]]
        ]
        self._init_system()
        self.init_map()
        self.spawn_block()
        self.game_over = False
        self.restart = False

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

    def _init_system(self):
        self.systems = {
            'InputSystem': InputSystem(),
            'MovementSystem': MovementSystem(),
            'CollisionSystem': CollisionSystem(self.world.playfield_width, self.world.playfield_height),
            'ClearLinesSystem': ClearLinesSystem(),
            'RenderSystem': RenderSystem(self.screen, self.play_field, self.score_board, self.BLOCK_SIZE),
            'MapSystem': MapSystem(),
            'SpawnSystem': SpawnSystem(self.shapes, self.PLAYFIELD_WIDTH)
        }
    
    def spawn_block(self):
        random_shapes = random.choices(self.shapes, k=2)
        shape = random_shapes[0]
        next_shape = random_shapes[1]
        self.create_entity(
            'block', 
            PositionComponent(self.world.playfield_width // 2 - len(shape[0]) // 2, 0),
            SpeedComponent(0, 1000), 
            ShapeComponent(shape), 
            ColorComponent(), 
            StateComponent()
        )

        self.create_entity(
            'next_block',
            PositionComponent(self.world.playfield_width // 2 - len(next_shape[0]) // 2, 0),
            SpeedComponent(0, 1000), 
            ShapeComponent(next_shape), 
            ColorComponent(),
            StateComponent()
        )

    def create_entity(self, entity_type, *components):
        entity = self.entity_manager.create_entity(entity_type)
        for component in components:
            entity.add_component(component)
    
    def init_map(self):
        self.create_entity('map', MapComponent(np.zeros((self.PLAYFIELD_HEIGHT, self.PLAYFIELD_WIDTH), dtype=int)))

    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT or event.type == pygame.USEREVENT + 2:
                self.running = False
            if event.type == pygame.USEREVENT + 1:
                # 方块落触底或碰撞
                # 1. 判断消行
                # 2. 重新生成方块
                self.systems['ClearLinesSystem'].process(self.entity_manager.entities)
                self.systems['SpawnSystem'].process(self.entity_manager)
            else:
                continue

        self.systems['InputSystem'].process(events, self.entity_manager.entities)

    def update(self):
        # 检测是否碰撞（触底、碰撞、左右界）
        self.systems['CollisionSystem'].process(self.entity_manager.entities)
        # 根据碰撞结果更新map
        self.systems['MapSystem'].process(self.entity_manager.entities)
        self.systems['MovementSystem'].process(self.entity_manager.entities)
        # 更新map
        self.systems['MapSystem'].process(self.entity_manager.entities)

    def render(self):
        self.systems['RenderSystem'].process(self.entity_manager.entities)
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            map_comp = self.entity_manager.entities['map'].get_component(MapComponent)
            paused = map_comp.paused
            self.game_over = map_comp.game_over
            self.restart = map_comp.restart
            if not paused and not self.game_over:
                if not self.restart:
                    self.update()
                    self.render()
                    self.clock.tick(self.FPS)
                else:
                    self.restart = False
                    self._init_system()
                    self.init_map()
                    self.spawn_block()
        pygame.quit()