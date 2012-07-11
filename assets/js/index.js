require.config({
    baseUrl: "/static/js",
    paths: {
        'jquery': 'libs/jquery-amd',
        'underscore': 'libs/underscore-amd',
        'backbone': 'libs/backbone-amd',
        'domReady': 'libs/domReady',
        'dateformat': 'libs/dateformat',
        'jquery-plugins': 'libs/jquery-plugins'
    }
});

require([
    'jquery',
    'underscore',
    'backbone',
    'domReady',
    'dateformat',
    'jquery-plugins'
], function($, _, Backbone, domReady) {
    // test modules
    console.log('index.js');
    // console.log('underscore', _.each);
    // console.log('backbone', Backbone.Model);

    var getYmdHM = function(time) {
        var dt = new Date(time * 1000);
        return dt.format('yyyy-mm-dd HH:MM');
    }

    // define views
    var PanelView = Backbone.View.extend({
        // el: $('#panel')

        events: {
            'click a.tip': 'showPasswordInput',
            'click a.cancel': 'hidePasswordInput',
            'click .colors a': 'selectColor',
            'click .userinfo .logout': 'logout',
            'mouseover .title.sec2': 'showPoweredBy'
        },

        initialize: function() {
            var _this = this;

            this.status('Loading', 1, 'info');

            this.renderColor();
            // this.activePoweredBy();

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

        updateRoominfo: function(online_users) {
            var _this = this;
            if (online_users) {
                _this.$('.roominfo .number').html(online_users);
            } else {
                $.ajax({
                    url: '/room',
                    type: 'GET',
                    success: function(json) {
                        console.log('ajax success this', this);
                        _this.$('.roominfo .number').html(json.online_users.length);
                        // _this.$('.roominfo .users')
                    }
                });
            }

        },

        // activePoweredBy: function() {
        showPoweredBy: function() {
            var parent = this.$('.mouseWrapper'),
                toShow = this.$('.pb'),
                _this = this;

            if (toShow.is(':visible'))
                return;

            toShow.slideDown(500, function() {
                $(window).bind('mousemove', function(e2) {
                    var target = $(e2.target);
                    if (target.get(0) !== parent.get(0) && parent.has(target).length === 0 && toShow.is(':visible')) {
                        $(window).unbind('mousemove');
                        toShow.slideUp(500);
                    }
                });
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
            toHide.wrap('<div></div>');
            var wrapper = toHide.parent();
            toShow.appendTo(wrapper);

            wrapper.height(wrapper.height());

            // console.log('toShow', toShow, 'height', toShow.height());
            toHide.fadeOut(function() {
                // wrapper.height(toShow.height());
                wrapper.animate({
                    height: toShow.height() + 'px'
                }, 500, function() {
                    toShow.fadeIn(function() {
                        toShow.unwrap();
                    });
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

        poll: function(anonymous) {
            console.log('-> poll(); this:', this);
            var _this = this,
                data = {};

            if (anonymous)
                data.anonymous = true;

            if (this.lastMessage)
                data.last_message_id = this.lastMessage._id;

            this.connection = $.ajax({
                url: "/chat/messages/updates",
                type: "POST",
                data: data,
                success: function(json) {
                    // console.log('poll json', json);
                    _this.receiveMessages(json);

                    // reset retry time counter
                    _this.errorSleepTime = 500;

                    console.log('-> poll after receiveMessages');
                    _this.poll();
                },
                error: function(xhr) {
                    // console.log('error, repoll', xhr);

                    if (xhr.statusText == 'abort') {
                        console.log('-> repoll by function');
                        _this.poll();
                    } else {
                        if (xhr.responseText) console.log('Poll error:', $.parseJSON(xhr.responseText).error);

                        _this.errorSleepTime += 1000;
                        panelView.status('Connection interrupted, reconnect in ' + _this.errorSleepTime / 1000 + 's',
                            0, 'warning');
                        setTimeout($.proxy(_this.poll, _this), _this.errorSleepTime);
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

        separateMessages: function(content) {
            var dialog = $.tmpl($('#tmpl-dialog-separate'), {content: content});
            this.chatsBody$.append(dialog);
            this.lastMessage = null;
        },

        getRecents: function() {
            var _this = this;
            $.ajax({
                type: 'GET',
                url: '/chat/messages/recents',
                success: function(json) {
                    _this.receiveMessages(json);
                    if (json.messages.length > 0)
                        _this.separateMessages(
                            'last message was send on:&nbsp&nbsp' + getYmdHM(_this.lastMessage.time));
                }
            });
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
            /*
             * json
             *  - messages
             *  - online_users_number
             */
            console.log('-> just receiveMessages');
            var _this = this;

            _.each(json.messages, function(message, loop) {
                _this.showMessage(message);
            });

            panelView.updateRoominfo(json.online_users_number);
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
                hourtime = date.format('HH:MM');


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

        // load recents
        chatView.getRecents();

        // authenticate user
        /*
         * API requesting should following a sequence
         *  1. /users/me
         *  2. /chat/messages/update    /room
         */
        $.ajax({
            url: '/users/me',
            type: 'GET',
            success: function(json) {
                panelView.user = json;
                if (json.is_online) {
                    chatView.poll(true);

                    panelView.status('Duplicate login', 1, 'warning');

                    var loginTitle = panelView.$('.title.loginTitle'),
                        login = panelView.$('.login'),
                        wrapper,
                        time = 500;
                    loginTitle.wrap('<div></div>');
                    wrapper = loginTitle.parent();
                    login.appendTo(wrapper);
                    wrapper.height(wrapper.height());

                    loginTitle.fadeOut(time);
                    login.fadeOut(time);
                    setTimeout(function() {
                        wrapper.animate({
                            height: '0px'
                        }, time + 100, function() {
                            loginTitle.unwrap();
                        });
                    }, time);
                } else {
                    chatView.poll();

                    panelView.showUserinfo(json);
                    panelView.status(0);
                }
                console.log('end success()');
            },
            error: function() {
                panelView.showLogin();

                chatView.poll();
                panelView.status(0);
            },
            complete: function() {
                console.log('start complete()');
                panelView.updateRoominfo();
            }
        });

    });
});