

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    UI.disable_input();

    $.getJSON('/users/me', function (user) {
        $('#username .value').html(user.username);
        UI.enable_input();
    })

    $("#messageInput").live("keypress", function(e) {
        if (e.keyCode == 13) {
            newMessage($(this).val());
            return false;
        }
    });
    $("#messageInput").select();

    updater.poll();
});

var UI = {
    disable_input: function () {
        $('#messageInput').attr('readonly', 'readonly');
    },
    enable_input: function () {
        $('#messageInput').removeAttr('readonly');
    }
}

function newMessage(content) {
    var message = {
        body: content
    };

    // var disabled = form.find("input[type=submit]");
    // disabled.disable();

    $.postJSON("/a/message/new", message, function(response) {
        updater.showMessage(response);
        if (message.id) {
            // form.parent().remove();
            alert('message has id ' + message.id);
        } else {
            $('#messageInput').val('').select();
            // disabled.enable();
        }
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

jQuery.postJSON = function(url, args, callback) {
    args._xsrf = getCookie("_xsrf");
    $.ajax({url: url, data: $.param(args), dataType: "text", type: "POST",
            success: function(response) {
        if (callback) callback(eval("(" + response + ")"));
    }, error: function(response) {
        console.log("ERROR:", response)
    }});
};

jQuery.fn.formToDict = function() {
    var fields = this.serializeArray();
    var json = {}
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value;
    }
    if (json.next) delete json.next;
    return json;
};

jQuery.fn.disable = function() {
    this.enable(false);
    return this;
};

jQuery.fn.enable = function(opt_enable) {
    if (arguments.length && !opt_enable) {
        this.attr("disabled", "disabled");
    } else {
        this.removeAttr("disabled");
    }
    return this;
};

var updater = {
    errorSleepTime: 500,
    cursor: null,

    poll: function() {
        var args = {"_xsrf": getCookie("_xsrf")};
        if (updater.cursor) args.cursor = updater.cursor;
        $.ajax({url: "/a/message/updates", type: "POST", dataType: "text",
                data: $.param(args), success: updater.onSuccess,
                error: updater.onError});
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
