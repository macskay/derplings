import os
import logging

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

__version__ = (0, 0, 0)
__all__ = ['config']


config = configparser.ConfigParser()
logger = logging.getLogger('zkit.__init__')
filename = os.path.join(os.path.dirname(__file__), 'data', 'zkit.ini')
config.read(filename)
