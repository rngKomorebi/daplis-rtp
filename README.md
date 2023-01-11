# LinoSPAD2-app
A data analysis app for the LinoSPAD2 detector. This repo was separated from the main library
of scripts for data analysis for the LinoSPAD2 detector (https://github.com/rngKomorebi/LinoSPAD2).
The reasons are is that the app requires its own 'main.py' to run and having it as a standalone
makes it quite easy to generate an executable with pyinstaller (https://pyinstaller.org/en/stable/).

The "requirements.txt" lists all packages necessary for the app to run and it was generated
with pipreqs (https://pypi.org/project/pipreqs/).