#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @version:    1.0
# @license:    Apache Licence 
# @Filename:   safe_remove_common.py
# @Author:     chaidisheng
# @contact:    chaidisheng@stumail.ysu.edu.cn
# @site:       https://github.com/chaidisheng
# @software:   PyCharm
# @Time:       2022/2/11 21:51
# @torch: tensor.method(in-place) or torch.method(tensor)
r""" docs """

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import logging
import subprocess

from functools import wraps
from logging.handlers import RotatingFileHandler


class LoggingInfo(object):
    """
    日志信息打印
    """
    __slots__ = ('log_file', 'log_level', 'log_format')

    def __init__(self, log_level=logging.INFO, log_file="/b_iscsi/log/safe_remove.log"):
        self.log_file = log_file
        self.log_level = log_level
        self.log_format = '%(asctime)s %(filename)s (%(funcName)s %(lineno)s) [%(levelname)s] - %(message)s'

    def init_log_format(self):
        """
        设置日志初始化格式
        :return: None
        """
        logging.basicConfig(format=self.log_format, datefmt='%Y-%m-%d %H:%M:%S', level=self.log_level,
                            filename=os.path.join(os.getcwd(), self.log_file))

    def generator_logger(self):
        """
        register loop logger
        :return: logger object
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(level=self.log_level)
        # 定义一个RotatingFileHandler，最多备份3个日志文件，每个日志文件最大1K
        rHandler = RotatingFileHandler(self.log_file, maxBytes=1 * 1024, backupCount=3)
        rHandler.setLevel(level=self.log_level)
        formatter = logging.Formatter(self.log_format)
        rHandler.setFormatter(formatter)
        logger.addHandler(rHandler)
        # lack logger.removeHandler(rHandler)
        return logger

    def __call__(self, func):
        r""" logging decorator
            TODO 预留日志装饰器（函数名称、注释文档、参数列表）
        """
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            logger = logging.getLogger(func.__name__)
            logger.setLevel(self.log_level)
            fh = logging.FileHandler(self.log_file)
            fh.setLevel(self.log_level)
            formatter = logging.Formatter(self.log_format)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            logger.info("step into {0}".format(func.__name__))
            result = func(*args, **kwargs)
            logger.info("step out {0}".format(func.__name__))
            logger.removeHandler(fh)
            return result
        return wrapped_function


class SafeRemoveCommon(object):
    def __init__(self):
        pass

    @staticmethod
    def fun_exec_command(cmd):
        """
        用于执行bash调用的函数
        :param cmd: bash调用的命令
        :return: 成功返回0和标准输出，
        失败返回bash命令的返回值和标准出错
        """
        logging.info('cmd:{}'.format(cmd))
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        process.wait()
        stdout, stderr = process.communicate()
        ret_code = process.returncode
        return ret_code, stdout if 0 == ret_code else stderr

    @staticmethod
    def __fun_exec_command_(cmd):
        """
        TODO
        :param cmd:
        :return:
        """
        with os.popen(cmd, 'r') as fd:
            return fd.readlines()

    @staticmethod
    def __fun_exec_command__(cmd):
        """
        TODO
        :param cmd:
        :return:
        """
        return os.system(cmd)
