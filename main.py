#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Author      : Bluzy
Date        : 2023/06/26 14:35:34
Contact     : zoe4896@outlook.com
Description : 
'''

from game import Game
import yaml

def get_config(file_path):
    config = yaml.safe_load(open(file_path, 'r'))
    return config

if __name__ == '__main__':
    config = get_config('config.yaml')
    game = Game(config)
    game.run()