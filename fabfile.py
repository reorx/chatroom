#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fabric.api import run, hosts, abort, local, cd
from fabric.contrib.console import confirm

HOST = 'root@reorx.com'


@hosts(HOST)
def test_conn():
    run('pwd')
    run('cd /etc/ziproxy')
    run('pwd')


@hosts(HOST)
def update():
    with cd('cd /root/projects/chatroom'):
        res = run('git pull')
        if res.failed:
            abort('code update failed, abort')
        res = run('make')
        if res.failed:
            abort('make failed, abort')

    #if default_file not in args:
        #if confirm('Also update ziproxy.conf, right ?'):
            #args = (default_file, ) + args

    #print '1. backup server side configs'
    #res = run('tar czf /root/ziproxy.confbak.tar.gz /etc/ziproxy')
    #if res.failed:
        #abort('backup failed, abort')

    #print '2. copy files'
    #local('scp %s %s:/etc/ziproxy/' % (' '.join(args), HOST))

    #print '3. restart service'
    #res = run('service ziproxy restart')
    #if res.failed:
        #res = run('service ziproxy start')

    #if res.failed:
        #print 'Failed !'
    #else:
        #print 'OK !'


def recover_server():
    """
    do this if update_server failed
    """
    pass


def sync_log():
    local('scp %s:/var/log/ziproxy/*.log log/' % HOST)
