$(document).ready(function() {
	var paused = false;


	$( window ).resize(function() {
		// when header resizes, move ui down
		$('.table-layout').css('margin-top',$('.navbar-collapse').height()-34);
	});

	namespace = '/test'; // change to an empty string to use the global namespace
	var socket = io.connect('http://' + document.domain + ':' + 5000 + namespace);


	socket.on('connect',function() {
		$("#ws-status").toggleClass("led-red led-green");
		$("#ws-status").prop('title', 'Server Online');

		socket.on('machineStatus', function (data) {
			$('#mStatus').html(data.status);
			$('#mX').html('X: '+data.mpos[0]);
			$('#mY').html('Y: '+data.mpos[1]);
			$('#mZ').html('Z: '+data.mpos[2]);
			$('#wX').html('X: '+data.wpos[0]);
			$('#wY').html('Y: '+data.wpos[1]);
			$('#wZ').html('Z: '+data.wpos[2]);
		});

		socket.on('machineSettings', function(data){
			var settingHtml = '<pre>';
			data.forEach(function(setting) {
				settingHtml += '<span>'+setting+'</span>';
			});
			$('#settings').find('.modal-body').html(settingHtml+'</pre>');
		});

		socket.on('disconnect',function() {
			$("#ws-status").toggleClass("led-red led-green");
			$("#ws-status").prop('title', 'Server Offline');
		});

		socket.on('serialRead', function (data) {
			$('#console').append(data.line);
			$('#console').scrollTop($("#console")[0].scrollHeight - $("#console").height());
		});

		socket.on('qStatus', function (data) {
			$('#qStatus').html(data.currentLength+'/'+data.currentMax);
		});

		/*
			socket.on('gcodeFromJscut', function (data) {
				$('#command').val(data.val);
				openGCodeFromText();
				alert('new data from jscut');
			});
		*/



	});

	// All button clicks
	$(document).click(function(item) {
		var itemClicked = item.target.id;
		switch(itemClicked){
			case "chk_singleCommandMode":
				if ($('#chk_singleCommandMode').is(":checked")){
					socket.emit('command',{"cmd":"singleCommandMode","value":true});
				} else {
					socket.emit('command',{"cmd":"singleCommandMode","value":false});
				}
				break;
			case "abort":
			case "sendReset":
				socket.emit('command',{"cmd":"doReset"});
				break;
			case "sendUnlock":
				socket.emit('command',{"cmd":"gcodeLine","line":"$X"});
				break;
			case "sendHome":
				socket.emit('command',{"cmd":"gcodeLine","line":"$H"});
				break;
			case "xM":
				socket.emit('command',{"cmd":"gcodeLine","line":'G91\nG1 F'+$('#jogSpeed').val()+' X-'+$('#jogSize').val()+'\nG90'});
				break;
			case "xP":
				socket.emit('command',{"cmd":"gcodeLine","line":'G91\nG1 F'+$('#jogSpeed').val()+' X'+$('#jogSize').val()+'\nG90'});
				break;
			case "yP":
				socket.emit('command',{"cmd":"gcodeLine","line":'G91\nG1 F'+$('#jogSpeed').val()+' Y'+$('#jogSize').val()+'\nG90'});
				break;
			case "yM":
				socket.emit('command',{"cmd":"gcodeLine","line":'G91\nG1 F'+$('#jogSpeed').val()+' Y-'+$('#jogSize').val()+'\nG90'});
				break;
			case "zP":
				socket.emit('command',{"cmd":"gcodeLine","line":'G91\nG1 F'+$('#jogSpeed').val()+' Z'+$('#jogSize').val()+'\nG90'});
				break;
			case "zM":
				socket.emit('command',{"cmd":"gcodeLine","line":'G91\nG1 F'+$('#jogSpeed').val()+' Z-'+$('#jogSize').val()+'\nG90'});
				break;
			case "sendGrblHelp":
				socket.emit('command',{"cmd":"gcodeLine","line":"$"});
				break;
			case "sendGrblSettings":
				socket.emit('command',{"cmd":"gcodeLine","line":"$$"});
				break;
			case "sendCommand":
				socket.emit('command',{"cmd":"gcodeLine","line":$('#command').val()});
				$('#command').val('');
				break;
			case "sendZero":
				socket.emit('command',{"cmd":"gcodeLine","line":'G92 X0 Y0 Z0'});
				break;
			case "stopStart":
				paused = !paused;
				socket.emit('command',{"cmd":"paused","value":paused});
				break;
			case "pause":
				if ($('#pause').html() == 'Pause') {
					// pause queue on server
					socket.emit('command',{"cmd":"pause","value":true});
					$('#pause').html('Unpause');
					$('#clearQ').removeClass('disabled');
				} else {
					socket.emit('command',{"cmd":"pause","value":false});
					$('#pause').html('Pause');
					$('#clearQ').addClass('disabled');
				}
				break;
			case "clearQ":
				// if paused let user clear the command queue
				socket.emit('command',{"cmd":"clearQ"});
				// must clear queue first, then unpause (click) because unpause does a sendFirstQ on server
				$('#pause').click();
				break;
			case "settings_btn":
				socket.emit('command',{"cmd":"refreshSettings"});
				$('#settings').find('.modal-body').html('Loading...');
				$('#settings').modal('show');
				setTimeout(function (){
					socket.emit('command',{"cmd":"machineSettings"});
				},2000);
				break;
			case "mpC":
				$('#mpA').addClass('active');
				$('#wpA').removeClass('active');
				$('#mPosition').show();
				$('#wPosition').hide();
				break;
			case "wpC":
				$('#wpA').addClass('active');
				$('#mpA').removeClass('active');
				$('#wPosition').show();
				$('#mPosition').hide();
				break;
			case "btn-save-settings":
				var settingsArray = new Array();

				$('#settings .modal-body span').each(function(){
					settingsArray.push($(this).text().substring(0,$(this).text().indexOf(' ')));
				});

				var settings = '';
				for (value of settingsArray) {
					settings += value + '\r\n';
				}

				var savesettings = document.createElement('a');
				savesettings.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(settings));
				savesettings.setAttribute('download', "settings.nc");
				savesettings.style.display = 'none';
				document.body.appendChild(savesettings);
				savesettings.click();
				document.body.removeChild(savesettings)
				break;
			case "fileInput":
				// Work around to enable reload the same file
				document.getElementById('fileInput').value = null;
				break;
		};
	});

	// shift enter for send command
	$('#command').keydown(function (e) {
		if (e.shiftKey) {
			var keyCode = e.keyCode || e.which;
			if (keyCode == 13) {
				// we have shift + enter
				$('#sendCommand').click();
				// stop enter from creating a new line
				e.preventDefault();
			}
		}
	});


	// WASD and up/down keys
	$(document).keydown(function (e) {
		var keyCode = e.keyCode || e.which;

		if ($('#command').is(':focus')) {
			// don't handle keycodes inside command window
			return;
		}

		switch (keyCode) {
		case 65:
			// a key X-
			e.preventDefault();
			$('#xM').click();
			break;
		case 68:
			// d key X+
			e.preventDefault();
			$('#xP').click();
			break;
		case 87:
			// w key Y+
			e.preventDefault();
			$('#yP').click();
			break;
		case 83:
			// s key Y-
			e.preventDefault();
			$('#yM').click();
			break;
		case 38:
			// up arrow Z+
			e.preventDefault();
			$('#zP').click();
			break;
		case 40:
			// down arrow Z-
			e.preventDefault();
			$('#zM').click();
			break;
		}
	});

	// handle gcode uploads
	if (window.FileReader) {

		var reader = new FileReader ();

		// drag and drop
		function dragEvent (ev) {
			ev.stopPropagation ();
			ev.preventDefault ();
			if (ev.type == 'drop') {
				loadFile();
			}
		}

		document.getElementById('command').addEventListener ('dragenter', dragEvent, false);
		document.getElementById('command').addEventListener ('dragover', dragEvent, false);
		document.getElementById('command').addEventListener ('drop', dragEvent, false);


		// button
		var fileInput = document.getElementById('fileInput');

		fileInput.addEventListener('change', function(e) {
			loadFile();
		});

	} else {
		alert('your browser is too old to upload files, get the latest Chromium or Firefox');
	}

	function loadFile(){
			var fileInput = document.getElementById('fileInput');
			reader.onloadend = function (ev) {
				document.getElementById('command').value = this.result;
				//openGCodeFromText();
			};
			reader.readAsText (fileInput.files[0]);
	}

});
