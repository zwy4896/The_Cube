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
import random
from component import PositionComponent, ShapeComponent, ColorComponent, SpeedComponent, StateComponent, MapComponent
# 输入系统
class InputSystem:
    key_mapping = {
        pygame.K_LEFT: 'left',
        pygame.K_RIGHT: 'right',
        pygame.K_DOWN: 'down',
        pygame.K_UP: 'rotate',
        pygame.K_SPACE: 'quick_drop',
    }
    def process(self, events, entities):
        entity = entities['block']
        pygame.key.set_repeat(500, 50)
        for event in events:
            if event.type == pygame.KEYDOWN:
                position = entity.get_component(PositionComponent)
                shape = entity.get_component(ShapeComponent)
                state = entity.get_component(StateComponent)
                if state.active:
                    self.handle_key_event(event.key, position, shape)

    def handle_key_event(self, key, position, shape):
        action = self.key_mapping.get(key)
        if action == 'left':
            position.x -= 1
        elif action == 'right':
            position.x += 1
        elif action == 'down':
            position.y += 1
        elif action == 'rotate':
            shape.shape = np.rot90(shape.shape, -1)
            shape.width = len(shape.shape[0])
            shape.height = len(shape.shape)

# 移动系统
class MovementSystem:
    def process(self, entities):
        entity = entities['block']
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
        entity = entities['block']
        map_entity = entities['map']
        position = entity.get_component(PositionComponent)
        shape = entity.get_component(ShapeComponent)
        state = entity.get_component(StateComponent)
        map_mat = map_entity.get_component(MapComponent)

        # 检测是否到达最顶层
        if map_mat.height >= self.playfield_height:
            pygame.event.post(pygame.event.Event(pygame.USEREVENT+2))
            return
        # 检测方块是否碰到窗口底部
        if position.y + shape.height >= self.playfield_height:
            position.y = self.playfield_height - shape.height
            # 停止方块的运动
            state.active = False
            pygame.event.post(pygame.event.Event(pygame.USEREVENT+1))
            return
        # 检测方块是否碰到左边界
        if position.x < 0:
            position.x = 0
        elif position.x> self.playfield_width - shape.width:
            # 限制右移
            position.x = self.playfield_width - shape.width
        # 检测方块的底部与其他方块的顶部碰撞
        for idx, arr in enumerate(shape.shape[::-1]):
            if np.count_nonzero(map_mat.map[position.y + shape.height-idx-1, position.x:position.x+shape.width].squeeze() & np.asarray(arr)):
                # 停止方块的运动
                state.active = False
                pygame.event.post(pygame.event.Event(pygame.USEREVENT+1))
                return

# 消行和得分系统
class ClearLinesSystem:
    def process(self, entities):
        # 处理消行和更新得分逻辑
        map_mat = entities['map'].get_component(MapComponent)
        rows_to_delete = np.where(np.sum(map_mat.map, axis=1) == map_mat.map.shape[1])[0]
        if len(rows_to_delete) > 0: 
            self.delete_rows(map_mat, rows_to_delete)
            self.update_score(map_mat, len(rows_to_delete))

    def delete_rows(self, map_mat, rows_to_delete):
        map_mat.map = np.delete(map_mat.map, rows_to_delete, axis=0)
        map_mat.color_map = np.delete(map_mat.color_map, rows_to_delete, axis=0)
        empty_rows = np.tile(map_mat.empty_row, (len(rows_to_delete), 1))
        map_mat.map = np.concatenate((empty_rows, map_mat.map), axis=0)
        map_mat.color_map = np.concatenate((empty_rows, map_mat.color_map), axis=0)
        map_mat.height -= len(rows_to_delete)

    def update_score(self, map_mat, rows_cleared):
        map_mat.lines_cleared += rows_cleared

# 渲染系统
class RenderSystem:
    def __init__(self, screen, play_field, score_board, block_size):
        self.screen = screen
        self.block_size = block_size
        self.real_block_size = block_size-3
        self.play_field = play_field
        self.score_board = score_board
        self.font = pygame.font.Font(None, 36)

    def process(self, entities):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.play_field, (0, 0))
        self.map_mat = entities['map'].get_component(MapComponent)
        
        self._render_block(self.map_mat.active_map, self.map_mat.active_color_map)
        self._render_block(self.map_mat.map, self.map_mat.color_map)
        self._render_score()
        self._render_next_block(entities)

    def _render_next_block(self, entities):
        next_shape = entities['next_block'].get_component(ShapeComponent)
        next_color = entities['next_block'].get_component(ColorComponent)
        # 获取方块的非零索引
        next_nonzero_indices = np.where(np.asarray(next_shape.shape) != 0)
        # 计算方块的绘制位置
        next_block_positions = (11 + next_nonzero_indices[1], 10 + next_nonzero_indices[0])
        # 创建方块表面
        next_block_surface = pygame.Surface((self.real_block_size, self.real_block_size))
        next_block_surface.fill(next_color.color)
        # 批量绘制所有方块
        for x, y in zip(next_block_positions[0], next_block_positions[1]):
            next_block_rect = pygame.Rect(x * self.block_size, y * self.block_size, self.real_block_size, self.real_block_size)
            self.screen.blit(next_block_surface, next_block_rect)

    def _render_block(self, block_mat, color_mat):
        nonzero_indices = np.where(block_mat != 0)
        for x, y in zip(nonzero_indices[0], nonzero_indices[1]):
            block_rect = pygame.Rect(y * self.block_size, x * self.block_size, self.real_block_size, self.real_block_size)
            pygame.draw.rect(self.screen, color_mat[x][y], block_rect)
    
    def _render_score(self):
        self.score_board.fill((255,255,255))
        self.screen.blit(self.score_board, (self.screen.get_width()-self.score_board.get_size()[0], 0))
        score_text = self.font.render(str(self.map_mat.lines_cleared), True, (0,0, 255))
        score_rect = score_text.get_rect(center=(self.screen.get_width() - self.score_board.get_rect().centerx, self.score_board.get_rect().centery//2))
        self.screen.blit(score_text, score_rect)
    
class MapSystem:
    def process(self, entities):
        map_entity = entities['map']
        last_entity = entities['block']
        map_mat = map_entity.get_component(MapComponent)
        position = last_entity.get_component(PositionComponent)
        shape = last_entity.get_component(ShapeComponent)
        state = last_entity.get_component(StateComponent)
        color = last_entity.get_component(ColorComponent)
        np_shape = np.asarray(shape.shape)
        color_map_copy = map_mat.color_map.copy()

        if state.active:
            active_color_map_cache = np.zeros_like(map_mat.active_color_map)
            map_mat.active_map*=0
            map_mat.active_map[position.y:position.y+shape.height, position.x:position.x+shape.width] = np_shape
            cache = active_color_map_cache[position.y:position.y+shape.height, position.x:position.x+shape.width] | np_shape
            nonzero_indices = np.where(cache != 0)
            for x, y in zip(nonzero_indices[0], nonzero_indices[1]):
                if cache[x][y] == 1:
                    active_color_map_cache[position.y:position.y+shape.height, position.x:position.x+shape.width][x][y] = color.color
            map_mat.active_color_map = active_color_map_cache
        if not state.active:
            # 方块落地，更新动态方块状态矩阵
            map_mat.active_map = np.where(map_mat.active_map==1, 0, map_mat.active_map)
            map_mat_block = map_mat.map[position.y-1:position.y-1+shape.height, position.x:position.x+shape.width]
            color_block = map_mat.color_map[position.y-1:position.y-1+shape.height, position.x:position.x+shape.width]
            map_mat_block |= np_shape
            color_mask = map_mat_block&np_shape
            nonzero_indices = np.where(color_mask != 0)
            color_map_copy[position.y-1:position.y-1+shape.height, position.x:position.x+shape.width] = np_shape
            
            for x, y in zip(nonzero_indices[0], nonzero_indices[1]):
                if color_mask[x][y]==1:
                    color_block[x][y] = color.color
                else:
                    continue
            map_mat.height = np.max(np.where(map_mat.map[::-1]==1)[0])+1

class SpawnSystem:
    def __init__(self, shapes, paly_field_width) -> None:
        self.shapes = shapes
        self.paly_field_width = paly_field_width
    def process(self, entity_manager):
        next_block = entity_manager.entities['next_block']
        entity_manager.entities['block'] = next_block

        next_shape = random.choice(self.shapes)
        next_entity = entity_manager.create_entity('next_block')

        next_entity.add_component(PositionComponent(self.paly_field_width // 2 - len(next_shape[0]) // 2, 0))
        next_entity.add_component(SpeedComponent(0, 5))
        next_entity.add_component(ShapeComponent(next_shape))
        next_entity.add_component(ColorComponent())
        next_entity.add_component(StateComponent())