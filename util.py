#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess
import logging
import logging.config
import xmltodict
from datetime import datetime
from typing import List, Any, Dict, Tuple, Optional, Set
from ordered_set import OrderedSet
from pprint import pprint


logging.config.fileConfig("logging.conf")
logger = logging.getLogger()


def make_path(path: str) -> None:
    try:
        os.makedirs(path)
    except FileExistsError:
        # ignore
        pass


def exec_cmd(cmd: str, input_data=None) -> Tuple[Optional[str], str]:
    try:
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if input_data:
            result, error = p.communicate(input_data.encode("utf-8"))
        else:
            result, error = p.communicate()
        if p.returncode != 0:
            raise subprocess.CalledProcessError(returncode=p.returncode, cmd=cmd, output=result, stderr=error)
        if error:
            if not error.startswith(
                    b"_RegisterApplication(), FAILED TO establish the default connection to the WindowServer"):
                return None, error.decode("utf-8")
    except subprocess.CalledProcessError:
        return None, "Error with non-zero exit status in command '{}'".format(cmd)
    except subprocess.SubprocessError:
        return None, "Error in execution of command '{}'".format(cmd)
    return result.decode(encoding="utf-8"), ""


def determine_crawler_options(options: Dict[str, Any]) -> str:
    logger.debug("# determine_crawler_options()")

    option_str: str = ""
    if "render_js" in options and options["render_js"]:
        option_str += " --render-js"
    if "user_agent" in options and options["user_agent"]:
        option_str += " --ua '%s'" % options["user_agent"]
    if "referer" in options and options["referer"]:
        option_str += " --referer '%s'" % options["referer"]
    if "encoding" in options and options["encoding"]:
        option_str += " --encoding '%s'" % options["encoding"]
    if "sleep_time" in options and options["sleep_time"]:
        option_str += " --sleep %s" % options["sleep_time"]
    if "header_list" in options and options["header_list"]:
        for header in options["header_list"]:
            option_str += " --header '%s'" % header

    '''
    logger.debug("title=%s, review_point=%d, review_point_threshold=%f" % (title, review_point, review_point_threshold))
    if review_point and review_point_threshold and review_point > review_point_threshold:
        # 일반적으로 평점이 사용되지 않는 경우나
        # 평점이 기준치를 초과하는 경우에만 추출
        warn("ignore an article due to the low score")
        return 0
    '''

    return option_str


def remove_duplicates(a_list: List[Any]) -> List[Any]:
    seen: Set[Any] = OrderedSet()
    result: List[Any] = []
    for item in a_list:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def remove_file(file_path: str) -> None:
    if os.path.isfile(file_path):
        os.remove(file_path)


def get_current_time() -> datetime:
    return datetime.now().astimezone()


def get_time_str(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def get_current_time_str() -> str:
    return get_time_str(get_current_time())


def get_rss_date_str() -> str:
    dt = get_current_time()
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def get_short_date_str(dt=get_current_time()) -> str:
    return dt.strftime("%Y%m%d")
    

class HTMLExtractor:
    @staticmethod
    def get_first_token_from_path(path_str: str) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[str], bool]:
        # print "get_first_token_from_path(path_str='%s')" % path_str
        is_anywhere: bool = False
        if path_str[0:2] == "//":
            is_anywhere = True
        tokens: List[str] = path_str.split("/")
        i: int = 0
        valid_token: str = ""
        for token in tokens:
            valid_token = token
            # print "tokens[%d]='%s'" % (i, token)
            i += 1
            if token in ("", "html", "body"):
                continue
            else:
                # 첫번째 유효한 토큰만 꺼내옴
                break

        # 해당 토큰에 대해 정규식 매칭 시도
        pattern = re.compile(r"""
        (
          (?P<name>\w+)
          (?:
          \[
            (?P<idx>\d+)
          \]
          |
          (?P<is_function>\(\))
          )?
        |
          \*\[@id=\"(?P<id>\w+)\"\]
        )
        """, re.VERBOSE)
        m = pattern.match(valid_token)
        if m:
            name = m.group("name")
            idx = int(m.group("idx")) if m.group("idx") else None
            is_function = True if m.group("is_function") else False
            id_str = m.group("id")
        else:
            return None, None, None, None, False

        # id, name, idx, path의 나머지 부분, is_anywhere을 반환
        return id_str, name, idx, is_function, "/".join(tokens[i:]), is_anywhere

    @staticmethod
    def print_element(num, element):
        print("%d" % num, end="")
        if hasattr(element, "name"):
            print(" %s" % element.name, end="")
        if "id" in element:
            print(" id=''" % element["id"], end="")
        if "class" in element:
            print(" id=''" % element["class"], end="")
        print()

    @staticmethod
    def get_node_with_path(node, path_str: str) -> Optional[List[Any]]:
        if not node:
            return None
        print("\n# get_node_with_path(node='%s', path_str='%s')" % (node.name, path_str))
        node_list = []

        (node_id, name, idx, is_function, next_path_str, is_anywhere) = HTMLExtractor.get_first_token_from_path(path_str)
        print("node_id='%s', name='%s', idx=%d, is_function=%r, next_path_str='%s', is_anywhere=%s" % (node_id, name, idx if idx else -1, is_function, next_path_str, is_anywhere))

        if node_id:
            print("searching with id")
            # 특정 id로 노드를 찾아서 현재 노드에 대입
            nodes = node.find_all(attrs={"id": node_id})
            #print("nodes=", nodes)
            if not nodes or nodes == []:
                print("error, no id matched")
                return None
            if len(nodes) > 1:
                print("error, two or more id matched")
                return None
            print("found! node=%s" % nodes[0].name)
            node_list.append(nodes[0])
            result_node_list = HTMLExtractor.get_node_with_path(nodes[0], next_path_str)
            if result_node_list:
                node_list = result_node_list
        else:
            print("searching with name and index")
            if not name:
                return None

            # 기본 함수
            if is_function and name == "text":
                print("function")
                node_list.append(node.text)
            else:
                print("#children=%d" % len(node.contents))
                i = 1
                for child in node.contents:
                    HTMLExtractor.print_element(i, child)
                    if hasattr(child, 'name'):
                        if child.name == None:
                            continue
                        # 이름이 일치하거나 //로 시작한 경우
                        elif child.name == name:
                            print("name matched! i=%d child.name='%s', type(child)=%s <--> name='%s', idx=%d" % (i, child.name, type(child), name, idx if idx else -1))
                            if not idx or i == idx:
                                # 인덱스가 지정되지 않았거나, 지정되었고 인덱스가 일치할 때
                                if next_path_str == "":
                                    # 단말 노드이면 현재 일치한 노드를 반환
                                    print("*** append! child='%s'" % child.name)
                                    #logging.debug(child)
                                    node_list.append(child)
                                else:
                                    # 중간 노드이면 recursion
                                    print("*** recursion ***")
                                    result_node_list = HTMLExtractor.get_node_with_path(child, next_path_str)
                                    print("\n*** extend! #result_node_list=", len(result_node_list))
                                    if result_node_list:
                                        #logging.debug(result_node_list)
                                        node_list.extend(result_node_list)
                            if idx and i == idx:
                                break
                            # 이름이 일치했을 때만 i를 증가시킴
                            i = i + 1
                        if is_anywhere:
                            print("can be anywhere")
                            result_node_list = HTMLExtractor.get_node_with_path(child, name)
                            if result_node_list:
                                node_list.extend(result_node_list)
                            #print("node_list=", node_list)

        return node_list


class IO:
    @staticmethod
    def read_stdin() -> str:
        line_list = IO.read_stdin_as_line_list()
        return "".join(line_list)

    @staticmethod
    def read_stdin_as_line_list() -> List[str]:
        import io
        input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="ignore")
        line_list = []
        for line in input_stream:
            line_list.append(line)
        return line_list

    @staticmethod
    def read_file(file=None) -> str:
        if not file or file == "":
            return IO.read_stdin()

        line_list = IO.read_file_as_line_list(file)
        return "".join(line_list)

    @staticmethod
    def read_file_as_line_list(file) -> List[str]:
        import codecs

        with codecs.open(file, 'rb', encoding="utf-8", errors="ignore") as f:
            line_list = f.readlines()
            f.close()
        return line_list


class Config:
    config: Dict[str, Dict[str, Any]] = {}

    def __init__(self) -> None:
        if "FEED_MAKER_CONF_FILE" in os.environ and os.environ["FEED_MAKER_CONF_FILE"]:
            config_file = os.environ["FEED_MAKER_CONF_FILE"]
        else:
            config_file = "conf.xml"
        with open(config_file, "r") as f:
            parsed_data = xmltodict.parse(f.read())
            if not parsed_data or "configuration" not in parsed_data:
                logger.error("can't get configuration from config file")
                sys.exit(-1)
            else:
                self.config = parsed_data["configuration"]

    def _get_bool_config_value(self, config_node: Dict[str, Any], key: str, default: bool = False) -> bool:
        if key in config_node:
            if "true" == config_node[key]:
                return True
        return default

    def _get_str_config_value(self, config_node: Dict[str, Any], key: str, default: str = None) -> Optional[str]:
        if key in config_node:
            return config_node[key]
        return default

    def _traverse_config_node(self, config_node: Dict[str, Any], key: str) -> List[str]:
        result: List[str] = []
        if key in config_node:
            if isinstance(config_node[key], list):
                result.extend(config_node[key])
            else:
                result.append(config_node[key])
            return result

        for k, v in config_node.items():
            if isinstance(v, Dict):
                data = self._traverse_config_node(v, key)
                result.extend(data)
        return result
    
    def _get_config_value_list(self, config_node: Dict[str, Any], key: str, default: List[Any] = None) -> Optional[List[Any]]:
        result = self._traverse_config_node(config_node, key)
        if result:
            return result
        return default

    def get_collection_configs(self) -> Dict[str, Any]:
        logger.debug("# get_collection_configs()")
        conf: Dict[str, Any] = {}
        if "collection" in self.config:
            collection_conf = self.config["collection"]

            url_prefix = self._get_str_config_value(collection_conf, "url_prefix")
            user_agent = self._get_str_config_value(collection_conf, "user_agent")
            encoding = self._get_str_config_value(collection_conf, "encoding", "utf-8")

            list_url_list = self._get_config_value_list(collection_conf, "list_url", [])
            element_list = self._get_config_value_list(collection_conf, "element_list", [])
            element_id_list = self._get_config_value_list(collection_conf, "element_id", [])
            element_class_list = self._get_config_value_list(collection_conf, "element_class", [])
            element_path_list = self._get_config_value_list(collection_conf, "element_path", [])
            conf = {
                "url_prefix": url_prefix,
                "user_agent": user_agent,
                "encoding": encoding,
                "list_url_list": list_url_list,
                "element_list": element_list,
                "element_id_list": element_id_list,
                "element_class_list": element_class_list,
                "element_path_list": element_path_list,
            }
        return conf

class URL:
    # http://naver.com/api/items?page_no=3 => http
    @staticmethod
    def get_url_scheme(url: str) -> str:
        scheme_separator = "://"
        separator_index = url.find(scheme_separator)
        if separator_index >= 0:
            return url[:separator_index]
        return ""

    # http://naver.com/api/items?page_no=3 => naver.com
    @staticmethod
    def get_url_domain(url: str) -> str:
        scheme_separator = "://"
        host_index = url.find(scheme_separator) + len(scheme_separator)
        if host_index >= 0:
            first_slash_index = url[host_index:].find('/', host_index)
            if first_slash_index >= 0:
                return url[host_index:(host_index+first_slash_index)]
        return ""

    # http://naver.com/api/items?page_no=3 => /api/items?page_no=3
    @staticmethod
    def get_url_path(url: str) -> str:
        scheme_separator = "://"
        host_index = url.find(scheme_separator) + len(scheme_separator)
        if host_index >= 0:
            first_slash_index = url[host_index:].find('/', host_index)
            if first_slash_index >= 0:
                return url[(host_index+first_slash_index):]
        return ""

    # http://naver.com/api/items?page_no=3 => http://naver.com/api/
    @staticmethod
    def get_url_prefix(url: str) -> str:
        scheme_separator = "://"
        host_index = url.find(scheme_separator) + len(scheme_separator)
        if host_index >= 0:
            last_slash_index = url.rfind('/', host_index)
            if last_slash_index >= 0:
                return url[:(last_slash_index + 1)]
        return ""

    # http://naver.com/api/items?page_no=3 => http://naver.com/api/items
    @staticmethod
    def get_url_except_query(url: str) -> str:
        query_index = url.find('?')
        if query_index >= 0:
            return url[:query_index]
        return url

    # http://naver.com/api + /data => http://naver.com/data
    # http://naver.com/api + data => http://naver.com/api/data
    # http://naver.com/api/view.nhn?page_no=3 + # => http://naver.com/api/view.nhn?page_no=3
    @staticmethod
    def concatenate_url(full_url: str, url2: str) -> str:
        if url2 == "#":
            return full_url
        if len(url2) > 0 and url2[0] == '/':
            url1 = URL.get_url_scheme(full_url) + "://" + URL.get_url_domain(full_url)
        else:
            url1 = URL.get_url_except_query(full_url)

        if len(url1) > 0 and len(url2) > 0:
            if url1[-1] == '/' and url2[0] == '/':
                return url1 + url2[1:]
            if url1[-1] != '/' and url2[0] != '/':
                return url1 + '/' + url2
        return url1 + url2

    @staticmethod
    def get_short_md5_name(content: str) -> str:
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()[:7]


