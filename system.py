#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Author      : Bluzy
Date        : 2023/06/26 14:32:54
Contact     : zoe4896@outlook.com
Description : 
'''
import pygame
import numpy as np
from component import PositionComponent, ShapeComponent, ColorComponent, SpeedComponent, StateComponent, MapComponent
# 输入系统
class InputSystem:
    def process(self, events, entities):
        entity = entities[-1]
        pygame.key.set_repeat(500, 50)
        for event in events:
            if event.type == pygame.KEYDOWN:
                if entity.has_components(PositionComponent, ShapeComponent):
                    position = entity.get_component(PositionComponent)
                    shape = entity.get_component(ShapeComponent)
                    state = entity.get_component(StateComponent)
                    if state.active:
                        if event.key == pygame.K_LEFT:
                            # 左移方块
                            position.x -= 1
                            # velocity.x = -1
                        elif event.key == pygame.K_RIGHT:
                            # 右移方块
                            position.x += 1
                        elif event.key == pygame.K_DOWN:
                            # 加速下落
                            position.y += 1
                            # 增加方块速度
                            # entity.add_component(SpeedComponent(1))
                        elif event.key == pygame.K_UP:
                            # 旋转方块
                            # position.y -= 1
                            rotated_shape = list(zip(*reversed(shape.shape)))
                            shape.shape = rotated_shape
                            shape.width = len(shape.shape[0])
                            shape.height = len(shape.shape)
# 移动系统
class MovementSystem:
    def __init__(self, dt) -> None:
        self.dt = dt
    def process(self, entities):
        entity = entities[-1]
        if entity.has_components(PositionComponent, SpeedComponent):
            position = entity.get_component(PositionComponent)
            state = entity.get_component(StateComponent)

            if state.active:
                # 计算新的位置
                position.y += 1

# 碰撞检测系统
class CollisionSystem:
    def __init__(self, playfield_width, playfield_height) -> None:
        self.playfield_width = playfield_width
        self.playfield_height = playfield_height
    def process(self, entities):
        entity = entities[-1]
        map_entity = entities[0]
        if entity.has_components(PositionComponent, ShapeComponent):
            position = entity.get_component(PositionComponent)
            shape = entity.get_component(ShapeComponent)
            state = entity.get_component(StateComponent)
            map_mat = map_entity.get_component(MapComponent)
            # 检测方块是否碰到窗口底部
            if position.y + shape.height >= self.playfield_height:
                # 停止方块的运动
                position.y = self.playfield_height - shape.height
                state.active = False
                pygame.event.post(pygame.event.Event(pygame.USEREVENT+1))
                # self.playfield_mat[position.y:position.y+shape.height, position.x:position.x+shape.width] |= np.asarray(shape.shape)
                return
            # 检测方块是否碰到左边界
            if position.x <= 0:
                position.x = 0
            if position.x + shape.width >= self.playfield_width:
                # 限制右移
                position.x = self.playfield_width - shape.width
            # 检测方块的底部与其他方块的顶部碰撞
            if np.count_nonzero(map_mat.map[position.y + shape.height, position.x:position.x+shape.width].squeeze() & np.asarray(shape.shape[-1])):
                # 停止方块的运动
                state.active = False
                pygame.event.post(pygame.event.Event(pygame.USEREVENT+1))
                return

# 消行和得分系统
class ClearLinesSystem:
    def process(self, entities):
        # 处理消行和更新得分逻辑
        pass

# 渲染系统
class RenderSystem:
    def __init__(self, screen, play_filed, score_board, block_size):
        self.screen = screen
        self.block_size = block_size
        self.play_filed = play_filed
        self.score_board = score_board

    def process(self, entities):
        self.screen.fill((0, 0, 0))
        # 渲染游戏区域
        self.screen.blit(self.play_filed, (0, 0))

        # 渲染分数和下一个方块
        self.score_board.fill((255,255,255))
        self.screen.blit(self.score_board, (self.play_filed.get_size()[0]*40-self.score_board.get_size()[0], 0))
        for entity in entities:
            if entity.has_components(PositionComponent, ShapeComponent, ColorComponent):
                position = entity.get_component(PositionComponent)
                shape = entity.get_component(ShapeComponent)
                block = entity.get_component(ColorComponent)
                # 绘制方块
                for i in range(shape.height):
                    for j in range(len(shape.shape[i])):
                        if shape.shape[i][j] == 1:
                            block_rect = pygame.Rect((position.x + j) * self.block_size, (position.y + i) * self.block_size, self.block_size, self.block_size)
                            pygame.draw.rect(self.screen, block.color, block_rect)

class MapSystem:
    def __init__(self, playfield_mat) -> None:
        self.playfield_mat = playfield_mat
    def process(self, entities):
        map_entity = entities[0]
        entity = entities[-1]
        if map_entity.has_components(MapComponent) and entity.has_components(PositionComponent, ShapeComponent, StateComponent):
            position = entity.get_component(PositionComponent)
            shape = entity.get_component(ShapeComponent)
            state = entity.get_component(StateComponent)
            map_mat = map_entity.get_component(MapComponent)
            if not state.active:
                map_mat.map[position.y:position.y+shape.height, position.x:position.x+shape.width] |= np.asarray(shape.shape)