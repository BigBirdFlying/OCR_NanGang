from distutils.core import setup
from Cython.Build import cythonize
import os

rootpath = os.getcwd()
excludes = ["__init__","__build__", "__install__", "venv", "ArNT"]


def get_file_list(path, mark):
    parents = os.listdir(path)
    for parent in parents:
        child = os.path.join(path, parent)
        if os.path.isdir(child):
            get_file_list(child, mark)
        else:
            ext = child.split('.')
            if ext[-1] == mark:
                file_path = child
                file_name = parent
                if not any(ex in file_path for ex in excludes):
                    os.chdir(path)
                    setup(name='hkj_ibkvision_char',
                          ext_modules=cythonize(file_name, compiler_directives={'language_level': 2}), )


get_file_list(rootpath, "py")
