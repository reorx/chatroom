#!/usr/bin/env python

import re
import copy
import time
import datetime
import logging
from bson.objectid import ObjectId
from tornado.web import asynchronous

import torext
from torext import errors
from torext.app import TorextApp
from torext.conns import conns
from torext.lib.hashs import md5_string
from torext.handlers import _BaseHandler, define_api
from torext.lib.validator import RegexValidator

import settings
torext.initialize(settings)


PASSWORD_VALIDATOR = RegexValidator(6, 16, 'must be words&symbols in 6~16 range',
    regex=re.compile(r'^[A-Za-z0-9@#$%^&+=]+$'))

USERNAME_VALIDATOR = RegexValidator(4, 16, 'must be words in 4~16 range',
    regex=re.compile(ur'[a-zA-Z0-9\u2E80-\u9FFF]+'))


class AuthMixin(object):

    def authenticate(self):
        user_id = self.get_secure_cookie('user_id')
        if user_id:
            try:
                user_id = ObjectId(user_id)
            except:
                pass
            else:
                cur = self.db.users.find({'_id': user_id})
                if cur.count() > 0:
                    self.user = cur.next()
                    return

        raise errors.AuthenticationNotPass('Authentication not pass')

    def authorize(self, user):
        self.set_secure_cookie('user_id', str(user['_id']))


class UserMixin(object):
    """
    User
        _id
        username
        username_lower
        is_anonymous
        password
        color
        logout_time
    """
    def generate_password(self, raw):
        salt = 'Est Sularus oth Mithas'
        return md5_string(raw + salt)

    def check_password(self, raw, pwd):
        salt = 'Est Sularus oth Mithas'
        return md5_string(raw + salt) == pwd

    def create_user(self, username, color, password=None):
        user = {
            'username': username,
            'username_lower': username.lower(),
            'is_anonymous': True,
            'color': color
        }
        if password:
            user['is_anonymous'] = False
            user['password'] = self.generate_password(password)
        _id = self.save_user(user)
        user['_id'] = _id
        return user

    def save_user(self, user):
        _id = self.db.users.save(user, safe=True)
        if not _id:
            raise errors.DatabaseError('mongodb insert failed: %' % user)
        return _id


class MessageMixin(object):
    """
    Message
     - _id
     - username
     - content
     - time
     - hourtime
     - datetime
    """
    def create_message(self, content):
        t = time.time()
        dt = datetime.datetime.fromtimestamp(t)
        msg = {
            '_id': ObjectId(),
            'username': self.user['username'],
            'content': content,
            'time': t,
            'datetime': dt.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.save_message(msg)
        return msg

    def save_message(self, msg):
        _id = self.db.messages.save(msg, safe=True)
        if not _id:
            raise errors.DatabaseError('mongodb insert failed: %' % msg)
        return _id


class PollMixin(object):
    waiters = set()
    cache = []
    cache_size = 200
    _online_users = 0

    def get_online_users(self):
        cls = PollMixin
        # return [i.im_self.user for i in cls.waiters if hasattr(i.im_self, 'user')]
        return cls._online_users

    def is_online(self, username):
        cls = PollMixin
        for i in cls.waiters:
            hdr = i.im_self
            if hasattr(hdr, 'user') and hdr.user['username'] == username.lower():
                return True
        return False

    def wait_for_messages(self, callback, id=None):
        cls = PollMixin

        if id and len(PollMixin.cache) != 0:
            # need to load some recent messages
            if cls.cache[-1]['_id'] != id:
                pos = None
                for i in xrange(len(cls.cache)):
                    if cls.cache[i]['_id'] == id:
                        pos = i
                        break
                if pos is not None:
                    callback(cls.cache[pos:])
                    return
                else:
                    logging.warning('Could positioning the last message in cache, response error')
                    raise errors.OperationNotAllowed('Could not find the last message id, try polling without id')

        cls.waiters.add(callback)

        if hasattr(self, 'user'):
            cls._online_users += 1

        print 'listeners:', len(cls.waiters)

    def cancel_wait(self):
        cls = PollMixin
        cls.waiters.remove(self.on_new_messages)

        if hasattr(self, 'user'):
            cls._online_users -= 1

    def sendMessage(self, msg):
        cls = PollMixin
        logging.info("Sending new messages to %r listeners", len(cls.waiters))

        for callback in cls.waiters:
            try:
                callback(msg)
            except:
                logging.error("Error in waiter callback", exc_info=True)

        # clear waiters
        cls.waiters = set()

        # add message to message cache
        cls.cache.append(msg)
        if len(cls.cache) > self.cache_size:
            cls.cache = cls.cache[-self.cache_size:]


class BaseHandler(_BaseHandler):

    db = conns.get('mongodb', 'master').chatroom

    HTTP_STATUS_EXCEPTIONS = {
        # 400: (errors.ParametersInvalid, errors.OperationNotAllowed),
        (errors.ParametersInvalid, errors.OperationNotAllowed): '_handle_400',
        # 401: (errors.AuthenticationNotPass),
        (errors.AuthenticationNotPass): '_handle_401',
        # 404: (errors.ObjectNotFound)
        (errors.ObjectNotFound): '_handle_404'
    }

    def _handle_400(self, e):
        self.json_error(400, e)

    def _handle_401(self, e):
        self.json_error(401, e)

    def _handle_404(self, e):
        self.json_error(404, e)


class AuthedHandler(BaseHandler, AuthMixin):
    PREPARES = ['auth']

    def _prepare_auth(self):
        self.authenticate()


class MainHandler(BaseHandler):
    def get(self):
        self.render("index.html")


def _validate_objectid(v):
    try:
        return ObjectId(v)
    except:
        raise errors.ValidationError('Not a valid objectid string')


class ChatMessagesUpdateHdr(BaseHandler, AuthMixin, PollMixin):
    @asynchronous
    @define_api([
        # ('recents', False)
        ('last_message_id', False, _validate_objectid),
        ('anonymous', False)
    ])
    def post(self):
        print '/chat/messages/updates params', self.params

        if not 'anonymous' in self.params:
            try:
                self.authenticate()
                print 'user connected:', self.user['username']
            except errors.AuthenticationNotPass:
                pass

        if 'last_message_id' in self.params:
            self.wait_for_messages(self.on_new_messages, id=self.params.last_message_id)
        else:
            cache = PollMixin.cache
            if len(cache) == 0:
                self.wait_for_messages(self.on_new_messages)
            else:
                if len(cache) > 10:
                    msgs = cache[-10:]
                else:
                    msgs = cache
                self.json_write(msgs)
                return

    def on_new_messages(self, messages):
        if self.request.connection.stream.closed():
            return
        self.json_write(messages)

    def on_connection_close(self):
        self.cancel_wait()


class ChatMessagesHdr(AuthedHandler, MessageMixin, PollMixin):
    @define_api([
        ('content', True)
    ])
    def post(self):
        """
        This method is not asynchronous, so each message
        append to PollMixin.cache is in time sequence
        """
        msg = self.create_message(self.params.content)
        # extra value
        msg['color'] = self.user['color']
        print 'msg ', msg

        self.sendMessage(msg)


class LoginHdr(BaseHandler, AuthMixin, UserMixin, PollMixin):
    def get(self):
        self.render('login.html', message='Welcome')

    @define_api([
        ('username', True, USERNAME_VALIDATOR),
        ('color', True),
        ('password', False, PASSWORD_VALIDATOR)
    ])
    def post(self):
        print 'username', self.params.username
        print 'all users', [i.im_self.user for i in PollMixin.waiters if hasattr(i.im_self, 'user')]
        if self.is_online(self.params.username):
            raise errors.AuthenticationNotPass('This user is online')

        cur = self.db.users.find({'username_lower': self.params.username.lower()})
        if cur.count() == 0:
            user = self.create_user(self.params.username, self.params.color,
                password=self.params.get('password', None))
        else:
            user = cur.next()

            # if user has password
            if not user['is_anonymous']:
                if not 'password' in self.params:
                    raise errors.AuthenticationNotPass('Need password')
                if not self.check_password(self.params.password, user['password']):
                    raise errors.AuthenticationNotPass('Password invalid')
            # add password to this user
            else:
                if 'password' in self.params:
                    user['is_anonymous'] = False
                    user['password'] = self.generate_password(self.params.password)
                    self.save_user(user)

        print user

        self.authorize(user)
        self.json_write(user)


class LogoutHdr(BaseHandler):
    def get(self):
        self.clear_cookie("user_id")


class RoomHdr(BaseHandler, PollMixin):
    def get(self):
        info = {
            'online_users': self.get_online_users()
        }
        self.json_write(info)


class UsersMeHdr(AuthedHandler, PollMixin):
    def get(self):
        d = copy.copy(self.user)
        d['is_online'] = self.is_online(d['username']) and True or False
        self.json_write(d)


handlers = [
    (r"/", MainHandler),
    (r"/auth/login", LoginHdr),
    (r"/auth/logout", LogoutHdr),
    (r"/chat/messages", ChatMessagesHdr),
    (r"/chat/messages/updates", ChatMessagesUpdateHdr),
    (r"/room", RoomHdr),
    (r"/users/me", UsersMeHdr),
]


app = TorextApp(handlers)

if __name__ == "__main__":

    app.run()
