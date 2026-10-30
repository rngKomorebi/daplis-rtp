"""Standard-library names that moved after the oldest Python supported.

``importlib.resources.files`` arrived in 3.9. On 3.8 the same function
comes from the ``importlib_resources`` backport, which the package
depends on for that version only.

"""

try:
    from importlib.resources import files
except ImportError:  # Python 3.8
    from importlib_resources import files

__all__ = ["files"]
