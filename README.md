# Data Analysis Package for LInoSpad - Real-Time Plotting (DAPLIS-RTP).

Package with an application for real-time plotting of sensor population
for LinoSPAD2. A spin-off of the main data analysis package [daplis](https://github.com/rngKomorebi/daplis)

![Tests](https://github.com/rngKomorebi/LinoSPAD2-app/actions/workflows/tests.yml/badge.svg)
![Documentation](https://github.com/rngKomorebi/LinoSPAD2-app/actions/workflows/documentation.yml/badge.svg)
![PyPI - Version](https://img.shields.io/pypi/v/daplis-rtp)
![PyPI - License](https://img.shields.io/pypi/l/daplis-rtp)

Full documentation (including all docstrings) can be found [here](https://rngkomorebi.github.io/daplis-rtp/).

## Introduction

The main purpose of this application is real-time plotting of LinoSPAD2
sensor population for easier alignment: introducing the changes into the setup,
one can see the results instantly using this application. Given the detector 
data acquisition is running and once a path to where data files should
be saved to is provided, the program constantly checks for the latest saved file, then 
unpacks the data, and plots it as a number of photons detected in each pixel.

Additionally, a separate tab for checking the data quality by looking at 
the distribution of timestamps across the whole acquisition cycle is provided: 
if the distribution is uniform, the data is ok. The third tab can be used
for plotting the number of photons from two pixels vs the data file as two 
curves with primary application in Mach-Zehnder interferometer setup.
A fourth tab plots both sensor halves at once from two boards, and a fifth
drives a two-board synchronized acquisition over TCP.

While aligning, a few things are worth knowing about:

- The **"Peak in view"** box reports the brightest pixel, the centroid, the
  FWHM and the summed rate over the x-limits currently shown. The centroid is
  the one to watch while walking a mirror — it moves smoothly where the
  brightest pixel jumps.
- **Ctrl+click** a pixel on the plot to mask it, and Ctrl+click again to
  unmask. The trace updates immediately.
- The **"TDC memory"** box says how close the readout is to filling up. A TDC
  that fills drops the rest of the acquisition cycle with no sign of it in the
  data file, so raise `Timestamps` when it warns.
- **File → Export plotted data** (`Ctrl+E`) saves the numbers behind the plot
  as `.csv` or `.npz`, with the board, the firmware and the settings recorded
  in the file. Read a CSV back with
  `pandas.read_csv(path, comment="#")`.
- Each tab remembers its folder and settings between sessions.

This repo was separated from the [main](https://github.com/rngKomorebi/daplis)
library of scripts for LinoSPAD2 data analysis. The reason is that
the app requires its own 'main.py' to run and having it as a standalone
makes it quite easy to generate an executable with [pyinstaller](https://pyinstaller.org/en/stable/).

## Installation and how to run the application

To start using the package, one can download the whole repo. The 'main.py'
serves as the main hub for starting the app. "requirements.txt"
lists all packages required for this project to run. One can create
an environment for this project either using conda or install the
necessary packages using pip (for creating virtual environments using pip
see [this](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)).

Using pip, one can check if the virtualenv package is installed in the
current python environment:
```
pip show virtualenv
```
or install it directly using:
```
pip install virtualenv
```
To create a new environment (it is highly recommended
to keep the virtual environments in a separate folder), run the following:
```
py -m venv PATH/TO/NEW/ENVIRONMENT
```
E.g., for creating a 'daplis-rtp' environment, one can run (on Windows):
```
py -m venv C:/Users/USERNAME/venvs/daplis-rtp
```
To activate the environment, run (on Windows):
```
PATH/TO/NEW/ENVIRONMENT/Scripts/activate
```
or, on Linux:
```
source PATH/TO/NEW/ENVIRONMENT/bin/activate
```

There, the package can be installed from [PyPI](https://pypi.org/project/daplis-rtp/):
```
pip install daplis-rtp
```

The application can be run from the command line or terminal via
```
daplis-rtp
```

### Installation: using source code

Alternatively, one can run the application using the source code. To do it this way, first, create a virtual environment for the package by running the following set of commands (on Windows):

```
pip install virtualenv
py -m venv NEW_ENVIRONMENT_NAME
PATH/TO/NEW_ENVIRONMENT_NAME/Scripts/activate
```

Then, download the zip with the source code of this package from github, 
extract and change directory to the folder with the code. There, first install the required packages ("requirements.txt"), and, finally, install the package itself locally.
```
cd PATH/TO/THIS/PACKAGE
pip install -r requirements.txt
pip install -e .
```

Finally, to run the app, run the 'main.py' script.

### Executable from the source code using pyinstaller

On Windows, to create an executable, one can do the following: first,
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
recommended.

## Themes and colours

Nothing has to be edited to change how the app looks. Open
**View → Preferences** (or press `Ctrl+,`), or **View → Theme**, and pick
one of the ten:

| theme | for |
|---|---|
| Cyberpunk | the default: a near-black figure with the glow under the traces |
| Midnight | the same dark window with the glow off, for a fast stream |
| Night wave | synthwave neon on violet, with the glow |
| Blueprint | a CAD drawing: white and ice-blue lines on deep navy |
| High contrast | pure black, with trace colours that stay apart for the common forms of colour blindness |
| Daylight | a plain white figure, for a bright room |
| Komorebi | deep gold and forest green on parchment |
| Earth | terracotta and olive on aged paper |
| Solarized | Ethan Schoonover's light palette |
| Daplis (publication) | the house palette — rebeccapurple and darkorange on white, colourblind-safe. The one to export a figure in. |

The last six are ports of the matplotlib styles in
[komorebi_mpl](https://github.com/rngKomorebi/komorebi_mpl).

Any colour in a theme can then be changed - the accent, the figure and
plot backgrounds, the axes, the grid, the markers, and each trace - along
with the interface and plot font sizes and the glow and grid switches.
The Preferences window is not modal and every change applies at once, to
plots already on screen as well as new ones, so a colour can be chosen by
watching the plot rather than from memory.

The settings are stored per user, so two people sharing a machine keep
their own, and they survive an upgrade.

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
