# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals

import re
import sys
import time
import threading
from math import ceil

import six
if six.PY2:
    from backports.shutil_get_terminal_size import get_terminal_size
    input = raw_input
else:
    from shutil import get_terminal_size
    from builtins import input

last_output_lines = 0
overflow_flag = False
is_atty = sys.stdout.isatty()

magic_char = "\033[F"

widths = [
    (126,    1), (159,    0), (687,     1), (710,   0), (711,   1),
    (727,    0), (733,    1), (879,     0), (1154,  1), (1161,  0),
    (4347,   1), (4447,   2), (7467,    1), (7521,  0), (8369,  1),
    (8426,   0), (9000,   1), (9002,    2), (11021, 1), (12350, 2),
    (12351,  1), (12438,  2), (12442,   0), (19893, 2), (19967, 1),
    (55203,  2), (63743,  1), (64106,   2), (65039, 1), (65059, 0),
    (65131,  2), (65279,  1), (65376,   2), (65500, 1), (65510, 2),
    (120831, 1), (262141, 2), (1114109, 1),
]

def get_char_width(char):
    global widths
    o = ord(char)
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1


def preprocess(content):
    """
    对输出内容进行预处理，转为str类型 (py3)，并替换行内\r\t\n等字符为空格
    do pre-process to the content, turn it into str (for py3), and replace \r\t\n with space
    """

    if six.PY2:
        if not isinstance(content, unicode):
            if isinstance(content, str):
                _content = unicode(content, encoding=sys.stdin.encoding)
            elif isinstance(content, int):
                _content = unicode(content)
        else:
            _content = content
        assert isinstance(_content, unicode)

    elif six.PY3:
        _content = str(content)

    _content = re.sub(r'\r|\t|\n', ' ', _content)
    return _content


def cut_off_at(content, width):
    if line_width(content) > width:
        now = content[:width]
        while line_width(now) > width:
            now = now[:-1]
        now += "$" * (width - line_width(now))
        return now
    else:
        return content

def print_line(content, columns, force_single_line):

    padding = " " * ((columns - line_width(content)) % columns)
    output = "{content}{padding}".format(content=content, padding=padding)
    if force_single_line:
        output = cut_off_at(output, columns)
    print(output, end='')
    sys.stdout.flush()


def line_width(line):
    """
    计算本行在输出到命令行后所占的宽度
    calculate the width of output in terminal
    """
    if six.PY2:
        assert isinstance(line, unicode)
    result = sum(map(get_char_width, line))
    return result


def lines_of_content(content, width):
    """
    计算内容在特定输出宽度下实际显示的行数
    calculate the actual rows with specific terminal width
    """
    result = 0
    if isinstance(content, list):
        for line in content:
            _line = preprocess(line)
            result += ceil(line_width(_line) / width)
    elif isinstance(content, dict):
        for k, v in content.items():
            # 加2是算上行内冒号和空格的宽度
            # adding 2 for the for the colon and space ": "
            _k, _v = map(preprocess, (k, v))
            result += ceil((line_width(_k) + line_width(_v) + 2) / width)
    return int(result)


def print_multi_line(content, force_single_line):

    global last_output_lines
    global overflow_flag
    global is_atty

    if not is_atty:
        if isinstance(content, list):
            for line in content:
                print(line)
        elif isinstance(content, dict):
            for k, v in sorted(content.items(), key=lambda x: x[0]):
                print("{}: {}".format(k, v))
        else:
            raise TypeError("Excepting types: list, dict. Got: {}".format(type(content)))
        return

    columns, rows = get_terminal_size()
    lines = lines_of_content(content, columns)
    if force_single_line is False and lines > rows:
        overflow_flag = True
    elif force_single_line is True and len(content) > rows:
        overflow_flag = True

    # 确保初始输出位置是位于最左处的
    # to make sure the cursor is at the left most
    print("\b" * columns, end="")

    if isinstance(content, list):
        for line in content:
            _line = preprocess(line)
            print_line(_line, columns, force_single_line)
    elif isinstance(content, dict):
        for k, v in sorted(content.items(), key=lambda x: x[0]):
            _k, _v = map(preprocess, (k, v))
            print_line("{}: {}".format(_k, _v), columns, force_single_line)
    else:
        raise TypeError("Excepting types: list, dict. Got: {}".format(type(content)))

    # 输出额外的空行来清除上一次输出的剩余内容
    # do extra blank lines to wipe the remaining of last output
    print(" " * columns * (last_output_lines - lines), end="")

    # 回到初始输出位置
    # back to the origin pos
    print(magic_char * (max(last_output_lines, lines)-1), end="")
    sys.stdout.flush()
    last_output_lines = lines


class output:

    class SignalList(list):

        def __init__(self, parent, obj):
            super(output.SignalList, self).__init__(obj)
            self.parent = parent
            self.lock = threading.Lock()

        def change(self, newlist):
            with self.lock:
                if six.PY2:
                    self[:] = []
                else:
                    self.clear()
                self.extend(newlist)
                self.parent.refresh(int(time.time()*1000), forced=False)

        def __setitem__(self, key, value):
            global is_atty
            with self.lock:
                super(output.SignalList, self).__setitem__(key, value)
                if not is_atty:
                    print("{}".format(value))
                else:
                    self.parent.refresh(int(time.time()*1000), forced=False)

    class SignalDict(dict):

        def __init__(self, parent, obj):
            super(output.SignalDict, self).__init__(obj)
            self.parent = parent
            self.lock = threading.Lock()

        def change(self, newlist):
            with self.lock:
                self.clear()
                super(output.SignalDict, self).update(newlist)
                self.parent.refresh(int(time.time()*1000), forced=False)

        def __setitem__(self, key, value):
            global is_atty

            with self.lock:
                super(output.SignalDict, self).__setitem__(key, value)
                if not is_atty:
                    print("{}: {}".format(key, value))
                else:
                    self.parent.refresh(int(time.time()*1000), forced=False)

    def __init__(self, output_type="list", initial_len=1, interval=0, force_single_line=False, no_warning=False):
        self.no_warning = no_warning
        no_warning and print("All reprint warning diabled.")

        global is_atty
        # reprint does not work in the IDLE terminal, and any other environment that can't get terminal_size
        if is_atty and not all(get_terminal_size()):
            if not no_warning:
                r = input("Fail to get terminal size, we got {}, continue anyway? (y/N)".format(get_terminal_size()))
                if not (r and isinstance(r, str) and r.lower()[0] in ['y','t','1']):
                    sys.exit(0)

            is_atty = False


        if output_type == "list":
            self.warped_obj = output.SignalList(self, [''] * initial_len)
        elif output_type == "dict":
            self.warped_obj = output.SignalDict(self, {})

        self.interval = interval
        self.force_single_line = force_single_line
        self._last_update = int(time.time()*1000)

    def refresh(self, new_time=0, forced=True):
        if new_time - self._last_update >= self.interval or forced:
            print_multi_line(self.warped_obj, self.force_single_line)
            self._last_update = new_time

    def __enter__(self):
        global is_atty
        if not is_atty:
            if not self.no_warning:
                print("Not in terminal, reprint now using normal build-in print function.")

        return self.warped_obj

    def __exit__(self, exc_type, exc_val, exc_tb):
        global is_atty

        self.refresh(forced=True)
        if is_atty:
            columns, _ = get_terminal_size()
            if self.force_single_line:
                print('\n' * len(self.warped_obj), end="")
            else:
                print('\n' * lines_of_content(self.warped_obj, columns), end="")
            global last_output_lines
            global overflow_flag
            last_output_lines = 0
            if overflow_flag:
                if not self.no_warning:
                    print("Detected that the lines of output has been exceeded the height of terminal windows, which \
                    caused the former output remained and keep adding new lines.")
                    print("检测到输出过程中, 输出行数曾大于命令行窗口行数, 这会导致输出清除不完整, 而使输出不停增长。请注意控制输出行数。")
