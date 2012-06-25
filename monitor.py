#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import datetime


# alls = filter(lambda v: v, map(lambda m: getattr(m, "__file__", None), sys.modules.values()))


def get_path(root, name):
    path = os.path.join(root, name)
    return os.path.abspath(path)


def get_all_paths(root, ignores=[]):
    """
    recursive all files and dirs under root path,
    return tuple:
        (file path or dir path, is dir or not)
    """
    # (path, is_dir)
    l = []
    for root, dirs, files in os.walk(root):
        def judge_ignore(name):
            for ftype in ignores:
                if name.endswith('.' + ftype):
                    return True
            return False

        for i in dirs:
            l.append(
                (get_path(root, i), True))
        for i in files:
            if judge_ignore(i):
                continue
            l.append(
                (get_path(root, i), False))
    return l


class Monitor(object):
    def __init__(self, init_paths):
        self._refresh_pathd(init_paths)

    def _refresh_pathd(self, paths):
        self._pathd = {}
        for fname, is_dir in paths:
            self._pathd[fname] = (os.stat(fname).st_mtime,
                              is_dir)

    def _last_paths(self):
        return [(i, self._pathd[i][1]) for i in self._pathd]

    def check(self, current):
        last = self._last_paths()
        added = []
        removed = []
        modified = []
        added = [i for i in current\
                    if not i[0] in\
                        [j[0] for j in last]]
        removed = [i for i in last\
                    if not i[0] in\
                        [j[0] for j in current]]
        for i in dict(current).viewkeys() & dict(last).viewkeys():
            if os.stat(i).st_mtime != self._pathd[i][0]:
                # last also fine
                modified.append((i, self._pathd[i][1]))

        if added or removed or modified:
            has_changed = True
        else:
            has_changed = False

        self._refresh_pathd(current)
        return has_changed, added, removed, modified


class Bar(object):
    loop_range = 10

    def __init__(self,
                 char='-',
                 loop_range=10):
        self.char = char
        self.loop_range = loop_range
        self.loop = 0
        self.bar_fm = '[ scaning %s  %s ]'
        self.bar = ''

    def printbar(self):
        char_list = [self.char for i in range(self.loop_range)]
        char_list[self.loop] = ' '
        self.bar = self.bar_fm % (''.join(char_list),
                datetime.datetime.now().strftime('%H:%M:%S'))
        if self.loop == self.loop_range - 1:
            self.loop = 0
        else:
            self.loop += 1

        print self.bar, '\r',
        sys.stdout.flush()


if '__main__' == __name__:

    ROOT = os.getcwd()
    IGNORE = ['swp', 'pyc', 'html', 'css']

    monitor = Monitor(
        get_all_paths(os.path.join(ROOT, 'assets'), IGNORE)
    )
    bar = Bar()
    while True:
        bar.printbar()
        has_changed, added, removed, modified = monitor.check(get_all_paths(os.path.join(ROOT, 'assets'), IGNORE))
        if has_changed:
            print ''
            files = []
            if added:
                for i in added:
                    if not i[1]:  # file
                        print '    ', '[+] ', i[1] and '[dir] ' or '[file] ', i[0]
                        files.append(i[0])
            if modified:
                for i in modified:
                    if not i[1]:  # file
                        print '    ', '[*] ', i[1] and '[dir] ' or '[file] ', i[0]
                        files.append(i[0])
            print ''

            # do things
            print 'Doing on change task'

            #for i in files:
                #if i.split('.')[-1] == 'jade':
                    #name = i.split('.')[-2].split('/')[-1]
                    #cmd = 'jade < %s > %s' % (i, 'build/' + name + '.html')
                #elif i.split('.')[-1] == 'styl':
                    #name = i.split('.')[-2].split('/')[-1]
                    #cmd = 'stylus < %s > %s' % (i, 'build/css/' + name + '.css')

                #print cmd
                #os.system(cmd)

            if files:
                os.system('make')
        time.sleep(0.25)
