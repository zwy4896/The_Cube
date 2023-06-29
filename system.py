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
        entity = entities['block'][-1]
        pygame.key.set_repeat(500, 50)
        for event in events:
            if event.type == pygame.KEYDOWN:
                if entity.has_components(PositionComponent, ShapeComponent):
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
        entity = entities['block'][-1]
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
        entity = entities['block'][-1]
        map_entity = entities['map'][0]
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
                return
            # 检测方块是否碰到左边界
            if position.x <= 0:
                position.x = 0
            if position.x + shape.width >= self.playfield_width:
                # 限制右移
                position.x = self.playfield_width - shape.width
            # 检测方块的底部与其他方块的顶部碰撞
            for idx, arr in enumerate(shape.shape[::-1]):
                if np.count_nonzero(map_mat.map[position.y + shape.height-idx, position.x:position.x+shape.width].squeeze() & np.asarray(arr)):
                    # 停止方块的运动
                    state.active = False
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT+1))
                    return

# 消行和得分系统
class ClearLinesSystem:
    def process(self, entities):
        # 处理消行和更新得分逻辑
        map_mat = entities['map'][0].get_component(MapComponent)
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
        # 渲染游戏区域
        self.screen.blit(self.play_field, (0, 0))

        # 渲染分数和下一个方块
        self.score_board.fill((255,255,255))
        self.screen.blit(self.score_board, (self.screen.get_width()-self.score_board.get_size()[0], 0))
        self.map_mat = entities['map'][0].get_component(MapComponent)
        
        next_entity = entities['next_block'][0]
        self.next_shape = next_entity.get_component(ShapeComponent)
        self.next_color = next_entity.get_component(ColorComponent)

        self._render_score()
        self._render_active_block(entities)
        self._render_dead_block()

    def _render_active_block(self, entities):
        for entity in entities['block']:
            position = entity.get_component(PositionComponent)
            shape = entity.get_component(ShapeComponent)
            block = entity.get_component(ColorComponent)
            state = entity.get_component(StateComponent)
            if state.active:
                # 获取方块的非零索引
                nonzero_indices = np.where(np.asarray(shape.shape) != 0)
                next_nonzero_indices = np.where(np.asarray(self.next_shape.shape) != 0)
                # 计算方块的绘制位置
                block_positions = (position.x + nonzero_indices[1], position.y + nonzero_indices[0])
                next_block_positions = (11+next_nonzero_indices[1], 10+next_nonzero_indices[0])
                # 创建方块表面
                block_surface = pygame.Surface((self.real_block_size, self.real_block_size))
                block_surface.fill(block.color)
                next_block_surface = pygame.Surface((self.real_block_size, self.real_block_size))
                next_block_surface.fill(self.next_color.color)
                # 批量绘制所有方块
                for x, y in zip(block_positions[0], block_positions[1]):
                    block_rect = pygame.Rect(x * self.block_size, y * self.block_size, self.real_block_size, self.real_block_size)
                    self.screen.blit(block_surface, block_rect)
                for x, y in zip(next_block_positions[0], next_block_positions[1]):
                    next_block_rect = pygame.Rect(x * self.block_size, y * self.block_size, self.real_block_size, self.real_block_size)
                    self.screen.blit(next_block_surface, next_block_rect)

    def _render_dead_block(self):
        mat_flatten = self.map_mat.map.flatten()
        for idx, num in enumerate(mat_flatten):
            if num == 1:
                pos_y, pos_x = np.unravel_index(idx, self.map_mat.map.shape)
                block_rect = pygame.Rect(pos_x * self.block_size, pos_y * self.block_size, self.block_size-3, self.block_size-3)
                pygame.draw.rect(self.screen, self.map_mat.color_map[pos_y][pos_x], block_rect)
    
    def _render_score(self):
        score_text = self.font.render(str(self.map_mat.lines_cleared), True, (0,0, 255))
        score_rect = score_text.get_rect(center=(self.screen.get_width() - self.score_board.get_rect().centerx, self.score_board.get_rect().centery//2))
        self.screen.blit(score_text, score_rect)
    
class MapSystem:
    def __init__(self, playfield_mat) -> None:
        self.playfield_mat = playfield_mat
    def process(self, entities):
        map_entity = entities['map'][0]
        last_entity = entities['block'][-1]
        map_mat = map_entity.get_component(MapComponent)
        position = last_entity.get_component(PositionComponent)
        shape = last_entity.get_component(ShapeComponent)
        state = last_entity.get_component(StateComponent)
        color = last_entity.get_component(ColorComponent)
        np_shape = np.asarray(shape.shape)
        color_map_copy = map_mat.color_map.copy()
        if not state.active:
            map_mat.map[position.y:position.y+shape.height, position.x:position.x+shape.width] |= np_shape
            color_map_copy[position.y:position.y+shape.height, position.x:position.x+shape.width] = np_shape
            for i in range(map_mat.color_map.shape[0]):
                for j in range(map_mat.color_map.shape[1]):
                    if color_map_copy[i, j] == 1:
                        map_mat.color_map[i, j] = color.color
            map_mat.height = np.max(np.where(map_mat.map[::-1]==1)[0])+1
            if map_mat.height >= self.playfield_mat.shape[0]:
                pygame.event.post(pygame.event.Event(pygame.USEREVENT+2))
                return

class SpawnSystem:
    def __init__(self, shapes, paly_field_width) -> None:
        self.shapes = shapes
        self.paly_field_width = paly_field_width
    def process(self, entity_manager):
        next_block = entity_manager.entities['next_block'][0]
        entity_manager.entities['block'].append(next_block)

        entity_manager.destroy_entity('next_block')
        next_shape = random.choice(self.shapes)
        next_entity = entity_manager.create_entity('next_block')

        next_entity.add_component(PositionComponent(self.paly_field_width // 2 - len(next_shape[0]) // 2, 0))
        next_entity.add_component(SpeedComponent(0, 5))
        next_entity.add_component(ShapeComponent(next_shape))
        next_entity.add_component(ColorComponent())
        next_entity.add_component(StateComponent())