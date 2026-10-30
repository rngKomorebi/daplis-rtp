"""The GUI as it stood before the 1.5 rebuild, kept for reference.

Nothing in the running application imports from here. These are the
five tabs as they were - three generated from ``.ui`` files by
``pyuic`` and two built by hand - together with the three canvas
modules they shared and the ``.ui`` sources in ``ui/raw_ui``.

They are kept because they are the reference for what the rebuilt
tabs are supposed to do: every control, every default and every
error message here has a counterpart in ``gui/tabs``. They still
import - the paths were rewritten when they moved - so a behaviour
that looks wrong in the new application can be compared against the
old one rather than argued about.

They are not maintained. Nothing here follows the theme, and nothing
here is measured by ``tests/test_tab_geometry.py``.

"""
