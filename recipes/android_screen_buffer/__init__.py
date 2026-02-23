"""
Recipe for android_screen_buffer - Screen capture
"""
from pythonforandroid.recipe import PythonRecipe

class AndroidScreenBufferRecipe(PythonRecipe):
    version = '0.1.0'
    url = 'https://github.com/Android-for-Python/AndroidScreenBuffer/archive/refs/heads/main.zip'
    depends = ['setuptools', 'pyjnius', 'android']
    call_hostpython_via_targetpython = False

recipe = AndroidScreenBufferRecipe()
