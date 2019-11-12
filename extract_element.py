#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import signal
import logging
import logging.config
from bs4 import BeautifulSoup
from util import Config, IO, HTMLExtractor
from pprint import pprint


logging.config.fileConfig("logging.conf")
logger = logging.getLogger()
signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def extract_element(html: str) -> int:
    logger.debug("# extract_element()")

    result_content: str = ""

    # configuration
    config = Config()
    if not config:
        logger.error("can't read configuration")
        sys.exit(-1)

    collection_conf = config.get_collection_configs()
    if not collection_conf:
        logger.error("can't get collection configuration")
        sys.exit(-1)

    #id_list = collection_conf["element_id_list"]
    #class_list = collection_conf["element_class_list"]
    #path_list = collection_conf["element_path_list"]
    element_list = collection_conf["element_list"][0]
    encoding = collection_conf["encoding"]
    logger.debug("# encoding: %r" % encoding)

    # sanitize
    html = re.sub(r'alt="(.*)<br>(.*)"', r'alt="\1 \2"', html)
    html = re.sub(r'<br>', r'<br/>', html)
    html = re.sub(r'[\x01\x08]', '', html, re.LOCALE)
    html = re.sub(r'<\?xml[^>]+>', r'', html)

    for parser in ["html.parser"]:
        soup = BeautifulSoup(html, parser)
        if not soup:
            logger.error("can't parse HTML")
            sys.exit(-1)

        for element_spec in element_list:
            if element_spec == "element_path":
                path_str = element_list[element_spec]
                divs = HTMLExtractor.get_node_with_path(soup, path_str)
            elif element_spec == "element_class":
                class_str = element_list[element_spec]
                divs = soup.find_all(class_=class_str)
            elif element_spec == "element_id":
                id_str = element_list[element_spec]
                divs = soup.find_all(attrs={"id": id_str})
            else:
                raise RuntimeError("unknown configuration '%s'" % element_spec)

            if divs:
                for div in divs:
                    #logger.debug("div=%s" % str(div))
                    result_content = result_content + str(div)

    return result_content
