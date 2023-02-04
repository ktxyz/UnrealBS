import os
import json
from threading import Lock

from UnrealBS.Common.Recipes import Recipe


class RecipeHandler:
    def __init__(self):
        self.recipes_lock = Lock()
        self.recipes = []

        self.scan_recipes()

    def get_recipe(self, target):
        try:
            self.recipes_lock.acquire()

            for recipe in self.recipes:
                if recipe.target == target:
                    return recipe
            return None
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
            return True
        finally:
            self.recipes_lock.release()

    def scan_recipes(self):
        cwd = os.getcwd()
        # TODO
        # Make this configurable
        directory = os.path.join(cwd, 'Examples/Linux')
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                file_path = os.path.join(directory, filename)
                with open(file_path, 'r') as f:
                    self.learn_recipe(json.load(f))
                    print(f'Registered new {self.recipes[-1].target} recipe')
