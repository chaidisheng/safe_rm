#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @version:    1.0
# @license:    Apache Licence 
# @Filename:   safe_remove_test.py
# @Author:     chaidisheng
# @contact:    chaidisheng@stumail.ysu.edu.cn
# @site:       https://github.com/chaidisheng
# @software:   PyCharm
# @Time:       2022/2/11 21:54
# @torch: tensor.method(in-place) or torch.method(tensor)
r""" docs """

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import random
import unittest
import logging

# import HTMLTestRunner
# from unittestreport import TestRunner
sys.path.append("/home/hikos/system/bin/")
from safe_remove import SafeRemove
from safe_remove_ui import SafeRemoveUI
from safe_remove_common import SafeRemoveCommon

safe_remove = SafeRemove()
safe_remove_ui = SafeRemoveUI()
safe_remove_common = SafeRemoveCommon()
record_lines = ["success"]
file_path = "/home/hikos/system/bin/auto_test/safe_remove_auto_test.log"


class Args:
    def __init__(self, path):
        self.path = path
        self.force = ""
        self.recursive = "r"
        self.i = ""
        self.dir = ""


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("full test case begin!\n")

    @classmethod
    def tearDownClass(cls):
        # 记录测试报告
        with open(file_path, "w+") as f:
            [f.write("{}\n".format(content)) for content in record_lines]
        print("successfully full test case end!\n")

    def setUp(self):
        print("this test case begin!")

    def tearDown(self):
        print("successfully this test case end!")

    def auto_create_path(self, nums=0):
        """
        在/home/test下随机创建测试路径
        :return:
        """
        # 给出路径名称列表
        paths = ["test_"+str(i) for i in range(nums)]
        for path in paths:
            cmd = "mkdir -p /home/test/"+path
            ret_code, _ = safe_remove_common.fun_exec_command(cmd)
        return ["/home/test/"+path for path in paths]

    def test_safe_get(self):
        """
        测试保护路径列表获取
        :return:
        """
        self.assertEqual(safe_remove_ui.safe_get(None), 0)
        record_lines.append("success: 获取默认保护路径成功")

    def test_safe_get_all(self):
        """
        测试获取保护路径详情
        :return:
        """
        protect_path = safe_remove_ui.read_config_file(safe_remove_ui.usr_config_file)[0]
        protect_path.remove('/')  # du -sh / 出现错误
        args = Args(protect_path)
        self.assertEqual(safe_remove_ui.safe_get_all(args), 0)
        record_lines.append("success: 获取保护路径详情成功")

    def test_safe_add_remove(self):
        """
        测试创建->移除->添加->移除->删除
        在/home/test/下随机创建路径测试
        :return:
        """
        args = Args(self.auto_create_path(random.randint(1, 10)))
        # print("safe remove protect path {}".format(args.path))
        self.assertEqual(safe_remove_ui.safe_remove(args), 0)
        # print("safe add protect path {}".format(args.path))
        self.assertEqual(safe_remove_ui.safe_add(args), 0)
        # print("safe remove protect path {}".format(args.path))
        self.assertEqual(safe_remove_ui.safe_remove(args), 0)
        # 测试完添加-移除保护路径后需要删除测试路径
        ret_code_del = safe_remove.execute_delete(args)
        self.assertEqual(ret_code_del, 0)
        record_lines.append("success: 创建->移除->添加->移除->删除保护路径成功")

    def test_safe_delete(self):
        """
        测试安全删除功能:创建测试路径->添加测试路径->执行删除测试路径
        测试路径/home/test/，分场景测试：
        (1)普通场景，包括绝对路径与相对路径删除保护路径
        (2)通过进入其他目录删除保护路径
        :return:
        """
        # 场景一(1)(2)
        args = Args(self.auto_create_path(random.randint(1, 10)))
        self.assertEqual(safe_remove_ui.safe_remove(args), 0)
        self.assertEqual(safe_remove_ui.safe_add(args), 0)
        ret_code_del = safe_remove.execute_delete(args)
        self.assertEqual(ret_code_del, 1)
        self.assertEqual(safe_remove_ui.safe_remove(args), 0)
        ret_code_del = safe_remove.execute_delete(args)
        self.assertEqual(ret_code_del, 0)
        # self.countTestCases()
        record_lines.append("success: 通过绝对路径删除保护路径测试成功")

    def test_safe_delete_pre(self):
        """
        (3)通过删除保护路径的前级目录删除保护路径
        :return:
        """
        # 一个场景一个测试用例TestCase
        # 所有删除场景为一个suite
        # 包括保护路径和非保护路径
        paths = self.auto_create_path(random.randint(1, 10))
        args = Args(paths)
        self.assertEqual(safe_remove_ui.safe_remove(args), 0)
        self.assertEqual(safe_remove_ui.safe_add(args), 0)
        # 此处应该遍历所有的前级路径，当前取上一级路径测试
        paths_ = [os.path.abspath(os.path.join(path, os.pardir)) for path in paths]
        args_ = Args(paths_)
        ret_code_del = safe_remove.execute_delete(args_)
        self.assertEqual(ret_code_del, 1)
        self.assertEqual(safe_remove_ui.safe_remove(args), 0)
        ret_code_del = safe_remove.execute_delete(args)
        self.assertEqual(ret_code_del, 0)
        record_lines.append("success: 通过前级路径删除保护路径测试成功")

    def test_safe_delete_link(self):
        """
        (4)通过保护路径的软链接删除保护路径
        进一步实现通过保护路径的软链接删除其内层的其他保护路径
        这种场景会使保护路径失效，现在此版本的情况是可以防止进入
        软链接进行删除，<但是其他非保护路径亦不可以被删除,（有待
        进一步解决）)>
        :return:
        """
        paths = self.auto_create_path(random.randint(1, 10))
        paths_link = [path+"_link" for path in paths]
        [safe_remove_common.fun_exec_command("ln -s {} {}".format(path, path_link))
         for path, path_link in zip(paths, paths_link)]
        args, args_ = Args(paths_link), Args(paths)
        self.assertEqual(safe_remove_ui.safe_remove(args), 0)
        self.assertEqual(safe_remove_ui.safe_add(args), 0)
        ret_code_del = safe_remove.execute_delete(args)
        self.assertEqual(ret_code_del, 1)
        ret_code_del = safe_remove.execute_delete(args_)
        self.assertEqual(ret_code_del, 1)
        self.assertEqual(safe_remove_ui.safe_remove(args), 0)
        self.assertEqual(safe_remove_ui.safe_remove(args_), 0)
        ret_code_del = safe_remove.execute_delete(args)
        self.assertEqual(ret_code_del, 0)
        ret_code_del = safe_remove.execute_delete(args_)
        self.assertEqual(ret_code_del, 0)
        record_lines.append("success: 通过软链接路径删除保护路径测试成功")

    def test_safe_delete_mount(self):
        """TODO 考虑是否测试所有的保护挂载点路径，暂不实现
        (5) 通过保护路径的关联挂载点路径删除保护路径
        这种场景下，会使保护路径通过进入其挂载点关联路径删除其他
        保护路径，暂时这种场景未在此版本实现。
        暂时测试挂载点路径：/dev/mapper/centos_hikvisionos-opt
        :return:
        """
        safe_remove_common.fun_exec_command("mkdir -p /home/test/mount_opt")
        safe_remove_common.fun_exec_command("mount /dev/mapper/centos_hikvisionos-opt /home/test/mount_opt")
        ret_code_del = safe_remove.execute_delete(args=Args(["/opt", "/home/test/mount_opt"]))
        self.assertEqual(ret_code_del, 1)
        safe_remove_common.fun_exec_command("umount /home/test/mount_opt")
        ret_code_del = safe_remove.execute_delete(args=Args(["/home/test/mount_opt"]))
        self.assertEqual(ret_code_del, 0)
        record_lines.append("success: 通过挂载点路径删除保护路径测试成功")


if __name__ == '__main__':
    unittest.main(verbosity=2)
