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
    new_excel_file = "new_" + excel_file
    isbn: str = ""
    isbn_code: str = ""
    description: str = ""
    method = Method.GET
    headers = {"Accept-Encoding": "gzip, deflate", "User-Agent": "Mozillla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36", "Accept": "*/*", "Connection": "Keep-Alive"}
    timeout = 10
    encoding: Optional[str] = None
    description_col_num = 28

    config = Config()
    if not config:
        logger.error("can't read configuration")
        sys.exit(-1)
    collection_conf = config.get_collection_configs()
    url_prefix = collection_conf["url_prefix"]
    encoding = collection_conf["encoding"]
    logger.debug("url_prefix=%s" % url_prefix)

    workbook = xlrd.open_workbook(excel_file)
    worksheet1 = workbook.sheet_by_index(0)
    num_rows = worksheet1.nrows

    new_workbook = xlwt.Workbook()
    new_worksheet = new_workbook.add_sheet("Sheet1", cell_overwrite_ok=True)

    crawler = Crawler(method, headers, timeout, encoding)

    for row_num in range(num_rows):
        do_crawl = True
        do_extract = False

        row = worksheet1.row_values(row_num)
        isbn = str(row[0])

        try:
            isbn_code = convert_isbn(isbn)
        except ValueError as e:
            do_crawl = False
        logger.debug("isbn=%s" % isbn_code)

        if do_crawl:
            url = url_prefix + isbn_code
            logger.debug("url=%s" % url)

            html = crawler.run(url)
            #logger.debug("html=%s" % html)

            # ISBN -> bid
            state = 0
            for line in html.split('\n'):
                if state == 0:
                    m = re.search(r'<ul class="basic" id="searchBiblioList"', line)
                    if m:
                        state = 1
                elif state == 1:
                    m = re.search(r'<a href="(?P<url>http://book.naver.com/[^"]+)"', line)
                    if m:
                        url = m.group("url")
                        logger.debug(url)
                        html = crawler.run(url)
                        do_extract = True
                        if not html:
                            logger.warning("can't get response from '%s'" % url)
                            sys.exit(-1)
                        break

            if do_extract:
                row[description_col_num] = extract_element(html)
                logger.debug("len=%d" % len(row[description_col_num]))
                #logger.debug("row[description_col_num]=%s" % row[description_col_num])
                with open("test.%d.html" % row_num, "w") as outfile:
                    outfile.write(row[description_col_num])
                    outfile.write("\n")

        for col_num in range(len(row)):
            new_worksheet.write(row_num, col_num, row[col_num])

        # 테스트용으로 첫번째 건 수행 이후에 종료
        #if do_crawl:
            #print(row[description_col_num])
            #break;

    new_workbook.save(new_excel_file)

    return 0


def main() -> int:
    return read_excel_file(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())