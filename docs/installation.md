## Installation and usage

To start using the package, one can download the whole repo. The 'main.py'
serves as the main hub for starting the app. "requirements.txt"
lists all packages required for this project to run. One can create
an environment for this project either using conda or installing the
necessary packages using pip (for creating virtual environments using pip
see [this](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)).

Using pip:
```
pip install virtualenv
py -m venv NEW_ENVIRONMENT_NAME
PATH/TO/NEW_ENVIRONMENT_NAME/Scripts/activate
cd PATH/TO/THIS/PACKAGE
pip install -r requirements.txt
pip install -e .
```
Using conda:
```
conda create --name NEW_ENVIRONMENT_NAME
conda activate NEW_ENVIRONMENT NAME
cd PATH/TO/THIS/PACKAGE
conda install --file requirements.txt -c conda-forge
pip install -e .
```
Finally, to run the app, run the 'main.py' script.

### Executable

On Windows, to create an executable, one can run the following: first,
a separate virtual environment is highly recommended for a faster and
smoother experience with the app, as pyinstaller packs everything it
finds in the virtual environment; using pip:

```
pip install virtualenv
py -m venv PATH/TO/NEW_ENVIRONMENT_NAME
PATH/TO/NEW_ENVIRONMENT_NAME/Scripts/activate
```
where the last command activates the environment. Here, all the necessary
packages along with the app package itself should be installed. To do
this, run from the environment (given the package was downloaded):
```
cd PATH/TO/THIS/PACKAGE
pip install -r requirements.txt
pip install -e .
```
where the latter command installs the package itself in the environment.
To create the executable, pyinstaller should be installed, too:
```
pip install pyinstaller
```
Then, given the current directory is set to where the package is, run
```
pyinstaller --clean --onedir --noconsole main.py
```
which packs everything in the package for the "main.exe" executable
for the app. Options '--onedir' for installing everything into a single
directory and '--noconsole' for running the app without a console are
recommended. Additionally, in the '_tab.py' files, change the first
lines in the '__init__' functions to the following: 
```
def __init__(self, parent=None):
    super().__init__(parent)
    os.chdir(r"FULL\PATH\TO\LinoSPAD2-app\gui\ui")
    uic.loadUi(
        r"LiveTimestamps_tab_c.ui",
        self,
    )
    os.chdir("../..")
```
A full path to the '.ui' files should be provided as pyinstaller does not
handle relative paths, as it's implemented in the package. To run the app,
run 'main.exe' in the 'dist' folder.

If using conda, use the following chain of commands:
```
conda create --name NEW_ENVIRONMENT_NAME
conda activate NEW_ENVIRONMENT NAME
cd PATH/TO/THIS/PACKAGE
conda install --file requirements.txt -c conda-forge
conda install pyinstaller -c conda-forge
```
and the rest stay the same as for the installation using pip.