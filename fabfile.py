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
def poll():
    with cd('/root/projects/torext'):
        res = run('git pull')

    with cd('/root/projects/chatroom'):
        res = run('git pull')
        if res.failed:
            abort('code update failed, abort')
        res = run('cp Makefile.product Makefile && make')
        if res.failed:
            abort('make failed, abort')
        run('cp static /home/admin -r')


@hosts(HOST)
def restart_supervisor():
    with cd('/root/supervisor'):
        run('cp /root/projects/chatroom/supervisor.chatroom.conf conf.d/')
        run('kill `cat supervisord.pid`')
        res = run('supervisord')
        if res.failed:
            abort('restart supervisor failed, abort')


@hosts(HOST)
def restart_nginx():
    with cd('/etc/nginx'):
        run('cp /root/projects/chatroom/nginx.chatroom.conf conf.d/')
        res = run('service nginx restart')
        if res.failed:
            abort('restart nginx failed, abort')


@hosts(HOST)
def update():
    push()

    poll()

    restart_supervisor()

    restart_nginx()


@hosts(HOST)
def update_static():
    push()

    poll()

    restart_nginx()


@hosts(HOST)
def drop_db():
    with cd('/root/projects/chatroom'):
        run('python manager.py drop_db')


@hosts(HOST)
def backup_db():
    pass


@hosts(HOST)
def sync_logs():
    pass
