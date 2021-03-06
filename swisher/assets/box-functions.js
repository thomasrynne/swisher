function action(value) {
  jQuery.post("/action/invoke", { value: JSON.stringify(value) })
}

function record(value, name) {
  jQuery.post("/action/record", { value: JSON.stringify(value), name: name})
}

function cancelRecord() {
  jQuery.post("/action/cancelrecord")
}

function showDisconnected() {
    $('#status').html("Disconnected.")
    $.each(current, function(key, value ) {
        $("#"+key).html("--")
    })
}
function longPoll() {
    $.ajax({
        type: "POST",
        url: "http://" + hostname + "/longPoll/status",
        data: current,
        success: function(dataX) {
            data = JSON.parse(dataX)
            if (data['action'] == "stopping") {
                showDisconnected()
                setTimeout(longPoll, 5000)
            } else {
                if (data['action'] == "update") {
                    current = data['state']
                }
                $('#status').html("")
                $.each(current, function(key, value ) {
                    $("#"+key).html(value)
                })
                reconnectInterval = 1
                setTimeout(longPoll, 10)
            }
        },
        error: function (xhr, status, err) {
          if (status == "timeout") {
            setTimeout(longPoll, 10)
          } else {
            showDisconnected()
            reconnectInterval = Math.min(reconnectInterval * 2, 20)
            setTimeout(longPoll, reconnectInterval*1000)
          }
        }
    });
}
var hostname = window.location.hostname
if (window.location.port != "") {
    hostname = hostname + ":" + window.location.port
}

var current = { "reader":"", "mpd":"" }
reconnectInterval = 1
longPoll()


