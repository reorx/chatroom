
define('utils', function(_) {

    var exports = {};

    var getYmdHM = exports.getYmdHM = function(time) {
        var dt = new Date(time * 1000);
        // console.log('dt', dt, typeof dt);
        // var l = [dt.getUTCFullYear(), dt.getUTCMonth(), dt.getUTCDate(), dt.getHours(), dt.getMinutes()],
        //     s = '';
        // _.each(l, function(i) {
        //     s += l.toString();
        // });
        return dt.getUTCFullYear() + '-' + dt.getUTCMonth() + '-' + dt.getUTCDate() +
            ' ' + dt.getHours() + ':' + dt.getMinutes();
    };

    return exports;

});
