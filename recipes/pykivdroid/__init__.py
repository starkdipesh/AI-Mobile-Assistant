"""
Recipe for pykivdroid - Android Speech/TTS
"""
from pythonforandroid.recipe import PythonRecipe

class PykivdroidRecipe(PythonRecipe):
    version = '0.1.0'
    url = 'https://github.com/kivy/pykivdroid/archive/refs/heads/master.zip'
    depends = ['setuptools', 'pyjnius', 'android']
    call_hostpython_via_targetpython = False
    
    def get_recipe_env(self, arch=None, with_flags_in_cc=True):
        env = super().get_recipe_env(arch, with_flags_in_cc)
        return env

recipe = PykivdroidRecipe()
