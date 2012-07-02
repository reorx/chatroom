#!/usr/bin/env python

import re
import time
import logging
import uuid
from bson.objectid import ObjectId
from tornado.web import asynchronous

import torext
from torext import errors
from torext.app import TorextApp
from torext.conns import conns
from torext.lib.hashs import md5_string
from torext.handlers import _BaseHandler, define_api
from torext.lib.validator import RegexValidator, WordsValidator

import settings
torext.initialize(settings)


PASSWORD_VALIDATOR = RegexValidator(6, 32, 'must be words&symbols in 6~32 range',
    regex=re.compile(r'^[A-Za-z0-9@#$%^&+=]+$'))

USERNAME_VALIDATOR = WordsValidator(4, 16, 'must be words in 4~16 range')


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


class AuthedHandler(BaseHandler, AuthMixin):
    PREPARES = ['auth']

    def _prepare_auth(self):
        self.authenticate()


class MainHandler(BaseHandler):
    def get(self):
        self.render("index.html")


class MessageMixin(object):
    waiters = set()
    messages = []
    cache_size = 200

    def get_online_users(self):
        cls = MessageMixin
        # print 'get online users'
        # for i in cls.waiters:
        #     print i.im_self
        return [i.im_self.user for i in cls.waiters if hasattr(i.im_self, 'user')]

    def is_online(self, username):
        for i in self.get_online_users():
            if i['username'] == username:
                return True
        return False

    def wait_for_messages(self, callback, cursor=None):
        cls = MessageMixin

        if cursor:
            index = 0
            for i in xrange(len(cls.messages)):
                index = len(cls.messages) - i - 1
                if cls.messages[index]["id"] == cursor:
                    break
            recent = cls.messages[index + 1:]
            if recent:
                callback(recent)
                return
        cls.waiters.add(callback)

    def cancel_wait(self, callback):
        cls = MessageMixin
        cls.waiters.remove(callback)

    def new_messages(self, messages):
        cls = MessageMixin
        logging.info("Sending new message to %r listeners", len(cls.waiters))
        for callback in cls.waiters:
            try:
                callback(messages)
            except:
                logging.error("Error in waiter callback", exc_info=True)
        cls.waiters = set()
        cls.messages.extend(messages)
        if len(cls.messages) > self.cache_size:
            cls.messages = cls.messages[-self.cache_size:]


class MessageUpdatesHandler(BaseHandler, AuthMixin, MessageMixin):
    @define_api([
        ('cursor', False)
    ])
    @asynchronous
    def post(self):
        try:
            self.authenticate()
        except errors.AuthenticationNotPass:
            pass
        self.wait_for_messages(self.on_new_messages,
                               cursor=self.params.get('cursor', None))

    def on_new_messages(self, messages):
        # Closed client connection
        if self.request.connection.stream.closed():
            return
        self.finish(dict(messages=messages))

    def on_connection_close(self):
        self.cancel_wait(self.on_new_messages)


class MessageNewHdr(AuthedHandler, MessageMixin):
    @define_api([
        ('body', True)
    ])
    def post(self):
        message = {
            "id": str(uuid.uuid4()),
            "timestamp": int(time.time()),
            "from": self.user["username"],
            "body": self.params.body
        }
        # message["html"] = self.render_string("message.html", message=message)
        self.write(message)
        self.new_messages([message])


class UserMixin(object):
    """
    User
        _id
        username
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


class LoginHdr(BaseHandler, AuthMixin, UserMixin, MessageMixin):
    def get(self):
        self.render('login.html', message='Welcome')

    @define_api([
        ('username', True, USERNAME_VALIDATOR),
        ('color', True),
        ('password', False, PASSWORD_VALIDATOR)
    ])
    def post(self):
        if self.is_online(self.params.username):
            raise errors.AuthenticationNotPass('This user is online')

        cur = self.db.users.find({'username': self.params.username})
        if cur.count() == 0:
            user = self.create_user(self.params.username, self.params.color,
                password=self.params.get('password', None))
        else:
            user = cur.next()
            # if 'password' in self.params:
            # needs password checking
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
        self.clear_cookie("user")
        self.write("You are now logged out")


class RoomHdr(BaseHandler, MessageMixin):
    def get(self):
        info = {
            'online_users': self.get_online_users()
        }
        self.json_write(info)


class UsersMeHdr(AuthedHandler):
    def get(self):
        print self.user
        self.json_write(self.user)


# class Application(tornado.web.Application):
#     def __init__(self):
#         handlers = [
#             (r"/", MainHandler),
#             (r"/auth/login", LoginHdr),
#             (r"/auth/logout", LogoutHdr),
#             (r"/a/message/new", MessageNewHdr),
#             (r"/a/message/updates", MessageUpdatesHandler),
#             (r"/room", RoomHdr),
#             (r"/users/me", UsersMeHdr),
#         ]
#         settings = dict(
#             cookie_secret="43oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
#             login_url="/auth/login",
#             template_path=os.path.join(os.path.dirname(__file__), "templates"),
#             static_path=os.path.join(os.path.dirname(__file__), "static"),
#             #xsrf_cookies=True,
#             autoescape="xhtml_escape",
#             debug=True
#         )
#         tornado.web.Application.__init__(self, handlers, **settings)


handlers = [
    (r"/", MainHandler),
    (r"/auth/login", LoginHdr),
    (r"/auth/logout", LogoutHdr),
    (r"/a/message/new", MessageNewHdr),
    (r"/a/message/updates", MessageUpdatesHandler),
    (r"/room", RoomHdr),
    (r"/users/me", UsersMeHdr),
]

# if torext.settings['DEBUG']:
#     handlers_str = 'urls:\n' + '\n'.join(['  %s' % str(i) for i in handlers])
#     logging.info(handlers_str)

app = TorextApp(handlers)

if __name__ == "__main__":

    app.run()
