# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.3] - 2025-05-04

Fixes.

### Changed

- Updated MANIFEST.in so that it includes the '.txt' files to pypi.

## [1.1.2] - 2025-05-04

Mask call update.

### Changed

- How the '.txt' files with masks are called. No hard reversing on the path tree, works with every way of installation (manual, from github, pypi, distributable).

## [1.1.1] - 2025-01-28

Setup-file update.

### Changed

- Updated README with instruction on how to install and run the program.

- Added requirement for the 'qdarkstyle' package to the 'pyproject.toml' 
file.

## [1.1.0] - 2025-01-28

Adapted the package for installation via 'pip install'. Now, after
the package is installed, one can run it via 'daplis-rtp' command.

### Added

- Requirement for the 'qdarkstyle' package for dark-themed GUI.

### Changed

- The 'pyproject.toml' setup file: added a link to the 'main.py' so that
after installation the program can be run via 'daplis-rtp' from the 
terminal/command line.

### Removed

- The '.ui' files since they were changed to '.py'. Also, removed the
back-up copies of the second tab (single pixel histogram) UI.

## [1.0.1] - 2025-01-26

Minor fixes in all tabs, specifically regarding the canvas widget.

### Changed

- Fontsize in the plot widget in all three tabs.

## [1.0.0] - 2025-01-24

First official release to PyPI.

### Added

- This changelog.

### Changed

- Installation files: installation is now done using the 'pyproject.toml' 
file instead of 'setup.py'.

## [0.9.9] - 2025-01-24

Preparing the package for the official release

### Added

- Two boxes for the two top-most pixels (looked for automatically) in 
the live-timestamps tab for easier alignment.

### Fixed

### Changed

- The name of the package.

- The layout and size of the boxes in all tabs.

- The single-pixel-histogram tab to match its style to the other
two tabs.

### Removed

- Unused "mask_NL11_all.txt".
- Unused masks in "params/masks/old".
- Test leftovers in "tests/test_data/results".
