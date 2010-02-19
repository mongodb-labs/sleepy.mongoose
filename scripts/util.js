Sleepy.Mongoose.Util = function() {

    /**
     * Number of seconds/time unit
     * [sec/year, sec/month, sec/day, sec/hour, sec/minute]
     */
    var time_vals = [31104000, 2592000, 86400, 3600, 60];

    /**
     * Pretty names for time units
     */
    var time_units = ['year', 'month', 'day', 'hour', 'minute'];

    /**
     * Pretty names for byte units
     */
    var byte_units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'];

    /**
     * Turn number of seconds into a "pretty" time representation: years, 
     * months, days, etc.
     *
     * @param {Number} time number of seconds
     * @return the prettified time
     * @type String
     */
    get_time_format = function(time) {
        str = "";

        remaining = time;
        for (var i in time_vals) {
            if ((num = Math.floor(remaining/time_vals[i])) > 0) {
                str += num + " " + time_units[i] + (num == 1 ? "" : "s") + " ";
                remaining = remaining - (time_vals[i] * num);
            }
        }

        if (remaining > 0) {
            str += remaining + " seconds";
        }

        return str;
    };

    /**
     * Get the "pretty' size.
     * Uses the fact that sizes are measured base-10 as a hack.
     *
     * @param {Number} bytes size in bytes
     * @returns prettified size
     * @type String
     */
    var get_byte_format = function(bytes) {
        var size = Math.floor(((bytes+"").length-1)/3);
        bytes = bytes/Math.pow(1000, size);
        return bytes + " " + byte_units[size];
    }

};
