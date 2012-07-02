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
            'click .colors a': 'selectColor'
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

        authenticate: function() {
            var _this = this;
            $.ajax({
                url: '/users/me',
                type: 'GET',
                success: function(json) {
                    _this.showUserinfo(json);
                    // because yourself logged in
                    _this.updateRoominfo();
                },
                error: function() {
                    _this.$('.loginTitle').bind('click', function() {
                        _this.login();
                    });
                },
                complete: function() {
                    _this.status(0);
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
                    _this.$('.loginTitle').unbind('click');
                    _this.showUserinfo(json);

                    // repoll
                    Updater.repoll();
                    // and update roominfo
                    _this.updateRoominfo();
                },
                error: function(xhr) {
                    _this.ajaxError(xhr);
                }
            });
        },

        showUserinfo: function(user) {
            var $login = this.$('.login'),
                $userinfo = this.$('.userinfo'),
                wrapper = $login.parent();

            // change userinfo
            $userinfo.find('.username').html(user.username);
            //.css({'position': 'absolute', 'visibility': 'hidden'})

            // animation
            wrapper.height(wrapper.height());

            $login.fadeOut(function() {
                var h = $login.height() < $userinfo.height() ? $login.height() : $userinfo.height();
                console.log('change to', h);
                wrapper.animate({
                    height: h + 'px'
                }, 500, function() {
                    $userinfo.fadeIn();
                });
            });

            // change title
            this.$('.title.loginTitle').removeClass('green')
                .find('.text').fadeOut(function() {
                    $(this).html('Userinfo').fadeIn();
                });

        },

        showLogin: function() {
            // this.$('.login')
            var _this = this;
            this.$('.loginTitle').bind('click', function() {
                _this.login();
            });
        }
    });

    var ChatView = Backbone.View.extend({
        events: {
            'keypress .input textarea': 'postMessage'
        },

        initialize: function() {
            this.$input = this.$('.input textarea');
            this.disableInput();
        },

        enableInput: function() {
            this.$input.removeAttr('readonly')
                .removeClass('disable');
        },

        disableInput: function() {
            this.$input.attr('readonly', 'readonly')
                .attr('placeholder', 'Login to chat with people')
                .addClass('disable');
        },

        postMessage: function(e) {
            if (e.keyCode == 13) {
            }
        }

    });

    var updater = {
        errorSleepTime: 500,
        cursor: null,

        poll: function() {
            var args = {"_xsrf": $.cookie("_xsrf")};
            if (updater.cursor) args.cursor = updater.cursor;
            this.connection = $.ajax({
                url: "/a/message/updates",
                type: "POST",
                dataType: "text",
                data: $.param(args),
                success: updater.onSuccess,
                error: updater.onError
            });
        },

        repoll: function() {
            if (this.connection) {
                this.connection.abort();
                this.poll();
            }
        },

        onSuccess: function(response) {
            try {
                updater.newMessages(eval("(" + response + ")"));
            } catch (e) {
                updater.onError();
                return;
            }
            updater.errorSleepTime = 500;
            window.setTimeout(updater.poll, 0);
        },

        onError: function(response) {
            updater.errorSleepTime *= 2;
            console.log("Poll error; sleeping for", updater.errorSleepTime, "ms");
            window.setTimeout(updater.poll, updater.errorSleepTime);
        },

        newMessages: function(response) {
            if (!response.messages) return;
            updater.cursor = response.cursor;
            var messages = response.messages;
            updater.cursor = messages[messages.length - 1].id;
            console.log(messages.length, "new messages, cursor:", updater.cursor);
            for (var i = 0; i < messages.length; i++) {
                updater.showMessage(messages[i]);
            }
        },

        showMessage: function(message) {
            var existing = $("#m" + message.id);
            if (existing.length > 0) return;
            // var node = $(message.html);
            console.log('function showMessage');
            var node = $('<div class="message" id="m' + message.id + '"><b>' +
                message.from + ': </b>' + message.body + '</div>');
            node.hide();
            console.log('node', node);
            $("#chat .messages").append(node);
            node.slideDown();
        }
    };

    var Updater = updater;

    domReady(function() {
        // views
        var panelView = new PanelView({el: $('#panel')}),
            chatView = new ChatView({el: $('#main')});
        // debug
        // window.panelView = panelView;
        // window.chatView = chatView;

        // connect to server
        Updater.poll();

        // update roominfo
        panelView.updateRoominfo();

        // authenticate user
        panelView.authenticate();

    });
});