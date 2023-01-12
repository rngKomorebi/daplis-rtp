# LinoSPAD2-app
A data analysis app for the LinoSPAD2 detector. This repo was separated from the main library
of scripts for data analysis for the LinoSPAD2 detector (https://github.com/rngKomorebi/LinoSPAD2).
The reasons are is that the app requires its own 'main.py' to run and having it as a standalone
makes it quite easy to generate an executable with pyinstaller (https://pyinstaller.org/en/stable/).

The "requirements.txt" lists all packages necessary for the app to run and it was generated
with pipreqs (https://pypi.org/project/pipreqs/). To install the required packages try 1) using pip
"pip install -r requirements.txt", 2) using conda "conda install --file requirements.txt -n LinoSPAD2-app",
where the latter option points to the environment "LinoSPAD2-app". It's better to install into a separate
environment as the pyinstaller will pack everything from the environment together with the app during creation
of an executable.