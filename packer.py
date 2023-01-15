#!/usr/bin/env python3
"""A small tool to export Freeplane maps together with its linked files into one single container file.

AUTHOR - nnako, 2022
"""
from __future__ import print_function

import argparse
import logging
import os
import pathlib
import re
import shutil
import sys

import freeplane

__version__ = "0.3"

logging.basicConfig(
    format='%(name)s - %(levelname)-8s - %(message)s',
    level=logging.INFO,
)

if float(freeplane.__version__[:3]) < 0.7:
    print('[ ERROR  : please upgrade package "freeplane-io" to at least "v0.7" ]')
    sys.exit(1)


class Packer(object):

    def __init__(self, *fargs, **fkwargs):
        self._store_main_cli_argument(fargs, fkwargs)
        if self._is_module_started_from_command_line():
            parser = self._define_main_command_line_interface()
            self._read_out_cli_and_execute_main_command(parser)

    def _store_main_cli_argument(self, fargs, fkwargs):
        if fargs:
            self._id = fargs[0].lower()
        elif fkwargs and "id" in fkwargs.keys():
            self._id = fkwargs['id']
        else:
            self._id = ""

    def _is_module_started_from_command_line(self):
        return self._id == "cli"

    @staticmethod
    def _define_main_command_line_interface():
        # define information
        parser = argparse.ArgumentParser(
            description='Freeplane Packer',
            usage='''reqmgt <command> [<args>]
            Possible commands are:
            pack    create Freeplane container file
            unpack  [ not implemented, yet ]
            ''')
        # define command argument
        parser.add_argument('command', help='Subcommand to run')
        return parser

    def _read_out_cli_and_execute_main_command(self, parser):
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = self._get_main_arguments_from_user(parser)
        self._validate_command_is_provided_in_script(args, parser)
        self._use_dispatch_pattern_to_invoke_method_with_same_name(args)

    @staticmethod
    def _get_main_arguments_from_user(parser):
        return parser.parse_args(sys.argv[1:2])

    def _validate_command_is_provided_in_script(self, args, parser):
        if not hasattr(self, args.command):
            logging.error('Unrecognized command. EXITING.')
            parser.print_help()
            sys.exit(1)

    def _use_dispatch_pattern_to_invoke_method_with_same_name(self, args):
        getattr(self, args.command)()

    def pack(self, mmpath="", mmxpath="", log_level='info',):
        self._create_attributes_from_cli_or_api_arguments(log_level, mmpath, mmxpath)
        self._adjust_logging_level_to_users_wishes()
        mindmap = self._connect_to_mindmap_as_information_source()
        self._expand_user_arguments()
        dicHyperlinks, lstFpnodes = self._collect_linked_file_paths(mindmap)
        self._collect_inline_image_paths(dicHyperlinks, lstFpnodes)
        self._collect_html_image_sources(dicHyperlinks, lstFpnodes)
        _containerfolder, _filesfolder = self._build_container()
        self._set_mindmaps_path_as_current_path()
        lstAbsPaths = []
        for _path, _infolist in dicHyperlinks.items():
            _path = self._localize_original_file(_path)
            if self._is_source_file_existing(_path):
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
                _basename = self._paste_file_into_container_folder(_count, _filesfolder, _path, lstAbsPaths)
                self._walk_through_infolist(_basename, _infolist, mindmap)
        self._save_modified_mindmap_file_into_container_folder(_containerfolder, mindmap)
        self._build_zip_container(_containerfolder)

    def _create_attributes_from_cli_or_api_arguments(self, log_level, mmpath, mmxpath):
        if self._is_module_started_from_command_line():
            self._read_from_command_line()
        # module was called from function
        else:
            self._write_into_object(log_level, mmpath, mmxpath)

    def _read_from_command_line(self):
        parser = argparse.ArgumentParser(description='pack mindmap contents into container file')
        args = parse_opt_args(parser)
        self._write_into_object(args.log_level, args.mmpath, args.mmxpath)

    def _write_into_object(self, log_level, mmpath, mmxpath):
        self._mmpath = mmpath
        self._mmxpath = mmxpath
        self._log_level = log_level

    def _adjust_logging_level_to_users_wishes(self):
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

    def _connect_to_mindmap_as_information_source(self):
        # here, the desired mindmap will be loaded for being parsed
        # open mindmap
        mindmap = freeplane.Mindmap(self._mmpath)
        logging.debug(f'mindmap "{self._mmpath}" will be exported into a container')
        return mindmap

    def _expand_user_arguments(self):
        # in case, the user didn't provide all the specific input arguments,
        # now some default values are expanded in order to prevent the user
        # from the obligation to provide all of them using the command line
        # or graphical user interface.
        if not self._mmxpath:
            # set to be corresponding as mindmap
            self._mmxpath = self._mmpath + "x"

    def _collect_linked_file_paths(self, mindmap):
        # walk through entire mindmap and find links to files within the local
        # file system. web links will be prevailed. it would be possible to
        # convert web content e.g. to PDF and place it within the container.
        lstFpnodes = mindmap.find_nodes()
        dicHyperlinks = {}
        # take each freeplane node within the mindmap
        for fpnode in lstFpnodes:
            _path = self._get_sanitize_path_string_if_link_is_present_in_node(fpnode)
            if _path:
                _path = self._sanitize_file_link(_path)
                #
                # disregard_all_other_link_types
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
                _path = self._remove_possible_appended_freeplane_specifics(_path)
                self._initialize_details_list_if_not_already_done(_path, dicHyperlinks)
                self._store_new_directory_entry(_path, dicHyperlinks, fpnode)
        return dicHyperlinks, lstFpnodes

    @staticmethod
    def _get_sanitize_path_string_if_link_is_present_in_node(fpnode):
        return fpnode.hyperlink.replace("\\", "/")

    @staticmethod
    def _sanitize_file_link(_path):
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
        return _path

    @staticmethod
    def _remove_possible_appended_freeplane_specifics(_path):
        # remove hyperlink to node in external mindmap
        _pos = _path.rfind('#')
        if _pos > -1:
            _path = _path[:_pos]
        return _path

    @staticmethod
    def _store_new_directory_entry(_path, dicHyperlinks, fpnode):
        dicHyperlinks[_path].append({'nodeid': fpnode.id, 'type': "file",})

    def _collect_inline_image_paths(self, dicHyperlinks, lstFpnodes):
        # walk through entire mindmap and find paths to images within the local
        # file system. web links will be prevailed.
        # take each freeplane node within the mindmap
        for fpnode in lstFpnodes:
            _imagepath = self._get_inline_image_path_if_present_in_node(fpnode)
            if _imagepath:
                self._initialize_details_list_if_not_already_done(_imagepath, dicHyperlinks)
                _imagesize = self._get_image_size(fpnode)
                self._store_image_details(_imagepath, _imagesize, dicHyperlinks, fpnode)

    @staticmethod
    def _get_inline_image_path_if_present_in_node(fpnode):
        return fpnode.imagepath

    @staticmethod
    def _initialize_details_list_if_not_already_done(_imagepath, dicHyperlinks):
        if _imagepath not in dicHyperlinks.keys():
            dicHyperlinks[_imagepath] = []

    @staticmethod
    def _get_image_size(fpnode):
        return fpnode.imagesize

    @staticmethod
    def _store_image_details(_imagepath, _imagesize, dicHyperlinks, fpnode):
        # create new dictionary entry
        dicHyperlinks[_imagepath].append({'nodeid': fpnode.id, 'type': "image", 'size': _imagesize,})

    def _collect_html_image_sources(self, dicHyperlinks, lstFpnodes):
        # walk through entire mindmap and find paths to images within the local
        # file system. web links will be prevailed.
        # take each freeplane node within the mindmap
        for fpnode in lstFpnodes:
            lstImageElements = self._collect_all_html_image_nodes_present(fpnode)
            self._insert_paths_into_dictionary(dicHyperlinks, fpnode, lstImageElements)

    @staticmethod
    def _collect_all_html_image_nodes_present(fpnode):
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
        return lstImageElements

    def _insert_paths_into_dictionary(self, dicHyperlinks, fpnode, lstImageElements):
        for _element in lstImageElements:
            _imagepath = _element.get("src")
            # skip http images
            if self._is_http_image(_imagepath):
                logging.debug(f'web-linked images like "{_imagepath}" will not be changed.')
                continue
            self._initialize_details_list_if_not_already_done(_imagepath, dicHyperlinks)
            self._store_html_image_details(_element, _imagepath, dicHyperlinks, fpnode)

    @staticmethod
    def _is_http_image(_imagepath):
        return _imagepath.startswith("http:/") or _imagepath.startswith("https:/")

    @staticmethod
    def _store_html_image_details(_element, _imagepath, dicHyperlinks, fpnode):
        # create new dictionary entry
        dicHyperlinks[_imagepath].append({'nodeid': fpnode.id, 'type': "html_image", 'element': _element,})

    def _build_container(self):
        # create container folder structure
        _containerfolder = self._mmxpath + "_"
        pathlib.Path(_containerfolder).mkdir(parents=True, exist_ok=True)
        _filesfolder = os.path.join(_containerfolder, "files")
        pathlib.Path(_filesfolder).mkdir(parents=True, exist_ok=True)
        return _containerfolder, _filesfolder

    def _set_mindmaps_path_as_current_path(self):
        os.chdir(pathlib.Path(self._mmpath).parent)

    @staticmethod
    def _localize_original_file(_path):
        # convert relative to absolute path. if the path starts with dots
        # or if the path does not start with a drive letter or a slash.
        if re.search(r'^([A-z]{2,})', _path) is not None or _path.startswith('.'):
            _path = os.path.abspath(_path)
        return _path

    @staticmethod
    def _is_source_file_existing(_path):
        source_file_exists = not os.path.isfile(_path)
        return source_file_exists

    def _paste_file_into_container_folder(self, _count, _filesfolder, _path, lstAbsPaths):
        # already existing files within the container will be replaced
        # by the fresh ones
        _basename = os.path.basename(_path)
        _basename = self._adjust_name_if_already_multiple_identical_basenames_transferred(_basename, _count)
        self._paste_file(_basename, _filesfolder, _path)
        self._remember_the_file_path_as_being_pasted_into_folder(_path, lstAbsPaths)
        return _basename

    @staticmethod
    def _adjust_name_if_already_multiple_identical_basenames_transferred(_basename, _count):
        if _count:
            _basename = os.path.splitext(_basename)[0] + '__' + str(_count) + os.path.splitext(_basename)[1]
        return _basename

    @staticmethod
    def _paste_file(_basename, _filesfolder, _path):
        shutil.copyfile(_path, os.path.join(_filesfolder, _basename,))

    @staticmethod
    def _remember_the_file_path_as_being_pasted_into_folder(_path, lstAbsPaths):
        lstAbsPaths.append(_path.lower().replace("\\", "/"))

    def _walk_through_infolist(self, _basename, _infolist, mindmap):
        for _info in _infolist:
            self._evaluate_link_type(_basename, _info, mindmap)

    def _evaluate_link_type(self, _basename, _info, mindmap):
        if _info['type'] == "image":
            self._link_nodes_image_section_with_new_file_location(_basename, _info, mindmap)
        elif _info['type'] == "html_image":
            self._link_nodes_html_image_with_new_file_location(_basename, _info)
        else:
            self._link_node_to_new_file_location(_basename, _info, mindmap)

    @staticmethod
    def _link_nodes_image_section_with_new_file_location(_basename, _info, mindmap):
        # find mindmap node
        _node = mindmap.find_nodes(id=_info['nodeid'])[0]
        # replace image element in mindmap
        _imagesize = _info.get('size')
        _node.set_image(link='./files/' + _basename, size=_imagesize,)

    @staticmethod
    def _link_nodes_html_image_with_new_file_location(_basename, _info):
        # pick specific image node
        _img = _info['element']
        # replace image path in node
        _img.set("src", './files/' + _basename,)

    @staticmethod
    def _link_node_to_new_file_location(_basename, _info, mindmap):
        # find mindmap node
        _node = mindmap.find_nodes(id=_info['nodeid'])[0]
        # replace hyperlink path in mindmap
        _node.hyperlink = 'files/' + _basename

    def _save_modified_mindmap_file_into_container_folder(self, _containerfolder, mindmap):
        mindmap.save(os.path.join(_containerfolder, os.path.basename(self._mmpath),))

    def _build_zip_container(self, _containerfolder):
        shutil.make_archive(self._mmxpath, 'zip', _containerfolder)
        shutil.move(self._mmxpath + ".zip", self._mmxpath)
        shutil.rmtree(_containerfolder)


def parse_opt_args(parser):
    parser.add_argument('mmpath', default='',
                        help='mindmap file path. where to find the mindmap within the local file system.',)
    parser.add_argument('--mmxpath', default='',
                        help='container file path. this file will contain the mindmap and further files.',)
    parser.add_argument('--log-level', default='info',
                        help='log messages will be displayed only if severity level is matching or above. '
                             'options are "debug", "info", "warning" or "error"',)
    args = parser.parse_args(sys.argv[2:])
    return args


if __name__ == "__main__":
    Packer('cli')
