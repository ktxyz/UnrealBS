import os
import json
from threading import Lock

from UnrealBS.Common.Recipes import Recipe
from UnrealBS.Config import Config


class RecipeNotFound(Exception):
    pass

class RecipeHandler:
    def __init__(self, server):
        self.config = Config()
        self.server = server

        self.recipes_lock = Lock()
        self.recipes = []

        self.scan_recipes()

    def get_list(self):
        try:
            self.recipes_lock.acquire()
            return self.recipes
        finally:
            self.recipes_lock.release()

    def get_recipe(self, target):
        try:
            self.recipes_lock.acquire()

            for recipe in self.recipes:
                if recipe.target == target:
                    return recipe
            raise RecipeNotFound
        finally:
            self.recipes_lock.release()

    def learn_recipe(self, recipe_data):
        try:
            self.recipes_lock.acquire()

            new_recipe = Recipe(recipe_data)

            for recipe in self.recipes:
                if recipe.target == new_recipe.target:
                    return False

            self.recipes.append(new_recipe)

            if new_recipe._repeat_times is not None:
                self.config.server_logger.info(f'Found repeating recipe[{new_recipe.target}]')
                self.server.order_handler.repeat_order(new_recipe)
            return True
        finally:
            self.recipes_lock.release()

    def scan_recipes(self):
        cwd = os.getcwd()
        if os.path.isabs(self.config.args.recipe_dir):
            directory = self.config.args.recipe_dir
        else:
            directory = os.path.join(cwd, self.config.args.recipe_dir)
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                file_path = os.path.join(directory, filename)
                with open(file_path, 'r') as f:
                    self.learn_recipe(json.load(f))
                    self.config.server_logger.info(f'Registered new {self.recipes[-1].target} recipe')
