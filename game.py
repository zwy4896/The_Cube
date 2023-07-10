#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Author      : Bluzy
Date        : 2023/06/26 14:28:59
Contact     : zoe4896@outlook.com
Description : 
'''
import pygame
from manager import GameManager, Systems, Entities
from component import MapComponent, StateComponent, ShapeComponent

# 游戏类
class Game:
    def __init__(self, config_path):
        self.game_manager = GameManager(config_path)
        self._init()

    def _init(self):
        self.systems = Systems(self.game_manager)
        self.entities = Entities(self.game_manager)
        self.running = True

    def _handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT or event.type == pygame.USEREVENT + 2:
                self.running = False
            if event.type == pygame.USEREVENT + 1:
                # 方块落触底或碰撞
                # 1. 判断消行
                # 2. 重新生成方块
                self.systems.sys_clear_line.process(self.entities.entity_manager.entities)
                self.systems.sys_spawn.process(self.entities.entity_manager)
            else:
                continue
        self.state = self.entities.entity_manager.entities['block'].get_component(StateComponent)
        _shape = self.entities.entity_manager.entities['block'].get_component(ShapeComponent)
        self.map = self.entities.entity_manager.entities['map'].get_component(MapComponent)
        self.paused = self.map.paused
        self.game_over = self.map.game_over
        self.restart = self.map.restart

        if self.map.game_over:
            self.systems.sys_spawn.process(self.entities.entity_manager)
        if not self.state.hard_drop:
            self.systems.sys_input.process(events, self.entities.entity_manager.entities)
        if _shape.rotate:
            self.systems.sys_rotation.process(self.entities.entity_manager.entities)

    def _update(self):
        self.systems.sys_map.process(self.entities.entity_manager.entities)
        # 检测是否碰撞（触底、碰撞、左右界）
        self.systems.sys_collision.process(self.entities.entity_manager.entities)
        # 根据碰撞结果更新map
        self.systems.sys_map.process(self.entities.entity_manager.entities)
        if self.state.active:
            self.systems.sys_movement.process(self.entities.entity_manager.entities)

    def _render(self):
        self.systems.sys_render.process(self.entities.entity_manager.entities)

    def run(self):
        while self.running:
            self._handle_events()
            if not self.paused and not self.game_over:
                if not self.restart:
                    self._update()
                    self._render()
                else:
                    self._init()
            elif self.paused:
                self._render()
            pygame.display.update()
            self.game_manager.clock.tick(self.game_manager.config.FPS)
        pygame.quit()