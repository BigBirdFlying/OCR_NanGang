import os
import shutil

rootpath = os.getcwd()
savepath = "C:/hkj_ibkvision_char"
excludes = ["__pycache__", "build", "dist", ".idea", "venv"]


def get_file_list(path, mark):
    parents = os.listdir(path)
    for parent in parents:
        child = os.path.join(path, parent)
        if os.path.isdir(child):
            get_file_list(child, mark)
        else:
            ext = child.split('.')
            if ext[-1] == mark and (not any(ex in child for ex in excludes)):
                save_dir = path.replace(rootpath, savepath)
                if not os.path.isdir(save_dir):
                    os.makedirs(save_dir)
                save = child.replace(rootpath, savepath)
                print(save)
                shutil.move(child, save)


get_file_list(rootpath, "pyd")
