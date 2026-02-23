"""
Recipe for pvporcupine - Wake word detection
"""
from pythonforandroid.recipe import PythonRecipe

class PvporcupineRecipe(PythonRecipe):
    version = '2.2.1'
    url = 'https://files.pythonhosted.org/packages/source/p/pvporcupine/pvporcupine-{version}.tar.gz'
    depends = ['setuptools']
    call_hostpython_via_targetpython = False
    
    def get_recipe_env(self, arch=None, with_flags_in_cc=True):
        env = super().get_recipe_env(arch, with_flags_in_cc)
        return env

recipe = PvporcupineRecipe()
