require.config({
    baseUrl: "/static/js",
    paths: {
        'jquery': 'libs/jquery-amd',
        'underscore': 'libs/underscore-amd',
        'backbone': 'libs/backbone-amd',
        'domReady': 'libs/domReady'
    }
});

require([
    'jquery',
    'underscore',
    'backbone',
    'domReady'
], function($, _, Backbone, domReady) {
    // test modules
    console.log('index.js');
    console.log('underscore', _.each);
    console.log('backbone', Backbone.Model);

    // define views
    var PanelView = Backbone.View.extend({
        // el: $('#panel')

        events: {
            'click a.tip': 'showPasswordInput',
            'click a.cancel': 'hidePasswordInput'
        },

        initialize: function() {
            this.inputWidth= '115px';
        },

        showPasswordInput: function(e) {
            var et = $(e.currentTarget),
                _this = this,
                $username = _this.$('input[name="username"]'),
                $password = _this.$('input[name="password"]');


            $username.data('width', $username.width() + 'px')
                .animate({
                    width: _this.inputWidth
                });

            et.fadeOut(function() {
                $password.css({'width': _this.inputWidth})
                    .fadeIn();
                _this.$('a.cancel').fadeIn();
            });
        },

        hidePasswordInput: function(e) {
            var et = $(e.currentTarget),
                _this = this,
                $username = _this.$('input[name="username"]'),
                $password = _this.$('input[name="password"]');

            et.fadeOut();
            $password.fadeOut(function() {
                $username.animate({
                    width: $username.data('width')
                });
                _this.$('a.tip').fadeIn();
            });
        }
    });

    domReady(function() {
        // jquery
        $('#panel .colors a').each(function(loop, item) {
            // console.log($(item));
            var $this = $(item);
            $this.css('background', $this.attr('color'));
        }).click(function() {
            $('#panel .cursor').appendTo($(this).parent()
            ).show();
        });

        // background
        panelView = new PanelView({el: $('#panel')});

    });
});