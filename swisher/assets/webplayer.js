
$(document).ready(function() {
  function websocketConnect() {
          websocket = 'ws://' + hostname + '/webcontrol'
          if (window.WebSocket) {
            ws = new WebSocket(websocket);
          } else if (window.MozWebSocket) {
            ws = MozWebSocket(websocket);
          } else {
            showNoWebSocket()
            return;
          }

          function makeActive() {
             ws.send('MAKEACTIVE');
             return false;
          }
          function showActive() {
            $('#active').html('')
          }
          function showNotActive() {
            $('#active').html("This is not the active swisher windows. <br> " +
               "There is another swisher window used for playing. <br>" +
               "<input type='button' id='makeactive' value='Make Active' />")
            $('#makeactive').click(function() { ws.send("MAKEACTIVE"); return false })
          }
          function showNoWebSocket() {
            $('#active').html('This browser does not support websockets so it can not be used with swisher. Please install a recent version of firefox chrome or IE10')
          }
          function showDisconnected() {
            $('#active').html('Disconnected. Swisher is not running <br>' +
             "<input type='button' id='reconnect' value='Reconnect' />")
            $('#reconnect').click(websocketConnect())
          }
          window.onbeforeunload = function(e) {
            if(!e) e = window.event;
            e.stopPropagation();
            e.preventDefault();
          };
          var current_videoid = ""
          ws.onmessage = function (evt) {
             if (evt.data == 'ACTIVE') {
               showActive()
             } else if (evt.data == "REPLACED") {
               showNotActive()
             } else if (evt.data == "PING") {
               //Ignore
             } else {
               var value = JSON.parse(evt.data)
               var action = value["action"]
               var player = jQuery("#youtube-player-container")
               if (action) {
                 if (action == "pause") {
                     if (player.tubeplayer("player").getPlayerState() == 2) { //paused
                       player.tubeplayer("play") 
                     } else {
                       player.tubeplayer("pause") 
                     }
                 }
                 if (action == "stop") {
                     jQuery("#youtube-player-container").tubeplayer("pause") 
                 }
               } else {
                 videoid = value['play_youtube'] 
                 if (current_videoid == videoid) {
                     player.tubeplayer("seek", 0)
                     player.tubeplayer("play")
                 } else {
                     current_videoid = videoid
                     player.tubeplayer("play", videoid)
                 }
               }
             }
          };
          ws.onopen = function() {
             showNotActive()
          };
          ws.onclose = function(evt) {
             showDisconnected()
          };
    }
    websocketConnect()
jQuery("#youtube-player-container").tubeplayer({
	width: 600, // the width of the player
	height: 450, // the height of the player
	allowFullScreen: "true", // true by default, allow user to go full screen
	initialVideo: "", // the video that is loaded into the player
	preferredQuality: "default",// preferred quality: default, small, medium, large, hd720
	onPlay: function(id){}, // after the play method is called
	onPause: function(){}, // after the pause method is called
	onStop: function(){}, // after the player is stopped
	onSeek: function(time){}, // after the video has been seeked to a defined point
	onMute: function(){}, // after the player is muted
	onUnMute: function(){} // after the player is unmuted
});
        });

