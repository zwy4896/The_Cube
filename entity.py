#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Author      : Bluzy
Date        : 2023/06/26 14:31:26
Contact     : zoe4896@outlook.com
Description : 
'''

# 实体管理器
class EntityManager:
    def __init__(self):
        self.entities = {}

    def create_entity(self, id):
        entity = Entity()
        if id not in self.entities:
            self.entities[id] = [entity]
        else:
            self.entities[id].append(entity)
        # self.entities.append(entity)
        return entity

    def destroy_entity(self, entity):
        self.entities.remove(entity)

# 实体类
class Entity:
    def __init__(self):
        self.components = {}

    def add_component(self, component):
        component_type = type(component)
        self.components[component_type] = component

    def remove_component(self, component_type):
        if component_type in self.components:
            del self.components[component_type]

    def has_component(self, component_type):
        return component_type in self.components

    def has_components(self, *component_types):
        return all(self.has_component(component_type) for component_type in component_types)

    def get_component(self, component_type):
        return self.components.get(component_type)
    
    def reset_position(self, initial_position):
        self.position.x = initial_position.x
        self.position.y = initial_position.y