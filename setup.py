from cx_Freeze import setup


build_exe_options = {
    'include_files': ['data'],
    'excludes': ['tkinter', 'unittest'],
}

setup(
    name='Computergenesis',
    version='0.1.0',
    description='shooter game where you fight computers in medieval times',
    options={'build_exe': build_exe_options},
    executables=[{'script': 'main.py', 'base': 'gui'}],
)

