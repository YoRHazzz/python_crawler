import sys
from shutil import rmtree
from os.path import exists
from os import remove

build_dir_flag = False
pycache_dir_flag = False
spec_file_flag = False

if exists("./build"):
    rmtree("./build")
    build_dir_flag = True
else:
    print("build 文件夹不存在")

if exists("./__pycache__"):
    rmtree("./__pycache__")
    pycache_dir_flag = True
else:
    print("__pycache__ 文件夹不存在")

if len(sys.argv) == 2:
    file_name = "./"+sys.argv[1].split('.')[0]+".spec"
    if exists(file_name):
        remove(file_name)
        spec_file_flag = True
    else:
        print(file_name, "文件不存在")

print("bulid: ", build_dir_flag,
      " pycache: ", pycache_dir_flag,
      " spec: ", spec_file_flag,
      "\npyinstaller_clean finish")
