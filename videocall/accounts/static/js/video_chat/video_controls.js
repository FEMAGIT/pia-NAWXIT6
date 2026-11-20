controls.style.visibility = "visible";
fullBtn.click(function (e) {
  fullscreen();
});
micBtn.click(function (e) {
  mute();
});
audioBtn.click(function (e) {
  audio_mute();
});

camBtn.click(function (e) {
  disable_cam(remote_video_enabled);
  remote_video_enabled = false;
});

hangUpBtn.click(function (e) {
  ws_system.closeCall(contactInCall);
  ws_webrtc.handleLeave();
});
remoteVideo.addEventListener("ended", stopMedia);

function stopMedia() {
  remoteVideo.pause();
  remoteVideo.currentTime = 0;
  remove_fullscreen;
}

remoteVideo.addEventListener("timeupdate", setTime);

function setTime() {
  var minutes = Math.floor(remoteVideo.currentTime / 60);
  var seconds = Math.floor(remoteVideo.currentTime - minutes * 60);
  var minuteValue;
  var secondValue;

  if (minutes < 10) {
    minuteValue = "0" + minutes;
  } else {
    minuteValue = minutes;
  }

  if (seconds < 10) {
    secondValue = "0" + seconds;
  } else {
    secondValue = seconds;
  }

  var mediaTime = minuteValue + ":" + secondValue;
  timer.textContent = mediaTime;

  var barLength =
    timerWrapper.clientWidth * (remoteVideo.currentTime / remoteVideo.duration);
  timerBar.style.width = barLength + "px";
}

function fullscreen() {
  var docElm = document.getElementById("videos");
  var isInFullScreen =
    (document.fullscreenElement && document.fullscreenElement !== null) ||
    (document.webkitFullscreenElement &&
      document.webkitFullscreenElement !== null) ||
    (document.mozFullScreenElement && document.mozFullScreenElement !== null) ||
    (document.msFullscreenElement && document.msFullscreenElement !== null);

  if (!isInFullScreen) {
    fullBtn
      .removeClass("maximise")
      .removeClass("minimise")
      .addClass("maximise");
    if (docElm.requestFullscreen) {
      docElm.requestFullscreen();
    } else if (docElm.mozRequestFullScreen) {
      docElm.mozRequestFullScreen();
    } else if (docElm.webkitRequestFullScreen) {
      docElm.webkitRequestFullScreen();
    } else if (docElm.msRequestFullscreen) {
      docElm.msRequestFullscreen();
    }
  } else {
    fullBtn
      .removeClass("maximise")
      .removeClass("minimise")
      .addClass("minimise");

    remove_fullscreen();
  }
}

function mute() {
  var mute = ws_webrtc.mute();
  if (mute == null) return;
  if (!mute) {
    micBtn.removeClass("mute").removeClass("unmute").addClass("unmute");
  } else {
    micBtn.removeClass("mute").removeClass("unmute").addClass("mute");
  }
}

function disable_cam(video_enabled) {
  ws_webrtc.remote_video(!video_enabled);
  disable_cam_gui(video_enabled);
}

function disable_cam_gui(video_enabled) {
  if (video_enabled) {
    camBtn
      .removeClass("enable_video")
      .removeClass("disable_video")
      .addClass("enable_video");
  } else {
    camBtn
      .removeClass("enable_video")
      .removeClass("disable_video")
      .addClass("disable_video");
  }
}

function audio_mute() {
  if (remoteVideo.muted) {
    audioBtn
      .removeClass("enable_sound")
      .removeClass("disable_sound")
      .addClass("disable_sound");
    remoteVideo.muted = false;
  } else {
    audioBtn
      .removeClass("enable_sound")
      .removeClass("disable_sound")
      .addClass("enable_sound");
    remoteVideo.muted = true;
  }
}

function remove_fullscreen() {
  var isInFullScreen =
    (document.fullscreenElement && document.fullscreenElement !== null) ||
    (document.webkitFullscreenElement &&
      document.webkitFullscreenElement !== null) ||
    (document.mozFullScreenElement && document.mozFullScreenElement !== null) ||
    (document.msFullscreenElement && document.msFullscreenElement !== null);

  if (isInFullScreen) {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    } else if (document.mozCancelFullScreen) {
      document.mozCancelFullScreen();
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen();
    }
  }
}

function reset_call() {
  remove_fullscreen();
  closeCanvasBtn.click();
  messageTextBox.prop("disabled", true);
  sendMessageTextBox.prop("disabled", true);
  sendLinkTextBox.prop("disabled", true);
  remote_video_enabled = false;
  remoteVideo.muted = false;
  callPage.hide();
  buttorQRCodeGenerate.show();
  smartglassList.show();
  micBtn.removeClass("mute").removeClass("unmute").addClass("unmute");
  audioBtn
    .removeClass("enable_sound")
    .removeClass("disable_sound")
    .addClass("disable_sound");
  camBtn
    .removeClass("enable_video")
    .removeClass("disable_video")
    .addClass("disable_video");
  var save = msgHistoryDivToSave.detach();
  msgHistory.empty().append(save);
  messageTextBox[0].value = "";
}

function startCallGui() {
  remove_fullscreen();
  closeCanvasBtn.click();
  messageTextBox.prop("disabled", true);
  sendMessageTextBox.prop("disabled", true);
  sendLinkTextBox.prop("disabled", true);
  remote_video_enabled = false;
  remoteVideo.muted = false;
  micBtn.removeClass("mute").removeClass("unmute").addClass("unmute");
  audioBtn
    .removeClass("enable_sound")
    .removeClass("disable_sound")
    .addClass("disable_sound");
  camBtn
    .removeClass("enable_video")
    .removeClass("disable_video")
    .addClass("disable_video");

  smartglassList.hide();

  callPage.show();
  buttorQRCodeGenerate.hide();
  var save = msgHistoryDivToSave.detach();
  msgHistory.empty().append(save);
  messageTextBox[0].value = "";
}

togglePipButton.addEventListener("click", async function (event) {
  togglePipButton.disabled = true; //disable toggle button while the event occurs
  try {
    // If there is no element in Picture-in-Picture yet, request for it
    if (remoteVideo !== document.pictureInPictureElement) {
      await remoteVideo.requestPictureInPicture();
    }
    // If Picture-in-Picture already exists, exit the mode
    else {
      await document.exitPictureInPicture();
    }
  } catch (error) {
    console.log("${error}");
  } finally {
    togglePipButton.disabled = false; //enable toggle button after the event
  }
});

remoteVideo.addEventListener("enterpictureinpicture", function (event) {
  console.log("Entered PiP");
  pipWindow = event.pictureInPictureWindow;
  console.log(
    `Window size -  \n Width: ${pipWindow.width} \n Height: ${pipWindow.height}`
  ); // get the width and height of PiP window
});

remoteVideo.addEventListener("leavepictureinpicture", function (event) {
  console.log("Left PiP");
  togglePipButton.disabled = false;
});

if ("pictureInPictureEnabled" in document) {
  showPipButton();

  // loadedmetadata event occurs when meta data for the specified audio/video has been loaded.Meta data might consists of: duration, dimensions etc.
  remoteVideo.addEventListener("loadedmetadata", showPipButton);

  // emptied event is fired when the media has become empty, e.g. media has already been loaded or partially loaded.
  remoteVideo.addEventListener("emptied", showPipButton);
} else {
  console.log("The Picture-in-Picture Web API is not available.");
  togglePipButton.hidden = true;
}

// Enable/disable toggle button depending on whether PiP availability.
function showPipButton() {
  togglePipButton.disabled =
    !document.pictureInPictureEnabled || remoteVideo.disablePictureInPicture;
}
