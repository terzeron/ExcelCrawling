#!/usr/bin/env python


import sys
import os
import re
from enum import Enum
import time
import getopt
import requests
import logging
import logging.config
from typing import Dict, Optional, Union, Any


logging.config.fileConfig("logging.conf")
logger = logging.getLogger()


class Method(Enum):
    GET = 1
    HEAD = 2
    POST = 3


class Crawler():
    def __init__(self, method, headers, timeout, encoding=None) -> None:
        self.method = method
        self.timeout = timeout
        self.headers = headers
        self.encoding = encoding

    def make_request(self, url) -> Any:
        #print(url, self.method, self.headers)
        if self.method == Method.GET:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
        elif self.method == Method.HEAD:
            response = requests.head(url, headers=self.headers, timeout=self.timeout)
        elif self.method == Method.POST:
            response = requests.post(url, headers=self.headers, timeout=self.timeout)
        if response.status_code == 200:
            if self.encoding:
                response.encoding = self.encoding
            else:
                response.encoding = 'utf-8'
            return response.text
        #print(response.status_code)
        return None
            
    def run(self, url) -> str:
        response = None
        response = self.make_request(url)
        if not response:
            logger.warning("can't get response from '%s'" % url)
            sys.exit(-1)
           
        return response


