#!/usr/bin/env python

""""""

try:
    import tornado
except ImportError:
    raise ImportError("tornado library not installed. Install tornado. https://github.com/facebook/tornado")

version = "0.0.1"
version_info = (0, 0, 1)

from errors import Error, InterfaceError
from client import Client, AJAMClient

