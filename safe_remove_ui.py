#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @version:    1.0
# @license:    Apache Licence 
# @Filename:   safe_remove_ui.py
# @Author:     chaidisheng
# @contact:    chaidisheng@stumail.ysu.edu.cn
# @site:       https://github.com/chaidisheng
# @software:   PyCharm
# @Time:       2022/2/11 21:55
# @torch: tensor.method(in-place) or torch.method(tensor)
r""" docs """

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import re
import os
import sys
import json
import copy
import time
import pathlib
import logging
import argparse
import datetime

from safe_remove import SafeRemove
from safe_remove_common import SafeRemoveCommon

LOG_LEVEL = logging.INFO
# LOG_FILE = "/home/hikos/system/log/hikos_safe_remove.log"
LOG_FILE = " /var/log/safe_remove/hikos_safe_remove.log"

# 实例化共享类，进行调用
safe_remove_common = SafeRemoveCommon()
# 初始化日志格式、日志路径、等级
safe_remove_common.init_log_formate(LOG_LEVEL, LOG_FILE)


class SafeRemoveUI(SafeRemove):
    def __init__(self):
        super(SafeRemoveUI, self).__init__()
        # 提供给用户的配置文件
        # safe_remove.cfg： 配置文件添加说明
        # safe_remove.d: 不同产品所选取的配置文件
        # 默认创建配置文件(暂时不考虑)
        self.default_protect_path = []
        self.is_remove_path = [1] * (len(self.default_protect_path))
        self.cmd_log = "/usr/bin/cli_log -a set -c LOG_SET_OPERATION_LOG -i {} -e {} >/dev/null 2>&1"

    def write_config_file(self, mode, path_list, is_remove_list):
        """
        将（保护路径：是否默认删除标志位）写入配置文件
        :param mode: 写入模式
        :param path_list: 路径
        :return:
        """
        logging.info('step into method: {}'.format(self.get_method_name()))
        try:
            with open(self.usr_config_file, mode) as f:
                [f.write("{}:{}\n".format(path, flag)) for path, flag in zip(path_list, is_remove_list)]
        except Exception as e:
            logging.error("analyze file list {} fail for {}".format(path_list, str(e)))

    def remove_config_file(self, path):
        """
        移除文件中（保护路径：是否默认删除标志位）的内容
        :param path: 移除的路径
        :return: None
        """
        logging.info('step into method: {}'.format(self.get_method_name()))
        with open(self.usr_config_file, 'r') as f:
            lines = f.readlines()
        with open(self.usr_config_file, 'w') as f:
            for line in lines:
                # if path not in line:
                if path != line.split(':')[0]:
                    f.write(line)

    def is_mount_points(self, path):
        """
        判断是否为挂载点
        :param path: 路径
        :return: 挂载路径
        """
        logging.info('step into method: {}'.format(self.get_method_name()))
        path = os.path.abspath(path)
        while path != os.path.sep:
            if os.path.ismount(path):
                return path
            path = os.path.abspath(os.path.join(path, os.pardir))
        return path

    def timestamp_to_time(self, timestamp):
        """
        把时间戳转化为时间: 1479264792 to 2016-11-16 10:53:12
        :param timestamp: 时间戳
        :return: 标准时间
        """
        logging.info('step into method: {}'.format(self.get_method_name()))
        timeStruct = time.localtime(timestamp)
        return time.strftime('%Y-%m-%d %H:%M:%S', timeStruct)

    def get_path_create_time(self, filePath):
        """
        获取文件的创建时间
        :param filePath: 路径
        :return: 创建时间
        """
        logging.info('step into method: {}'.format(self.get_method_name()))
        t = os.path.getctime(filePath)
        return self.timestamp_to_time(t)

    def get_path_size(self, path):
        """
        获取指定路径的文件夹大小
        :param path: 路径
        :return: 容量（MB）
        """
        logging.info('step into method: {}'.format(self.get_method_name()))
        total_size = 0
        if not os.path.exists(path):
            return total_size
        if os.path.isfile(path):
            return round(os.path.getsize(path) / float(1024 * 1024), 2)
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                total_size += sum([os.path.getsize(os.path.join(root, name))
                                   for name in files])
                return round(total_size / float(1024 * 1024), 2)

    def get_path_usage_size(self, path):
        """
        获取指定路径占用空间大小
        :param path: 指定路径
        :return: 容量（Bytes）
        """
        logging.info('step into method: {}'.format(self.get_method_name()))
        if not os.path.exists(path):
            return None
        elif os.path.isfile(path):
            return int(os.path.getsize(path))
        else:
            response = os.popen('du -sh {} 2>/dev/null'.format(path))
            str_size = response.read().split()[0]
            response.close()
            f_size = float(re.findall(r'[.\d]+', str_size)[0])
            size_unit = re.findall(r'[A-Z]', str_size)
            size_unit = size_unit[0] if size_unit else ""
            if size_unit == 'M':
                f_size = int(f_size * 1024 ** 2)
            if size_unit == 'G':
                f_size = int(f_size * 1024 ** 3)
            if size_unit == 'T':
                f_size = int(f_size * 1024 ** 4)
            return int(f_size)

    def get_mount_points(self):
        """
        获取系统所有的挂载点及其对应的文件系统
        :return: 挂载点，文件系统
        """
        logging.info('step into method: {}'.format(self.get_method_name()))
        cmd = "mount -v"
        ret_code, ret_str = safe_remove_common.fun_exec_command(cmd)
        if 0 != ret_code:
            logging.error("get mount points fail for {}".format(ret_str))
        lines = ret_str.decode('utf-8').split('\n')
        points = map(lambda line: line.split()[2], [line for line in lines if line])
        filesystem = map(lambda line: line.split()[0], [line for line in lines if line])
        return points, filesystem

    def get_mount_paths(self, mount_path):
        """
        获取挂载点mount_point所有的关联路径
        :param mount_point: 挂载点路径
        :return: 关联挂载点列表
        """
        mount_paths, file_paths = map(lambda path: list(path), self.get_mount_points())
        mount_points = dict(zip(mount_paths, file_paths))
        file_system = mount_points[mount_path]
        return [key for key, value in mount_points.items() if value == file_system and key != mount_path]+ \
               [mount_points[mount_path]]

    def safe_get(self, args):
        """
        获取保护路径的属性与类型
        :param args: 暂时不需要
        :return: Json数据
        """
        logging.info('step into method: {}'.format(self.get_method_name()))
        # 返回Json数据 定义私有变量
        __data = {
            "path": "",
            "flag": "",
            "style": ""
        }
        result_output = {
            "code": 0,
            "msg": "",
            "data": {}
        }
        # 获取配置文件中保护路径的详情
        if os.path.exists(self.usr_config_file):
            protect_path, is_remove_flag = self.read_config_file(self.usr_config_file)
            protect_path = [path for path in protect_path if "" != path]
            is_remove_flag = [flag for flag in is_remove_flag if "" != flag]
            protect_dict = dict(zip(protect_path, is_remove_flag))
            protect_list = sorted(protect_dict.items(), key=lambda k: len(k[0]))
            if 0 != len(protect_list):
                result_output["code"] = 0
                result_output["msg"] = "success"
                for path, flag in protect_list:
                    __data["path"] = path
                    __data["flag"] = flag
                    if os.path.ismount(path):
                        __data["style"] = u"挂载点"
                    elif os.path.islink(path):
                        __data["style"] = u"软链接"
                    elif os.path.isdir(path):
                        __data["style"] = u"普通目录"
                    elif os.path.isfile(path):
                        __data["style"] = u"普通文件"
                    elif "*" in path:
                        __data["style"] = u"通配符路径"
                    else:
                        logging.error(u"不存在此路径")
                    for key, value in __data.items():
                        print("{}:{}".format(key, value))
                    print("\n", end="")
                    result_output["data"] = {u"正常获取保护路径信息"}
            else:
                result_output["code"] = 1
                result_output["msg"] = "fail"
                result_output["data"] = {u"配置文件为空!"}
        else:
            result_output["code"] = 1
            result_output["msg"] = "fail"
            result_output["data"] = {u"不存在此配置文件路径!"}
        # print(json.dumps({"list":result_output["data"]}, indent=4))
        return result_output["code"]

    def safe_get_all(self, args):
        """
        获取保护路径详情
        :param args: 对应路径
        :return: 路径详情（创建时间，占用空间，原路径， 链接关联路径，挂载关联路径）
        """
        logging.info('step into method: {}'.format(self.get_method_name()))
        # 返回Json数据
        __data = {
            "create_time": "",
            "path_size": "",
            "real_path": "",
            "link_path": "",
            "mounts_path": ""
        }
        result_output = {
            "code": 0,
            "msg": "",
            "data": {}
        }
        if not args.path:
            result_output["code"] = 1
            result_output["msg"] = "fail"
            result_output["data"] = u"输入路径为空"
        else:
            for path in args.path:
                path = os.path.abspath(path)
                __data["real_path"] = path
                __data["create_time"] = self.get_path_create_time(path)
                # __data["path_size"] = self.get_path_size(path)
                __data["path_size"] = self.get_path_usage_size(path)
                if os.path.ismount(path):
                    # __data["mounts_path"] = mount_points[os.path.abspath(path)]
                    for str_path in self.get_mount_paths(os.path.abspath(path)):
                        __data["mounts_path"] += str_path
                        __data["mounts_path"] += ";"
                elif os.path.islink(path):
                    __data["link_path"] = str(pathlib.Path(path).resolve())
                else:
                    __data["link_path"] = ""
                    __data["mounts_path"] = ""
                for key, value in __data.items():
                    print("{}:{}".format(key, value))
            else:
                result_output["code"] = 0
                result_output["msg"] = "success"
                result_output["data"] = u"正常获取保护路径详情"
        # print(json.dumps({"list": result_output["data"]}, indent=4))
        return result_output["code"]

    def safe_add(self, args):
        """
        用户添加保护路径至配置文件中
        :param args:
        :return:Json数据
        """
        logging.info('step into method: {}'.format(self.get_method_name()))
        result_output = {
            "code": 0,
            "msg": "",
            "data": {}
        }
        try:
            # 判断输入路径是否为空
            if not args.path:
                result_output["code"] = 1
                result_output["msg"] = "fail"
                result_output["data"] = u"输入路径为空"
            else:
                add_path, add_flag = [], []
                protect_path, is_remove_flag = self.read_config_file(self.usr_config_file)
                for path in args.path:
                    if '*' in path:
                        add_path.append(path)
                        add_flag.append(0)
                    elif os.path.abspath(path) in protect_path:
                        # 判断保护是否已存在于配置文件
                        result_output["code"] = 1
                        result_output["msg"] = "fail"
                        result_output["data"] = u"{}路径已存在".format(path)
                        ret_code, ret_str = safe_remove_common.fun_exec_command(
                            self.cmd_log.format("0x01080035", path))
                        if 0 != ret_code:
                            logging.error("Record added protect path log fail for {}".format(ret_str))
                        break
                    else:
                        path = os.path.abspath(path)
                        if os.path.exists(path):
                            add_path.append(path)
                            add_flag.append(0)
                            result_output["code"] = 0
                            result_output["msg"] = "success"
                            result_output["data"] = ""
                            ret_code, ret_str = safe_remove_common.fun_exec_command(
                                self.cmd_log.format("0x01080034", path))
                            if 0 != ret_code:
                                logging.error("Record added protect path log fail for {}".format(ret_str))
                        else:
                            result_output["code"] = 1
                            result_output["msg"] = "fail"
                            result_output["data"] = u"{}路径不存在".format(path)
                            ret_code, ret_str = safe_remove_common.fun_exec_command(
                                self.cmd_log.format("0x01080035", path))
                            if 0 != ret_code:
                                logging.error("Record added protect path log fail for {}".format(ret_str))
                else:
                    self.write_config_file('a', add_path, add_flag)
        except Exception as e:
            logging.error("Add protected paths to config file fail for {}".format(str(e)))
            result_output["code"] = 1
            result_output["msg"] = "fail"
            result_output["data"] = str(e)
        return result_output["code"]

    def safe_remove(self, args):
        """
        从配置文件中移除不再需要保护的路径
        :param args: 待移除路径列表
        :return:Json数据
        """
        logging.info('step into method: {}'.format(self.get_method_name()))
        result_output = {
            "code": 0,
            "msg": "",
            "data": {}
        }
        try:
            # 判断输入路径是否为空
            if not args.path:
                result_output["code"] = 1
                result_output["msg"] = "fail"
                result_output["data"] = u"输入路径为空"
            else:
                [self.remove_config_file(path) for path in args.path]
                result_output["code"] = 0
                result_output["msg"] = "success"
                result_output["data"] = ""
                ret_list = [safe_remove_common.fun_exec_command(
                    self.cmd_log.format("0x01080036", path)) for path in args.path]
                ret_code_list = [ret_value[0] for ret_value in ret_list]
                if any(ret_code_list):
                    logging.error("Record remove protect path log fail.")
        except Exception as e:
            logging.error("Remove protected paths to config file fail for {}".format(str(e)))
            result_output["code"] = 1
            result_output["msg"] = "fail"
            result_output["data"] = str(e)
            ret_code, ret_str = safe_remove_common.fun_exec_command(self.cmd_log.format("0x01080037", str(e)))
            if 0 != ret_code:
                logging.error("Record remove protect path log fail for {}".format(ret_str))
        return result_output["code"]


def main(args):
    # 实例化SafeRemove类
    safe_rm_ui = SafeRemoveUI()
    safe_rm_api = dict(get=safe_rm_ui.safe_get, get_all=safe_rm_ui.safe_get_all,
                       add=safe_rm_ui.safe_add, remove=safe_rm_ui.safe_remove)
    try:
        # 选择不同的接口操作，包括safe_get、safe_get_all、safe_add、safe_remove
        return safe_rm_api[args.action](args)
    except KeyError as e:
        logging.error("analysis args fail for {}".format(str(e)))
        return 1
    except Exception as e:
        logging.error("execute function fail for {}".format(str(e)))
        return 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="python safe_remove_ui.py", description="safe remove ui")
    # 用户操作: 包括查询get、添加add、移除remove
    parser.add_argument("-a", "--action", type=str, default="",
                        help="action{get|get_all|add|remove}, Get which action to execute")
    # 接收保护路径列表
    parser.add_argument("-p", "--path", type=str, default="", nargs="*", help="delete path list [path...]")
    opt = parser.parse_args()
    sys.exit(main(opt))
