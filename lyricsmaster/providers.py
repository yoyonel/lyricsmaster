# -*- coding: utf-8 -*-

"""Main module.

This module defines the Api interface for the various Lyrics providers.
All lyrics providers inherit from the base class LyricsProvider.

"""

# We use abstract methods to ensure that all future classes inheriting from LyricsProvider will
# implement the required methods in order to have a nice and consistent API.

# We use gevent in order to make asynchronous http requests while downloading lyrics.
# It is also used to patch the socket module to use SOCKS5 instead to interface with the Tor controller.

# Python 2.7 compatibility
# Works for Python 2 and 3

try:
    from importlib import reload
except ImportError:
    try:
        from imp import reload
    except:
        pass

# Importing the app models and utilities

if __name__ == "__main__":
    pass
