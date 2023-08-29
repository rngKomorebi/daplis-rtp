# LinoSPAD2 app

Package with an application for real-time plotting of sensor population
for LinoSPAD2.

![Tests](https://github.com/rngKomorebi/LinoSPAD2-app/actions/workflows/tests.yml/badge.svg)
![Documentation](https://github.com/rngKomorebi/LinoSPAD2-app/actions/workflows/documentation.yml/badge.svg)

## Introduction

The main purpose of this application is real-time plotting of LinoSPAD2
sensor population for easier handling of the setup. Given the detector 
data acquisition is running and once a path to where data files should
be saved to, scripts constantly wait for the latest saved file, unpack
the data and plot it as a number of timestamps vs. pixel number.

This repo was separated from the [main](https://github.com/rngKomorebi/LinoSPAD2)
library of scripts for LinoSPAD2 data analysis. The reason is that
the app requires its own 'main.py' to run and having it as a standalone
makes it quite easy to generate an executable with [pyinstaller](https://pyinstaller.org/en/stable/).

## Installation and usage

To start using the package, one can download the whole repo. The 'main.py'
serves as the main hub for starting the app. "requirements.txt"
lists all packages required for this project to run. One can create
an environment for this project either using conda or install the
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
a separate virtual environment is highly recommended for faster and
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
Full path to the '.ui' files should be provided as pyinstaller does not
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

## How to contribute

This repo consists of two branches: 'main' serves as the release version
of the package, tested, and proved to be functional and ready to use, while
the 'develop' branch serves as the main hub for testing new stuff. To
contribute, the best way would be to fork the 'develop' branch and
submit via pull requests. Everyone willing to contribute is kindly asked
to follow the [PEP 8](https://peps.python.org/pep-0008/) and
[PEP 257](https://peps.python.org/pep-0257/) conventions.

## License and contact info

This package is available under the MIT license. See LICENSE for more
information. If you'd like to contact me, the author, feel free to
write at sergei.kulkov23@gmail.com.
