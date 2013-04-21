function action(prefix, value) {
  jQuery.post("/Action/invoke?prefix="+prefix + "&value=" + value)
}

function record(prefix, value) {
  jQuery.post("/Action/record?prefix="+prefix + "&value=" + value)
}

function addListener(elem, callback) {
  elem.data('oldVal', elem.val());
  elem.bind("propertychange keyup input paste", function(event) {
    if (elem.data('oldVal') != elem.val()) {
      elem.data('oldVal', elem.val());
      callback(elem.val())
    }
  })
}
var hostname = window.location.hostname
if (window.location.port != "") {
    hostname = hostname + ":" + window.location.port
}

var current = {}
reconnectInterval = 1
function showDisconnected() {
    $('#status').html("Disconnected.")
    $.each(current, function(key, value ) {
        $("#"+key).html("--")
    })
}
function longPoll() {
    console.log(current)
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


