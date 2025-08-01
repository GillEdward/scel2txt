#!/usr/bin/env python
#-*- encoding:utf-8 -*-

import argparse
import struct
import sys
import os

class FormatError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class scel:
    def __init__(self):
        self.title = ''
        self.category = ''
        self.description = ''
        self.samples = []
        self.py_map = {}
        self.word_list = []
        self.del_words = []

    def loads(self, bin_data):
        """
            bin_data 是包含 scel 格式的 bytes 类型二进制数据
            返回值： 返回读取到的数据字典
        """

        def read_str(offset, length = -1):
            if length >= 0:
                str_raw = bin_data[offset:offset+length]
            else:
                str_raw = bin_data[
                    offset:bin_data.find(b'\0\0', offset)
                    ]
            if len(str_raw) % 2 == 1:
                str_raw += b'\0'
            return str_raw.decode('utf-16-le')

        def read_uint16(offset):
            return struct.unpack('H', bin_data[offset:offset+2])[0]

        def read_uint32(offset):
            return struct.unpack('I', bin_data[offset:offset+4])[0]

        # 检验头部
        #   0x0 ~ 0x3
        magic = read_uint32(0)
        if magic != 0x1540:
            raise FormatError('头部校验错误，可能不是搜狗词库文件！')

        # scel格式类型，标志着汉字的偏移量
        #   0x4
        scel_type = bin_data[4]
        if scel_type == 0x44:
            hz_offset = 0x2628
        elif scel_type == 0x45:
            hz_offset = 0x26c4
        else:
            raise FormatError('未知的搜狗词库格式，可能为新版格式！')

        #   0x5 ~ 0x11F 目前未知

        # 读取到词组个数
        record_count = read_uint32(0x120)
        total_words = read_uint32(0x124)

        # 两个未知的值
        int_unknow1 = read_uint32(0x128)
        int_unknow2 = read_uint32(0x12C)

        # 读取到标题、目录、描述、样例
        #   0x130 ~ 0x1540
        self.title = read_str(0x130)
        self.category = read_str(0x338)
        self.description = read_str(0x540)
        str_samples = read_str(0xd40)
        #self.samples = list(map(lambda s:s.split('\u3000'), str_samples.split('\r ')))
        #self.samples[-1][1] = self.samples[-1][1].rstrip(' ')
        self.samples = str_samples

        # 读取到拼音列表
        #   0x1540 ~ 0x1540 + ?
        py_count = read_uint32(0x1540)
        offset = 0x1544
        for j in range(py_count):
            py_idx = read_uint16(offset)
            offset += 2
            py_len = read_uint16(offset)
            offset += 2
            py_str = read_str(offset, py_len)
            offset += py_len

            self.py_map[py_idx] = py_str

        # 读取词语列表
        #   hz_offset ~ ?
        offset = hz_offset
        for j in range(record_count):
            word_count = read_uint16(offset)
            offset += 2
            py_idx_count = int(read_uint16(offset) / 2)
            offset += 2

            py_set = []
            for i in range(py_idx_count):
                py_idx = read_uint16(offset)
                offset += 2
                py_set.append(py_idx)

            for i in range(word_count):
                word_len = read_uint16(offset)
                offset += 2
                word_str = read_str(offset, word_len)
                offset += word_len

                info_len = read_uint16(offset)
                offset += 2
                seq = read_uint16(offset)
                flag_unknow = read_uint16(offset+2)
                info_unknow = []
                for i in range(3):
                    info_unknow.append(read_uint16(offset+4+i*2))
                if info_unknow != [0, 0, 0]:
                    print("发现新的扩展信息，请将该词库上报以便调试。", info_unknow)
                offset += info_len

                self.word_list.append([word_str, py_set, seq])

        # 读取的词语按顺序排序
        self.word_list.sort(key = lambda e:e[2])

        # 读取被删除的词语
        if bin_data[offset:offset+12] == 'DELTBL'.encode('utf-16-le'):
            offset += 12
            del_count = read_uint16(offset)
            offset += 2
            for i in range(del_count):
                word_len = read_uint16(offset) * 2
                offset += 2
                word_str = read_str(offset, word_len)
                offset += word_len
                self.del_words.append(word_str)

    def load(self, file_path):
        data = open(file_path, 'rb').read()
        return self.loads(data)

def process_file(path, frequence):
    s = scel()
    s.load(path) # 读取 scel

    # 生成 text
    text = ''
    for w in s.word_list:
        text += w[0] + '\t' + ' '.join(map(lambda key:s.py_map[key], w[1])) + '\t' + str(frequence) + '\n'
    
    # 输出
    fp = open(path.replace(".scel", ".txt"), 'w') # 输出到同名.txt文件
    fp.write(text)

def process_directory(directory_path, frequence):
    """处理目录中的所有.scel文件"""
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith('.scel'):
                file_path = os.path.join(root, file)
                process_file(file_path, frequence)

def main(args):
    path = args.input
    
    if os.path.isfile(path) and path.lower().endswith('.scel'):
        process_file(path, args.frequence)
    elif os.path.isdir(path):
        process_directory(path, args.frequence)
    else:
        print("错误: 请提供有效的.scel文件路径或文件夹路径")
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description = "搜狗细胞词库（.scel）转换工具，" + \
        '输出格式为 "词语\\t拼音\\t优先级"')    # 添加必须参数

    parser.add_argument('input', help = '搜狗细胞词库文件.scel',
        nargs = '?')

    parser.add_argument('frequence', help = '该词库中所有词语的统一词频，默认为 0',
        nargs = '?',
        default = '0')

    args = parser.parse_args()
    exit(main(args))

