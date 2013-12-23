
$(document).ready(function() {

  //a bell sound is played as soon as the card is swiped because videos take a while to buffer
  //without this feedback users don't know if it worked or it's just buffering
  var bellsound = false
  soundManager.setup({
    url: '/assets/soundmanager2.swf',
    onready: function() {
      /* from http://www.freesound.org/people/OTBTechno/sounds/152595/ */
      bellsound = soundManager.createSound({ url: '/assets/bell.wav' })
    }
  })

  function playBell() {
      if (bellsound) { bellsound.play({"loops": 4}) }
  }
  function stopBell() {
      if (bellsound) {
        //stop sound with some fadeout
        bellsound.setVolume(50) 
        setInterval(function() {
         bellsound.stop()
         bellsound.setVolume(100)
        }, 0.3)        
      }
  }
  
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
                     playBell()
                     player.tubeplayer("seek", 0)
                     player.tubeplayer("play")
                 } else {
                     playBell()
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
	onPlayerPlaying: function() { stopBell() }
    })
});

