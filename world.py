#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Author      : Bluzy
Date        : 2023/06/28 10:35:06
Contact     : zoe4896@outlook.com
Description : 
'''
import numpy as np

class World:
    def __init__(self, playfield_width, playfield_height) -> None:
        self.playfield_width = playfield_width
        self.playfield_height = playfield_height
        self.mat = np.zeros((self.playfield_height, self.playfield_width), dtype=np.int0)