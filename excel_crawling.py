#!/usr/bin/env python

import sys
import re
import signal
import logging
from typing import Dict, Optional, Union, Any

import xlrd
import xlwt

from extract_element import extract_element
from util import Config, IO, HTMLExtractor
from crawler import Crawler, Method


logging.config.fileConfig("logging.conf")
logger = logging.getLogger()
signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def convert_isbn(isbn: str) -> str:
    isbn = isbn.strip()

    # 숫자로 저장된 셀의 값을 정수값 문자열로 변환
    isbn = re.sub(r'\.0$', '', isbn)
    # -제거
    isbn = re.sub(r'-', '', isbn)

    # 13자리 이상의 숫자로 구성된 문자열인지 검사
    m = re.search(r'(?P<isbn>[0-9]{13,})', isbn)
    if not m:
        raise ValueError
    isbn = m.group("isbn")
    return isbn


def read_excel_file(excel_file: str) -> int:
    workbook = xlrd.open_workbook(excel_file)
    worksheet1 = workbook.sheet_by_index(0)
    num_rows = worksheet1.nrows
    isbn: str = ""
    isbn_code: str = ""
    description: str = ""
    method = Method.GET
    headers = {"Accept-Encoding": "gzip, deflate", "User-Agent": "Mozillla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36", "Accept": "*/*", "Connection": "Keep-Alive"}
    timeout = 10
    encoding: Optional[str] = None

    config = Config()
    if not config:
        logger.error("can't read configuration")
        sys.exit(-1)
    collection_conf = config.get_collection_configs()
    url_prefix = collection_conf["url_prefix"]
    encoding = collection_conf["encoding"]
    logger.debug("url_prefix=%s" % url_prefix)

    crawler = Crawler(method, headers, timeout, encoding)

    for row_num in range(num_rows):
        row = worksheet1.row_values(row_num)
        isbn = str(row[0])
        description = str(row[28])

        try:
            isbn_code = convert_isbn(isbn)
        except ValueError as e:
            continue
        logger.debug("isbn=%s" % isbn_code)

        url = url_prefix + isbn_code
        logger.debug("url=%s" % url)

        html = crawler.run(url)
        #logger.debug("html=%s" % html)

        element_content = extract_element(html)
        #logger.debug("element_content=%s" % element_content)



    return 0


def main() -> int:
    return read_excel_file(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())