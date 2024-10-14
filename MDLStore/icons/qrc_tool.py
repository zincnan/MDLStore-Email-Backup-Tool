import os
import sys
import subprocess

def compile_qrc(qrc_file_, output_file_):
    command = ['pyrcc5', '-o', output_file_, qrc_file_]
    try:
        subprocess.run(command, check=True)
        print(f'Successfully compiled {qrc_file_} to {output_file_}')
    except subprocess.CalledProcessError as e:
        print(f'Failed to compile {qrc_file_}')
        print(e)

# 示例使用
qrc_file_path = r"E:\Xsoftware\Python\workstation\MDLStore_v1.0\MDLStore\icons\images.qrc"
output_file = r"E:\Xsoftware\Python\workstation\MDLStore_v1.0\MDLStore\images_rc.py"

# 编译 QRC 文件
compile_qrc(qrc_file_path, output_file)
