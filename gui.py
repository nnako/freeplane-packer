#!/usr/bin/python
# -*- coding: utf-8 -*-




#
# import necessary modules
#

import argparse
import sys
import os
import locale

# application
from gooey import Gooey, GooeyParser
import packer




#
# application version
#

__version__ = "1.0"




#
# ensure intuitive CLI use
#

# if arguments are added, Gooey GUI should not be active
# https://github.com/chriskiehl/Gooey/issues/449

if len(sys.argv) >= 2:
    if not "--ignore-gooey" in sys.argv:
        sys.argv.append("--ignore-gooey")




#
# argument parser
#

@Gooey(
        program_name="Freeplane Packer GUI v" + __version__ + " [ framework v" + packer.__version__ + " ]",
        program_description="pack mindmap and linked files into one container",
        navigation="TABBED",
        default_size=(800,650),

        # the correct choice of character encoding is critical for proper GUI
        # operation. when compiling / building an executable aiming at using
        # the GUI as a deployed application, the encoding should be set to
        # cp1251. when compiling / building for use in development mode (in
        # source code) while using the GUI, the encoding should be set to
        # utf-8.

        # encoding='cp1251',  # for build version starting in GUI mode
        encoding='utf-8',   # for interactive version starting in GUI mode
        )
def parseOptArgs():




    #
    # define GUI structure
    #

    # define parser
    parser = GooeyParser(
            description='pack mindmap and files into container',
            usage='freeplane-packer [<args>]')

    # define sub-parsers
    subs = parser.add_subparsers(help="commands", dest="command")
    pack = subs.add_parser(
            "pack",
            prog="pack",
            ).add_argument_group(
                    "create Freeplane container",
                    )
    unpack = subs.add_parser(
            "unpack",
            prog="unpack",
            ).add_argument_group(
                    "extract files from Freeplane container",
                    )




    #
    # define arguments for packer
    #

    pack.add_argument(
            '--mmpath',
            default='',
            widget='FileChooser',
            required=True,
            help='mindmap file path. where to find the mindmap within the local file system.',
            gooey_options=dict(wildcard="Freeplane mindmap files (.mm)|*.mm")
            )
    pack.add_argument(
            '--mmxpath',
            default='',
            widget='FileSaver',
            help='container file path. this file will contain the mindmap and further files.',
            gooey_options=dict(wildcard="MMX files (.mmx)|*.mmx")
            )
    pack.add_argument(
            '--log-level',
            default='info',
            help='log messages will be displayed only if severity level is matching or above. options are "debug", "info", "warning" or "error"',
            )




    #
    # evaluate command line arguments
    #

    # evaluate subcommand line arguments
    args = parser.parse_args()

    # return arguments
    return args




#
# IF executed via CLI
#

if __name__ == "__main__":




    #
    # get CLI arguments
    #

    arguments = parseOptArgs()




    #
    # evaluate tabbed command
    #

    # create application object
    app = packer.Packer()

    if arguments.command == "pack":




        # print separation
        print('\n---- PACKING FREEPLANE CONTAINER')




        #
        # create clickview
        #

        app.pack(
                mmpath=arguments.mmpath,
                mmxpath=arguments.mmxpath,
                log_level=arguments.log_level,
                )
