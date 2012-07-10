#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fabric.api import run, hosts, abort, local, cd, lcd
# from fabric.contrib.console import confirm

HOST = 'root@reorx.com'


@hosts(HOST)
def test_conn():
    run('pwd')
    run('cd /etc/ziproxy')
    run('pwd')


def push():
    with lcd('~/workspace/current/torext'):
        local('git push')
    local('git push')


@hosts(HOST)
def update():
    push()

    with cd('/root/projects/torext'):
        res = run('git pull')

    with cd('/root/projects/chatroom'):
        res = run('git pull')
        if res.failed:
            abort('code update failed, abort')
        run('cp Makefile.product Makefile && make')
        if res.failed:
            abort('make failed, abort')

    with cd('/root/supervisor'):
        run('cp /root/projects/chatroom/supervisor.chatroom.conf conf.d/')
        run('kill `cat supervisord.pid`')
        res = run('supervisord')
        if res.failed:
            abort('restart supervisor failed, abort')

    with cd('/etc/nginx'):
        run('cp /root/projects/chatroom/nginx.chatroom.conf conf.d/')
        res = run('service nginx restart')
        if res.failed:
            abort('restart nginx failed, abort')

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
