#!/usr/bin/env python

import os
import sys
import copy
import time
import logging
from hashlib import md5
from bson.objectid import ObjectId
from tornado.web import asynchronous
from torext import errors, params
from torext.app import TorextApp
from torext.handlers import BaseHandler as _BaseHandler
import pymongo.errors
from pymongo import Connection
import json


app = TorextApp(extra_settings={
    'COOKIE_SECRET': 'P0UTa5iuRaaVlV8QZF2uVR7hHwTOSkQhg2Fol18OKwc=',
    'TEMPLATE_PATH': 'templates',
    'PORT': os.environ.get('PORT', '8001')
})

#app.set_root_path()
#print 'root', app.root_path

app.setup()


def _handle_object_for_json(obj):
    if isinstance(obj, ObjectId):
        return str(obj)


@app.register_json_encoder
def encode_json(data):
    return json.dumps(data, default=_handle_object_for_json)


mongodb_uri = os.getenv('MONGOHQ_URL', 'mongodb://localhost:27017/chatroom')

if app.settings['DEBUG']:
    logging.info('Dev env')
else:
    logging.info('Heroku env')
    logging.info('mongodb uri: %s', mongodb_uri)

try:
    db = Connection(mongodb_uri)[mongodb_uri.split('/')[-1]]
except pymongo.errors.ConnectionFailure, e:
    logging.error('mongodb connection failed: %s, %s', mongodb_uri, e)
    sys.exit(1)


md5_string = lambda x: md5(x).hexdigest()


class BaseHandler(_BaseHandler):
    db = db

    EXCEPTION_HANDLERS = {
        (errors.ParamsInvalidError, errors.OperationNotAllowed): '_handle_400',
        errors.AuthenticationNotPass: '_handle_401',
        #errors.ObjectNotFound: '_handle_404'
    }

    def json_error(self, code, error=None):
        msg = {'code': code}
        if isinstance(error, str):
            msg['error'] = error
        else:
            msg['error'] = str(error)
            logging.info('Get exc to write: %s - %s' %
                         (error.__class__.__name__, error))

        self.set_status(code)
        self.write_json(msg, code=code)

    def _handle_400(self, e):
        self.json_error(400, e)

    def _handle_401(self, e):
        self.json_error(401, e)

    def _handle_404(self, e):
        self.json_error(404, e)


class AuthMixin(object):
    def authenticate(self):
        user_id = self.get_secure_cookie('user_id')
        if not user_id:
            raise errors.AuthenticationNotPass('could not get user_id')
        try:
            user_id = ObjectId(user_id)
        except:
            raise errors.AuthenticationNotPass('could not transform user_id in to ObjectId')
        cur = self.db.users.find({'_id': user_id})
        if not cur.count():
            raise errors.AuthenticationNotPass('could not find user by user_id')
        self.user = cur.next()

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
        offline_time
    """
    password_salt = 'Est Sularus oth Mithas'

    def generate_password(self, raw):
        return md5_string(raw + self.password_salt)

    def check_password(self, raw, password):
        return md5_string(raw + self.password_salt) == password

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

    def update_user(self, data):
        _id = self.db.users.update(
            {'_id': self.user['_id']},
            {'$set': data},
            safe=True)
        if not _id:
            raise errors.DatabaseError('mongodb save failed: %' % data)
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
    def create_message(self, content, color):
        t = time.time()
        # dt = datetime.datetime.fromtimestamp(t)
        msg = {
            '_id': ObjectId(),
            'username': self.user['username'],
            'content': content,
            'color': color,
            'time': t,
            # 'datetime': dt.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.save_message(msg)
        return msg

    def save_message(self, msg):
        _id = self.db.messages.save(msg, safe=True)
        if not _id:
            raise errors.DatabaseError('mongodb insert failed: %' % msg)
        return _id


def load_messages(after=None, limit=15):
    print 'load messages'
    if after:
        cur = db.messages.find({'time': {'$lt': after['time']}})
    else:
        cur = db.messages.find()
    cur = cur.sort('time', -1).limit(limit)
    return list(cur)


class PollMixin(object):
    waiters = set()
    cache = load_messages()
    cache_size = 200
    _online_users_numbers = 0

    def get_online_users(self):
        return PollMixin._online_users_numbers

    def is_online(self, username):
        cls = PollMixin
        for hdr in cls.waiters:
            if hasattr(hdr, 'user') and hdr.user['username'] == username.lower():
                return True
        return False

    def send_messages(self, msgs):
        if self.request.connection.stream.closed():
            return

        if isinstance(msgs, list):
            # as messages are stored in time-desc sequence,
            # need to reverse it before send to client
            # NOTE directly call reverse will change PollMixin.cache
            # which may be the source of msgs
            msgs = copy.copy(msgs)
            msgs.reverse()
        else:
            msgs = [msgs, ]

        d = {
            'messages': msgs,
            'online_users_number': PollMixin._online_users_numbers
        }

        self.write_json(d)
        self.finish()

    def new_message(self, msg):
        cls = PollMixin
        logging.info("Sending new messages to %r listeners", len(cls.waiters))

        # update online users counter
        cls._online_users_numbers = len([i for i in cls.waiters if hasattr(i, 'user')])

        for hdr in cls.waiters:
            try:
                hdr.send_messages(msg)
            except:
                logging.error("Error in waiter`s calling send_message()", exc_info=True)

        # clear waiters
        cls.waiters = set()

    def insert_to_cache(self, msg):
        cls = PollMixin
        cls.cache.insert(0, msg)
        if len(cls.cache) > self.cache_size:
            cls.cache = cls.cache[:self.cache_size]


class AuthedHandler(BaseHandler, AuthMixin):
    PREPARES = ['auth']

    def prepare_auth(self):
        self.authenticate()


class HomeHandler(BaseHandler):
    def get(self):
        self.render("index.html")


class ChatMessagesRecentsHdr(BaseHandler, PollMixin):
    def get(self):
        cache = PollMixin.cache
        if len(cache) == 0:
            self.send_messages([])
        else:
            if len(cache) > 10:
                msgs = cache[:10]
            else:
                msgs = cache
            self.send_messages(msgs)


class MessagesUpdateParams(params.ParamSet):
    last_message_id = params.Field()
    anonymous = params.Field()

    def validate_last_message_id(self, value):
        try:
            value = ObjectId(value)
        except:
            raise errors.ValidationError('Not a valid objectid string: %s' % value)
        return value


class ChatMessagesUpdateHdr(BaseHandler, AuthMixin, PollMixin, UserMixin):
    @asynchronous
    @MessagesUpdateParams.validation_required
    def post(self):
        print '/chat/messages/updates params', self.params

        if not 'anonymous' in self.params.data:
            try:
                self.authenticate()
                print 'user connected:', self.user['username']
            except errors.AuthenticationNotPass:
                pass

        self.wait_for_messages(id=self.params.data.get('last_message_id', None))

    def wait_for_messages(self, id=None):
        cls = PollMixin

        if id and len(PollMixin.cache) != 0:
            # need to load some recent messages
            if cls.cache[0]['_id'] != id:
                pos = None
                for i in xrange(len(cls.cache)):
                    if cls.cache[i]['_id'] == id:
                        pos = i
                        break
                if pos is not None:
                    self.send_messages(cls.cache[:pos])
                    return
                else:
                    logging.warning('Could positioning the last message in cache, response error')
                    raise errors.OperationNotAllowed('Could not find the last message id, try polling without id')

        cls.waiters.add(self)

        print 'listeners:', len(cls.waiters)

    def cancel_wait(self):
        print 'cancel wait'
        cls = PollMixin

        cls.waiters.remove(self)

        if hasattr(self, 'user'):
            self.update_user({'offline_time': time.time()})

    def on_connection_close(self):
        self.cancel_wait()


class ChatMessagesHdr(AuthedHandler, MessageMixin, PollMixin):
    @params.define_params({
        'content': params.Field(required=True)
    })
    def post(self):
        """
        This method is not asynchronous, so each message
        append to PollMixin.cache is in time sequence
        """
        msg = self.create_message(self.params.content, self.user['color'])

        # add message to message cache
        self.insert_to_cache(msg)

        self.new_message(msg)


class LoginParams(params.ParamSet):
    username = params.RegexField('username must be words in 4~16 range',
                                 pattern=ur'[a-zA-Z0-9\u2E80-\u9FFF]+',
                                 required=True, length=(4, 16))
    password = params.RegexField('password must be words&symbols in 6~16 range',
                                 pattern=r'^[A-Za-z0-9@#$%^&+=]+$')
    color = params.Field(required=True)


class LoginHdr(BaseHandler, AuthMixin, UserMixin, PollMixin):
    def get(self):
        self.render('login.html', message='Welcome')

    @LoginParams.validation_required
    def post(self):
        print 'username', self.params.username
        print 'all users', [i.user for i in PollMixin.waiters if hasattr(i, 'user')]
        if self.is_online(self.params.username):
            raise errors.AuthenticationNotPass('This user is online')

        cur = self.db.users.find({'username_lower': self.params.username.lower()})
        if cur.count() == 0:
            user = self.create_user(self.params.username, self.params.color,
                                    password=self.params.data.get('password', None))
        else:
            user = cur.next()

            # if user has password
            if not user['is_anonymous']:
                if not 'password' in self.params.data:
                    raise errors.AuthenticationNotPass('Need password')
                if not self.check_password(self.params.password, user['password']):
                    raise errors.AuthenticationNotPass('Password invalid')
            # add password to this user
            else:
                if 'password' in self.params.data:
                    user['is_anonymous'] = False
                    user['password'] = self.generate_password(self.params.password)
                    self.save_user(user)

        print user

        self.authorize(user)
        self.write_json(user)


class LogoutHdr(BaseHandler):
    def get(self):
        self.clear_cookie("user_id")


class RoomHdr(BaseHandler, PollMixin):
    def get(self):
        info = {
            'online_users': self.get_online_users()
        }
        self.write_json(info)


class UsersMeHdr(AuthedHandler, PollMixin):
    def get(self):
        d = copy.copy(self.user)
        d['is_online'] = self.is_online(d['username']) and True or False
        self.write_json(d)


class AsyncTestHdr(BaseHandler):
    @asynchronous
    def get(self):
        print '---- async test ----'
        time.sleep(30)


app.route_many([
    (r"/", HomeHandler),
    (r"/auth/login", LoginHdr),
    (r"/auth/logout", LogoutHdr),
    (r"/chat/messages", ChatMessagesHdr),
    (r"/chat/messages/recents", ChatMessagesRecentsHdr),
    (r"/chat/messages/updates", ChatMessagesUpdateHdr),
    (r"/room", RoomHdr),
    (r"/users/me", UsersMeHdr),

    (r"/test/async", AsyncTestHdr),
])


if __name__ == "__main__":
    app.command_line_config()
    app.run()
