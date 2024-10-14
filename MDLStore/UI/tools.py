import os
import sys
from pathlib import Path

for p in Path('./').rglob('*.ui'):
    path, ext = os.path.splitext(os.path.abspath(str(p)))
    file_name = os.path.basename(path)
    path = os.path.dirname(path)
    print(path)
    dst = os.path.join(path, 'Ui_' + file_name + '.py')
    command = '{0} -m PyQt5.uic.pyuic --from-imports -x -o {1} {2}'.format(
        sys.executable, dst, os.path.abspath(str(p)))
    os.system(command)
    print(p, file_name)