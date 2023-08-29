# Introduction

The main purpose of this application is real-time plotting of LinoSPAD2
sensor population for easier handling of the setup. Given the detector 
data acquisition is running and once a path to where data files should
be saved to was set, scripts constantly wait for the latest saved file,
unpack the data, and plot it as a number of timestamps vs. pixel number.

This repo was separated from the [main](https://github.com/rngKomorebi/LinoSPAD2)
library of scripts for LinoSPAD2 data analysis. The reason is that
the app requires its own 'main.py' to run and having it as a standalone
makes it quite easy to generate an executable with [pyinstaller](https://pyinstaller.org/en/stable/).