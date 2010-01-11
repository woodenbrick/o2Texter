#!/usr/bin/python

from DistUtilsExtra.command import *
from distutils.core import setup
import os
import glob 

PROGRAM_NAME = 'o2texter'
VERSION = '0.01'

glade = glob.glob("*.glade")
desc = """Send texts through o2 web interface to UK phones"""

long_desc = """The program requires that you have a o2 phone"""
setup ( name = PROGRAM_NAME,
        version = VERSION,
        description = desc,
        long_description = long_desc,
        author = 'Daniel Woodhouse',
        author_email = 'wodemoneke@gmail.com',
        license = 'GPLv3',
        packages = ['o2texter', "o2texter.authclients", "o2texter.authclients.ClientCookie"],
        data_files = [
            ('share/applications/', ['o2texter.desktop']),
            ('share/o2texter/', ["o2texter/texter.glade"]),
            ('bin/', ['bin/o2texter'])],
)
