from pythonforandroid.recipe import CythonRecipe
import os
import sys

class HfstolRecipe(CythonRecipe):
    version = '0.0.13'
    url = 'https://files.pythonhosted.org/packages/a7/e1/7d23601dc4520b667903939406106495b42332ad0f0429f2f7342a48480c/hfst-optimized-lookup-{version}.tar.gz'
    name = 'hfst_optimized_lookup'

    # Libraries it depends on
    depends = ['setuptools', 'pytest', 'black', 'twine', 'mypy', 'pytest-mypy', 'sphinx', 'sphinx-rtd-theme', 'm2r2'] 


    call_hostpython_via_targetpython = False
    install_in_hostpython = True

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['LDFLAGS'] += ' -lc++_shared'
        return env


recipe = HfstolRecipe()