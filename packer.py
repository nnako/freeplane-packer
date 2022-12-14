#!/usr/bin/env python
#-*- coding: utf-8 -*-




#
# DESCRIPTION
#
# a small tool to export Freeplane maps together with its linked files into
# one single container file.
#
#
# AUTHOR
#
#   - nnako, 2022
#




# generals
from __future__ import print_function
import argparse
import pathlib
import os
import shutil
import re
import sys
import datetime
import logging

# application
import freeplane




__version__ = "0.3"




# logging
logging.basicConfig(
        format='%(name)s - %(levelname)-8s - %(message)s',
        level=logging.INFO,
        )




# check dependencies
if float(freeplane.__version__[:3]) < 0.7:
    print('[ ERROR  : please upgrade package "freeplane-io" to at least "v0.7" ]')
    sys.exit(1)




# packer class
class Packer(object):

    def __init__(self, *fargs, **fkwargs):




        #
        # store main CLI argument
        #

        if fargs:
            self._id = fargs[0].lower()
        elif fkwargs and "id" in fkwargs.keys():
            self._id = fkwargs['id']
        else:
            self._id = ""




        #
        # when called from command line
        #

        # do this only if called from the command line
        if self._id == 'cli':




            #
            # define main command line interface
            #

            # define information
            parser = argparse.ArgumentParser(
                    description='Freeplane Packer',
                    usage='''reqmgt <command> [<args>]

            Possible commands are:
            pack    create Freeplane container file
            unpack  [ not implemented, yet ]
            ''')

            # define command argument
            parser.add_argument(
                    'command',
                    help='Subcommand to run'
                    )




            #
            # read out CLI and execute main command
            #

            # parse_args defaults to [1:] for args, but you need to
            # exclude the rest of the args too, or validation will fail

            # get main arguments from user
            args = parser.parse_args(sys.argv[1:2])

            # check if command is provided in script
            if not hasattr(self, args.command):

                logging.error('Unrecognized command. EXITING.')
                parser.print_help()
                sys.exit(1)

            # use dispatch pattern to invoke method with same name
            getattr(self, args.command)()


    def pack(self,
            mmpath="",
            mmxpath="",
            log_level='info',
            ):




        #
        # create attributes from CLI or API arguments
        #

        # module was started from command line?
        if self._id == "cli":

            # read from command line
            parser = argparse.ArgumentParser(
                    description='pack mindmap contents into container file')
            args = parseOptArgs(parser)

            # write into object
            self._mmpath = args.mmpath
            self._mmxpath = args.mmxpath
            self._log_level = args.log_level

        # module was called from function
        else:

            # read from function arguments and write into object
            self._mmpath = mmpath
            self._mmxpath = mmxpath
            self._log_level = log_level




        #
        # adjust logging level to user's wishes
        #

        if self._log_level.lower() == "debug":
            logging.getLogger().setLevel(logging.DEBUG)
        elif self._log_level.lower() == "info":
            logging.getLogger().setLevel(logging.INFO)
        elif self._log_level.lower() == "warning":
            logging.getLogger().setLevel(logging.WARNING)
        elif self._log_level.lower() == "error":
            logging.getLogger().setLevel(logging.ERROR)
        else:
            logging.getLogger().setLevel(logging.WARNING)
            logging.warning("log log level mismatch in user arguments. setting to WARNING.")




        #
        # connect to mindmap as information source
        #

        # here, the desired mindmap will be loaded for being parsed

        # open mindmap
        mindmap           = freeplane.Mindmap(self._mmpath)

        # debug
        logging.debug(f'mindmap "{self._mmpath}" will be exported into a container')




        #
        # expand user arguments
        #

        # in case, the user didn't provide all the specific input arguments,
        # now some default values are expanded in order to prevent the user
        # from the obligation to provide all of them using the command line
        # or graphical user interface.

        if not self._mmxpath:

            # set to be corresponding as mindmap
            self._mmxpath = self._mmpath+"x"




        #
        # get list of linked file paths
        #

        # walk through entire mindmap and find links to files within the local
        # file system. web links will be prevailed. it would be possible to
        # convert web content e.g. to PDF and place it within the container.

        lstFpnodes = mindmap.find_nodes()
        dicHyperlinks = {}

        # take each freeplane node within the mindmap
        for fpnode in lstFpnodes:




            #
            # IF link is present in node
            #

            # get sanitized path string (no backslash)
            _path = fpnode.hyperlink.replace("\\", "/")
            if _path:




                #
                # sanitize file link
                #

                # at this position, possible formats within the link attribute
                # might be one of the following. when a mm file, there can also
                # be appended a hash symbol followed by an NODE ID string
                #
                # - file:/C:/some-path/filename.ext (Windows)
                # - file://some-absolute-path/filename.ext (Linux)
                # - C:/some-absolute-path/filename.ext (Windows)
                # - /some-absolute-path/filename.ext (Linux)
                # - some-relative-path/filename.ext
                # - filename.ext

                # remove leading protocol token
                _token = 'file:/'
                if _path.lower().startswith(_token):

                    # remove file uri token
                    _path = _path[len(_token):]




                #
                # disregard all other link types
                #

                #  - no other link types (http, ...)
                #  - no local hyperlinks to other nodes
                #  - no external hyperlinks to mindmap nodes -> just the mindmap files

                # look for other protocol tokens (they start with at least 2
                # characters and then a colon and a slash)

                _match = re.search(r'^([A-z]{2,}:/)', _path)
                if _match:
                    logging.info(f'file "{_path}" uses a protocol token "{_match[1]}" which is not evaluated, here.')
                    continue

                if _path.startswith('#'):
                    logging.debug(f'file "{_path}" uses a local node link. will be disregarded, here.')
                    continue




                #
                # remove possible appended freeplane specifics
                #

                # remove hyperlink to node in external mindmap
                _pos = _path.rfind('#')
                if _pos > -1:
                    _path = _path[:_pos]




                #
                # initialize details list if not already done
                #

                if _path not in dicHyperlinks.keys():
                    dicHyperlinks[_path] = []




                #
                # create new dictionary entry
                #

                dicHyperlinks[_path].append(
                        {
                        'nodeid': fpnode.id,
                        'type': "file",
                        }
                        )




        #
        # get list of in-line image paths
        #

        # walk through entire mindmap and find paths to images within the local
        # file system. web links will be prevailed.

        # take each freeplane node within the mindmap
        for fpnode in lstFpnodes:




            #
            # IF in-line image is present in node
            #

            _imagepath = fpnode.imagepath
            if _imagepath:




                #
                # initialize details list if not already done
                #

                if _imagepath not in dicHyperlinks.keys():
                    dicHyperlinks[_imagepath] = []




                #
                # get image size
                #

                _imagesize = fpnode.imagesize




                #
                # store image details
                #

                # create new dictionary entry
                dicHyperlinks[_imagepath].append(
                        {
                        'nodeid': fpnode.id,
                        'type': "image",
                        'size': _imagesize,
                        }
                        )




        #
        # get list of html image sources
        #

        # walk through entire mindmap and find paths to images within the local
        # file system. web links will be prevailed.

        # take each freeplane node within the mindmap
        for fpnode in lstFpnodes:




            #
            # collect all html image nodes present
            #

            lstImageElements = []

            # check for richcontent element
            richnode = fpnode._node.find('richcontent')
            if richnode is not None:

                # check for html element
                htmlnode = richnode.find('html')
                if htmlnode is not None:

                    # check for html body element
                    htmlbody = htmlnode.find('body')
                    if htmlbody is not None:

                        # check for image elements directly below body tag
                        lstImageElements = []
                        lstImageElements.extend(htmlbody.findall('img'))

                        # and now below paragraph elements
                        for _element in htmlbody.findall('p'):
                            lstImageElements.extend(_element.findall('img'))




            #
            # insert paths into dictionary
            #

            for _element in lstImageElements:

                _imagepath = _element.get("src")




                #
                # skip http images
                #

                if _imagepath.startswith("http:/") \
                        or _imagepath.startswith("https:/"):
                    logging.debug(f'web-linked images like "{_imagepath}" will not be changed.')
                    continue




                #
                # initialize details list if not already done
                #

                if _imagepath not in dicHyperlinks.keys():
                    dicHyperlinks[_imagepath] = []




                #
                # store image details
                #

                # create new dictionary entry
                dicHyperlinks[_imagepath].append(
                        {
                        'nodeid': fpnode.id,
                        'type': "html_image",
                        'element': _element,
                        }
                        )




        #
        # build container
        #

        # create container folder structure
        _containerfolder = self._mmxpath + "_"
        pathlib.Path(_containerfolder).mkdir(parents=True, exist_ok=True)
        _filesfolder = os.path.join(_containerfolder, "files")
        pathlib.Path(_filesfolder).mkdir(parents=True, exist_ok=True)

        # set mindmap's path as current path
        os.chdir(pathlib.Path(self._mmpath).parent)

        lstAbsPaths = []
        for _path, _infolist in dicHyperlinks.items():




            #
            # localize original file
            #

            # convert relative to absolute path. if the path starts with dots
            # or if the path does not start with a drive letter or a slash.

            if re.search(r'^([A-z]{2,})', _path) is not None or _path.startswith('.'):
                _path = os.path.abspath(_path)




            #
            # IF source file exists
            #

            if not os.path.isfile(_path):
                for _info in _infolist:
                    logging.warning(f'file "{_path}" was NOT found as specified in node "{_info["nodeid"]}"')
            else:
                logging.info(f'file "{_path}" was found')




                #
                # IF file's basename was already seen
                #

                # in case, the current file has a name which does exist at
                # another path location, the file name is to be modified within
                # the container in order to keep both files. so, count how many
                # times the "same" path name exists. as in windows os upper or
                # lower case is not regarded, this might otherwise lead to
                # overwrite of container files.

                _count = lstAbsPaths.count(_path.lower().replace("\\", "/"))

                # same with the basenames
                lstBasenames = [os.path.basename(_path) for _path in lstAbsPaths]
                _count += lstBasenames.count(os.path.basename(_path).lower())




                #
                # paste file into container folder
                #

                # already existing files within the container will be replaced
                # by the fresh ones

                _basename = os.path.basename(_path)

                # adjust name if already multiple identical basenames transferred
                if _count:
                    _basename = os.path.splitext(_basename)[0] \
                            + '__' \
                            + str(_count) \
                            + os.path.splitext(_basename)[1]

                # paste file
                shutil.copyfile(
                    _path,
                    os.path.join(
                        _filesfolder,
                        _basename,
                        )
                    )

                # remember the file path as being pasted into folder
                lstAbsPaths.append(_path.lower().replace("\\", "/"))




                #
                # walk through infolist
                #

                for _info in _infolist:




                    #
                    # evaluate link type
                    #

                    if _info['type'] == "image":




                        #
                        # link node's image section with new file location
                        #

                        # find mindmap node
                        _node = mindmap.find_nodes(id=_info['nodeid'])[0]

                        # replace image element in mindmap
                        _node.set_image(
                                link='./files/' + _basename,
                                size=_imagesize,
                                )




                    elif _info['type'] == "html_image":




                        #
                        # link node's html image with new file location
                        #

                        # pick specific image node
                        _img = _info['element']

                        # replace image path in node
                        _img.set(
                                "src",
                                './files/' + _basename,
                                )




                    else:




                        #
                        # link node to new file location
                        #

                        # find mindmap node
                        _node = mindmap.find_nodes(id=_info['nodeid'])[0]

                        # replace hyperlink path in mindmap
                        _node.hyperlink = 'files/' + _basename




        #
        # save modified mindmap file into container folder
        #

        mindmap.save(
                os.path.join(
                    _containerfolder,
                    os.path.basename(self._mmpath),
                    )
                )




        #
        # build ZIP container
        #

        # create container
        shutil.make_archive(self._mmxpath, 'zip', _containerfolder)

        # rename container
        shutil.move(self._mmxpath + ".zip", self._mmxpath)




        #
        # remove container folder
        #

        shutil.rmtree(_containerfolder)




#
# ARGUMENT PARSING
#

def parseOptArgs(parser):




    #
    # define general optional arguments
    #

    parser.add_argument(
            'mmpath',
            default='',
            help='mindmap file path. where to find the mindmap within the local file system.',
            )
    parser.add_argument(
            '--mmxpath',
            default='',
            help='container file path. this file will contain the mindmap and further files.',
            )
    parser.add_argument(
            '--log-level',
            default='info',
            help=   'log messages will be displayed only if severity level is matching or above.' + \
                    ' options are "debug", "info", "warning" or "error"',
            )




    #
    # evaluate command line arguments
    #

    # evaluate subcommand line arguments
    args = parser.parse_args(sys.argv[2:])

    # return arguments
    return args




#
# MAIN ROUTINE
#

if __name__ == "__main__":




    #
    # run the application
    #

    app = Packer('cli')
