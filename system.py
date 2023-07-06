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
        pygame.K_p: 'pause',
        pygame.K_RETURN: 'restart',
    }
    def process(self, events, entities):
        entity = entities['block']
        map_entity = entities['map']
        pygame.key.set_repeat(500, 50)
        for event in events:
            if event.type == pygame.KEYDOWN:
                position = entity.get_component(PositionComponent)
                shape = entity.get_component(ShapeComponent)
                state = entity.get_component(StateComponent)
                self.speed = entity.get_component(SpeedComponent)
                self.map_comp = map_entity.get_component(MapComponent)
                if state.active:
                    self.handle_key_event(event.key, position, shape, state)

    def handle_key_event(self, key, position, shape, state):
        action = self.key_mapping.get(key)
        if action == 'left' and state.direction != 'left':
            position.x -= 1
        elif action == 'right' and state.direction != 'right':
            position.x += 1
        elif action == 'down' and state.direction != 'bottom':
            position.y += 1
        elif action == 'rotate':
            shape.rotate = True
            shape.rotate_shape = np.rot90(shape.shape, -1)
            shape.rotate_width = len(shape.rotate_shape[0])
            shape.rotate_height = len(shape.rotate_shape)
        elif action == 'quick_drop':
            self.speed.y = 1   # ms
        elif action == 'pause':
            self.map_comp.paused = not self.map_comp.paused
        elif action == 'restart':
            self.map_comp.game_over = False
            self.map_comp.restart = True

# 移动系统
class MovementSystem:
    def __init__(self) -> None:
        self.fall_time = 0
    def process(self, entities):
        entity = entities['block']
        position = entity.get_component(PositionComponent)
        state = entity.get_component(StateComponent)
        speed = entity.get_component(SpeedComponent)
        if state.active:
            current_time = pygame.time.get_ticks()
            if current_time - self.fall_time >= speed.y:
                position.y += 1
                self.fall_time = current_time

# 碰撞检测系统
class CollisionSystem:
    def __init__(self, config) -> None:
        self.playfield_width = config.PLAYFIELD_WIDTH
        self.playfield_height = config.PLAYFIELD_HEIGHT
    
    def process(self, entities):
        entity = entities['block']
        map_entity = entities['map']
        position = entity.get_component(PositionComponent)
        shape = entity.get_component(ShapeComponent)
        state = entity.get_component(StateComponent)
        map_mat = map_entity.get_component(MapComponent)

        np_shape = np.asarray(shape.shape)
        active_block_map = map_mat.active_map
        dead_block_map = map_mat.map

        map_left_boundary = active_block_map[:, 0]
        map_right_boundary = active_block_map[:, -1]
        map_bottom_boundary = active_block_map[-1, :]

        # 检测是否到达最顶层
        if map_mat.height >= self.playfield_height:
            map_mat.game_over = True
            return
        
        if np.any(map_bottom_boundary == 1):
            # 下边界
            state.active = False
            state.collision = True
            state.direction = 'bottom'
            pygame.event.post(pygame.event.Event(pygame.USEREVENT+1))
            return
        # 检测方块是否落在其他方块顶部
        if state.direction != 'bottom':
            for idx, arr in enumerate(np_shape):
                if np.any(map_mat.map[position.y + idx + 1, position.x:position.x+shape.width].squeeze() & arr):
                    # 停止方块的运动
                    state.active = False
                    state.collision = True
                    state.direction = 'bottom'
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT+1))
                    return
        # 检测方块是否碰到边界
        if np.any(map_left_boundary == 1):
            # 左边界
            state.collision = True
            state.direction = 'left'
        elif np.any(map_right_boundary == 1):
            # 右边界
            state.collision = True
            state.direction = 'right'
        else:
            state.collision = False
            state.direction = ''
        # 运动方块左/右边缘与静止方块右/左边缘发生碰撞
        # 检测方块左右是否碰撞
        for idx, arr in enumerate(np_shape.T):
            if state.direction != 'left' and np.any(map_mat.map[position.y:position.y+shape.height, position.x+idx-1].squeeze() & arr):
                state.collision = True
                state.direction = 'left'
            elif state.direction != 'right' and np.any(map_mat.map[position.y:position.y+shape.height, position.x+idx].squeeze() & arr):
                state.collision = True
                state.direction = 'right'

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
        map_mat.score += rows_cleared ** 2

# 渲染系统
class RenderSystem:
    def __init__(self, screen, config):
        self.screen = screen
        self.block_size = config.BLOCK_SIZE
        self.real_block_size = self.block_size-3
        self.font = pygame.font.Font(None, 36)
        self.play_field = pygame.Surface((config.PLAYFIELD_WIDTH, config.PLAYFIELD_HEIGHT))
        self.score_board = pygame.Surface((config.SCOREBOARD_WIDTH, config.SCOREBOARD_HEIGHT))
        self.game_over_text = self.font.render("You Died!", True, (255, 0, 0))
        self.game_over_text_rect = self.game_over_text.get_rect(center=((self.play_field.get_width()*self.block_size) // 2, (self.play_field.get_height()*self.block_size) // 2))

    def process(self, entities):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.play_field, (0, 0))
        self.map_mat = entities['map'].get_component(MapComponent)
        
        self._render_block(self.map_mat.active_map, self.map_mat.active_color_map)
        self._render_block(self.map_mat.map, self.map_mat.color_map)
        self._render_score()
        self._render_next_block(entities)
        if self.map_mat.game_over:
            self._render_game_over()

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
        score_text = self.font.render(str(self.map_mat.score), True, (0,0, 255))
        score_rect = score_text.get_rect(center=(self.screen.get_width() - self.score_board.get_rect().centerx, self.score_board.get_rect().centery//2))
        self.screen.blit(score_text, score_rect)
    
    def _render_game_over(self):
        self.screen.blit(self.game_over_text, self.game_over_text_rect)

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
        else:
            # 方块落地，更新动态方块状态矩阵
            map_mat.active_map = np.where(map_mat.active_map==1, 0, map_mat.active_map)
            map_mat_block = map_mat.map[position.y:position.y+shape.height, position.x:position.x+shape.width]
            color_block = map_mat.color_map[position.y:position.y+shape.height, position.x:position.x+shape.width]
            map_mat_block |= np_shape
            color_mask = map_mat_block&np_shape
            nonzero_indices = np.where(color_mask != 0)
            color_map_copy[position.y:position.y+shape.height, position.x:position.x+shape.width] = np_shape
            
            for x, y in zip(nonzero_indices[0], nonzero_indices[1]):
                if color_mask[x][y]==1:
                    color_block[x][y] = color.color
                else:
                    continue
            map_mat.height = np.max(np.where(map_mat.map[::-1]==1)[0])+1

class SpawnSystem:
    def __init__(self, shapes, config) -> None:
        self.shapes = shapes
        self.paly_field_width = config.PLAYFIELD_WIDTH
        
    def process(self, entity_manager):
        drop_speed = entity_manager.entities['map'].get_component(MapComponent).drop_speed
        next_block = entity_manager.entities['next_block']
        entity_manager.entities['block'] = next_block

        next_shape = random.choice(self.shapes)
        next_entity = entity_manager.create_entity('next_block')

        next_entity.add_component(PositionComponent(self.paly_field_width // 2 - len(next_shape[0]) // 2, 0))
        next_entity.add_component(SpeedComponent(0, drop_speed))
        next_entity.add_component(ShapeComponent(next_shape))
        next_entity.add_component(ColorComponent())
        next_entity.add_component(StateComponent())

class RotationSystem:
    def process(self, entities):
        shape = entities['block'].get_component(ShapeComponent)
        position = entities['block'].get_component(PositionComponent)
        map_mat = entities['map'].get_component(MapComponent)
        if shape.rotate:
            shape.rotate = False
            available_mat = map_mat.map[position.y:position.y+shape.rotate_height, position.x:position.x+shape.rotate_width]
            if not np.any(np.where(available_mat==1)) and available_mat.shape[1]==shape.rotate_width:
                shape.shape = shape.rotate_shape
                shape.height = shape.rotate_height
                shape.width = shape.rotate_width
