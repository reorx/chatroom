require.config({
    baseUrl: "/static/js",
    paths: {
        'jquery': 'libs/jquery-amd',
        'underscore': 'libs/underscore-amd',
        'backbone': 'libs/backbone-amd',
        'domReady': 'libs/domReady',
        'jquery-plugins': 'libs/jquery-plugins'
    }
});

require([
    'jquery',
    'underscore',
    'backbone',
    'domReady',
    'jquery-plugins'
], function($, _, Backbone, domReady) {
    // test modules
    console.log('index.js');
    // console.log('underscore', _.each);
    // console.log('backbone', Backbone.Model);

    // define views
    var PanelView = Backbone.View.extend({
        // el: $('#panel')

        events: {
            'click a.tip': 'showPasswordInput',
            'click a.cancel': 'hidePasswordInput',
            'click .colors a': 'selectColor',
            'click .userinfo .logout': 'logout'
            // 'click .loginTitle': 'login'
        },

        initialize: function() {
            var _this = this;

            this.status('Loading', 1, 'info');

            this.renderColor();

            this.inputWidth= '115px',
            this.$username = this.$('input[name="username"]'),
            this.$password = this.$('input[name="password"]');
            this.is_anonymous = true;
            this.color = this.$('.colors a').eq(0).attr('color');
        },

        status: function(content, stay, level) {
            var status = this.$('.status .content');
            if (content === 0) {
                status.fadeOut(function() {
                    status.html('');
                });
            } else {
                switch(level) {
                    case 'warning':
                        status.removeClass('info error').addClass('warning');
                        break;
                    case 'error':
                        status.removeClass('info warning').addClass('error');
                        break;
                    default:
                        status.removeClass('warning error').addClass('info');
                }

                status.html(content).stop(true, true);
                if (stay) {
                    status.fadeIn();
                } else {
                    // status.html(content).fadeIn(function () {
                    //     status.delay(3000).fadeOut();
                    // });
                    status.fadeIn().delay(3000).fadeOut();
                }
            }
            //     $(this).delay(3000).fadeOut();
            // });
        },

        ajaxError: function(jqXHR) {
            json = $.parseJSON(jqXHR.responseText);
            // console.log('ajaxError json', json);
            this.status(json.error, 0, 'error');
        },

        renderColor: function() {
            this.$('.colors a').each(function(loop, item) {
                var block = $(item);
                block.css('background', block.attr('color'));
            });
        },

        selectColor: function(e) {
            var et = $(e.currentTarget);
            this.$('.cursor').appendTo(et.parent());
            this.color = et.attr('color');
        },

        showPasswordInput: function(e) {
            var et = $(e.currentTarget),
                _this = this;
            _this.is_anonymous = false;

            _this.$username.data('width', _this.$username.width() + 'px')
                .animate({
                    width: _this.inputWidth
                });

            et.fadeOut(function() {
                _this.$password.css({'width': _this.inputWidth})
                    .val('').fadeIn();
                _this.$('a.cancel').fadeIn();
            });
        },

        hidePasswordInput: function(e) {
            var et = $(e.currentTarget),
                _this = this;
            _this.is_anonymous = true;

            et.fadeOut();
            _this.$password.fadeOut(function() {
                _this.$username.animate({
                    width: _this.$username.data('width')
                });
                _this.$('a.tip').fadeIn();
            });
        },

        updateRoominfo: function() {
            var _this = this;
            $.ajax({
                url: '/room',
                type: 'GET',
                success: function(json) {
                    console.log('ajax success this', this);
                    _this.$('.roominfo .number').html(json.online_users.length);
                    // _this.$('.roominfo .users')
                }
            });
        },

        login: function() {
            var data = {
                username: this.$username.val(),
                color: this.color
            },
                _this = this;
            if (!this.is_anonymous) data.password = this.$password.val();

            $.ajax({
                url: '/auth/login',
                type: 'POST',
                data: data,
                success: function(json) {
                    _this.status('You have logged in', 0);
                    _this.user = json;

                    chatView.repoll();
                    _this.showUserinfo(json);
                    _this.updateRoominfo();
                },
                error: function(xhr) {
                    _this.ajaxError(xhr);
                }
            });
        },

        _showAndHide: function(toShow, toHide) {
            var $login = this.$('.login'),
                $userinfo = this.$('.userinfo'),
                wrapper = $login.parent();

            wrapper.height(wrapper.height());

            // console.log('toShow', toShow, 'height', toShow.height());
            toHide.fadeOut(function() {
                wrapper.animate({
                    height: toShow.height() + 'px'
                }, 500, function() {
                    toShow.fadeIn();
                });
            });
        },

        showUserinfo: function(user) {
            chatView.enableInput();

            // unbind login button
            this.$('.loginTitle').unbind('click');

            // change userinfo
            this.$('.userinfo .username').html(user.username);

            // animation
            this._showAndHide( this.$('.userinfo'), this.$('.login'));

            // change title
            this.$('.title.loginTitle').removeClass('green')
                .find('.text').fadeOut(function() {
                    $(this).html('Userinfo').fadeIn();
                });

        },

        showLogin: function() {
            var _this = this;

            chatView.disableInput();

            // bind login button
            this.$('.loginTitle').bind('click', function() {
                _this.login();
            });

            // if .login already visible (first load), return the function
            if (this.$('.login').is(':visible')) return;

            // animation
            this._showAndHide( this.$('.login'), this.$('.userinfo'));

            // change title
            this.$('.title.loginTitle').addClass('green')
                .find('.text').fadeOut(function() {
                    $(this).html('Login').fadeIn();
                });
        },

        authenticate: function() {
            var _this = this;
            $.ajax({
                url: '/users/me',
                type: 'GET',
                success: function(json) {
                    _this.user = json;
                    _this.showUserinfo(json);
                },
                error: function() {
                    _this.showLogin();
                },
                complete: function() {
                    _this.updateRoominfo();
                    _this.status(0);
                }
            });
        },

        logout: function() {
            var _this = this;
            $.ajax({
                url: '/auth/logout',
                type: 'GET',
                success: function() {
                    _this.status('You have logged out', 0, 'warning');

                    chatView.repoll();
                    _this.showLogin();
                    _this.updateRoominfo();
                }
            });
        }
    });

    var ChatView = Backbone.View.extend({
        events: {
            'keypress .input textarea': 'checkInput'
        },

        initialize: function() {
            this.errorSleepTime = 500;
            this.$input = this.$('.input textarea');
            this.chatsBody$ = this.$('.chats .body');
            this.dialog_tmpl = $('#tmpl-dialog').html();
            this.message_tmpl = $('#tmpl-message').html();
            this.lastMessage = null;

            this.disableInput();
        },

        enableInput: function() {
            this.$input.removeAttr('readonly')
                .attr('placeholder', 'New message')
                .removeClass('disable');
        },

        disableInput: function() {
            this.$input.attr('readonly', 'readonly')
                .attr('placeholder', 'Login to chat with people')
                .addClass('disable');
        },

        checkInput: function(e) {
            if (e.keyCode == 13) {
                this.postMessage();
                $(e.currentTarget).val('').select();
                return false;
            }
        },

        poll: function(isFirst) {
            console.log('-> poll this:', this);
            var _this = this,
                data = {};

            // get recents on first poll
            if (isFirst) {
                console.log('-> first poll');
                data.recents = true;
            }

            this.connection = $.ajax({
                url: "/chat/messages/updates",
                type: "POST",
                data: data,
                success: function(json) {
                    // console.log('poll json', json);
                    _this.receiveMessages(json);
                },
                error: function(xhr) {
                    // console.log('error, repoll', xhr);

                    if (xhr.statusText == 'abort') {
                        console.log('-> poll in error');
                        _this.poll();
                    } else {
                        // force passing the right 'this'
                        _this.errorSleepTime += 1000;
                        console.log("Unexpected poll error; sleeping for", _this.errorSleepTime, "ms");
                        (function () {
                            window.setTimeout(_this.poll, _this.errorSleepTime);
                        }).call(_this);
                    }
                }
            });
        },

        repoll: function() {
            if (this.connection) {
                console.log('-> repoll');
                // after aborted, it will automatically start polling
                this.connection.abort();
                // this.poll();
            }
        },

        postMessage: function(e) {
            var message = {
                content: this.$input.val()
            },
                _this = this;

            $.ajax({
                url: '/chat/messages',
                type: 'POST',
                data: message,
                error: function(xhr) {
                    panelView.ajaxError(xhr);
                }
            });
        },

        receiveMessages: function(json) {
            var _this = this;
            if (json instanceof Array) {
                // Make sure messages have been sorted by time on the server
                _.each(json, function(message, loop) {
                    _this.showMessage(message);
                });
            } else {
                _this.showMessage(json);
            }

            this.errorSleepTime = 500;
            this.poll();
        },

        showMessage: function(message) {
            /*
             * message
             *  - username
             *  - content
             *  - time
             *  - datetime
             *
             *  - hourtime (extra)
             *  - domId (extra)
             */
            var lastMessage = this.lastMessage,
                date = new Date(message.time * 1000),
                hourtime = date.getHours() + ':' + date.getMinutes();

            function getYmdHM(time) {
                var dt = new Date(time * 1000);
                // console.log('dt', dt, typeof dt);
                var l = [dt.getUTCFullYear(), dt.getUTCMonth(), dt.getUTCDate(), dt.getHours(), dt.getMinutes()],
                    s = '';
                _.each(l, function(i) {
                    s += l.toString();
                });
                return s;
            }

            var needDialog = true, dialog$,
                message$,
                messageContext = {
                    content: message.content,
                    hourtime: hourtime
                };

            if (lastMessage) {
                if (message.username == lastMessage.username) {
                    needDialog = false;
                    if (getYmdHM(message.time) == getYmdHM(lastMessage.time))
                        delete messageContext.hourtime;
                }
            }

            if (needDialog) {
                dialog$ = $.tmpl(this.dialog_tmpl, {
                    username: message.username,
                    color: message.color
                });
                // if (lastMessage)
                //     dialog$.addClass('split');
            }

            message$ = $.tmpl(this.message_tmpl, messageContext);

            console.log('dialog$', dialog$);
            console.log('message$', message$);
            if (dialog$) {
                dialog$.find('.messages').append(message$);
                this.chatsBody$.append(dialog$);
            } else {
                this.$('.dialog:last').find('.messages').append(message$);
            }
            this.$('.chats').animate({scrollTop: this.$('.chats').height()}, 300);

            this.lastMessage = message;
        }
    });

    // will-be-defined-variables of this scope
    var panelView, chatView;

    domReady(function() {
        // views
        panelView = new PanelView({el: $('#panel')}),
        chatView = new ChatView({el: $('#main')});
        // debug
        window.panelView = panelView;
        window.chatView = chatView;

        // connect to server
        chatView.poll(true);

        // authenticate user
        panelView.authenticate();

    });
});