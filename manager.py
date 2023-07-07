#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Author      : Bluzy
Date        : 2023/07/06 11:33:10
Contact     : zoe4896@outlook.com
Description : 
'''

import yaml
import pygame
import random
import numpy as np
from types import SimpleNamespace
from entity import EntityManager
from system import InputSystem, MovementSystem, CollisionSystem, ClearLinesSystem, RenderSystem, MapSystem, SpawnSystem, RotationSystem
from component import PositionComponent, SpeedComponent, ShapeComponent, ColorComponent, StateComponent, MapComponent

class GameManager:
    def __init__(self, config_path) -> None:
        pygame.init()
        pygame.display.set_caption("The Cube")
        self.config = self._get_config_from_yaml(config_path)
        self.screen = pygame.display.set_mode((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), vsync=True)
        self.clock = pygame.time.Clock()
        self.shapes = [
            [[1, 1, 1, 1]],
            [[1, 1], [1, 1]],
            [[1, 0, 0], [1, 1, 1]],
            [[0, 0, 1], [1, 1, 1]],
            [[0, 1, 1], [1, 1, 0]],
            [[1, 1, 0], [0, 1, 1]],
            [[0, 1, 0], [1, 1, 1]]
        ]

    def _get_config_from_yaml(self, file_path):
        config = self._dict_to_struct(yaml.safe_load(open(file_path, 'r')))
        return config
    
    def _dict_to_struct(self, d):
        return SimpleNamespace(**{k: self._dict_to_struct(v) if isinstance(v, dict) else v for k, v in d.items()})
    
class Systems:
    def __init__(self, game_manager) -> None:
        self.game_manager = game_manager
        self.config = game_manager.config
        self.sys_input = InputSystem()
        self.sys_movement = MovementSystem()
        self.sys_collision = CollisionSystem(self.config)
        self.sys_clear_line = ClearLinesSystem()
        self.sys_render = RenderSystem(self.game_manager.screen, self.config)
        self.sys_map = MapSystem()
        self.sys_spawn = SpawnSystem(self.game_manager.shapes, self.config)
        self.sys_rotation = RotationSystem()

class Entities:
    def __init__(self, game_manager) -> None:
        self.game_manager = game_manager
        self.config = game_manager.config
        self.entity_manager = EntityManager()
        self._init_block()
        self._init_map()

    def _init_block(self):
        random_shapes = random.choices(self.game_manager.shapes, k=2)
        shape = random_shapes[0]
        next_shape = random_shapes[1]
        self.create_entity(
            'block',
            PositionComponent(self.config.PLAYFIELD_WIDTH // 2 - len(self.game_manager.shapes[0]) // 2, 0),
            SpeedComponent(0, self.config.FALL_SPEED, self.config.HARD_DROP_SPEED), 
            ShapeComponent(shape), 
            ColorComponent(), 
            StateComponent()
        )
        self.create_entity(
            'next_block',
            PositionComponent(self.config.PLAYFIELD_WIDTH // 2 - len(self.game_manager.shapes[0]) // 2, 0),
            SpeedComponent(0, self.config.FALL_SPEED, self.config.HARD_DROP_SPEED), 
            ShapeComponent(next_shape), 
            ColorComponent(), 
            StateComponent()
        )

    def _init_map(self):
        self.create_entity(
            'map',
            MapComponent(np.zeros((self.config.PLAYFIELD_HEIGHT, self.config.PLAYFIELD_WIDTH), dtype=int), self.config.FALL_SPEED)
        )

    def create_entity(self, entity_type, *components):
        entity = self.entity_manager.create_entity(entity_type)
        for component in components:
            entity.add_component(component)
