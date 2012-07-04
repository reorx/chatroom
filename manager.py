#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $ torext <command-in-manager>:arguments
#

import torext
import settings

torext.initialize(settings)

from torext.conns import conns

conn = conns.get('mongodb', 'master')
db = conn.chatroom


def drop_db():
    conn.drop_database('chatroom')


if __name__ == '__main__':
    import sys
    cmd = sys.argv[1]
    if cmd in globals():
        print 'run function %s()' % cmd
        globals()[cmd]()
    else:
        print 'no function %s, quit' % cmd
