#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Author      : Bluzy
Date        : 2023/06/26 14:32:19
Contact     : zoe4896@outlook.com
Description : 
'''
import random
import numpy as np

# 定义组件
class PositionComponent:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class SpeedComponent:
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y
    
class ShapeComponent:
    def __init__(self, shape):
        self.shape = shape
        self.width = len(shape[0])
        self.height = len(shape)
        self.rotate = False
        self.rotate_shape = shape
        self.rotate_width = len(shape[0])
        self.rotate_height = len(shape)

class ColorComponent:
    def __init__(self):
        self.color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))

class StateComponent:
    def __init__(self, active=True) -> None:
        self.active = active
        self.collision = False
        self.direction = ''

class MapComponent:
    def __init__(self, map_mat, block_drop_speed) -> None:
        self.map = map_mat
        self.active_map = np.zeros_like(self.map, dtype=int)
        self.active_color_map = np.zeros_like(self.map, dtype=object)
        self.color_map = np.zeros_like(self.map, dtype=object)
        self.height = 0
        self.lines_cleared = 0
        self.empty_row = np.zeros((1, self.map.shape[1]), dtype=int)
        self.paused = False
        self.game_over = False
        self.score = 0
        self.restart = False
        self.drop_speed = block_drop_speed