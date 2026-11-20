'use strict';

function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function (m, key, value) {
        vars[key] = value;
    });
    return vars;
}


function getUrlParam(parameter, defaultvalue) {
    var urlparameter = defaultvalue;
    if (window.location.href.indexOf(parameter) > -1) {
        urlparameter = getUrlVars()[parameter];
    }
    return urlparameter;
}

var ws_base_url = null;
var ws_system_url = null;
var ws_room_url = null;
var ice_servers = null;
var user_id = null;
var username = null;
var first_name = null;
var last_name = null;
var busy = false;
var contacts_list = null;
var contactToCall = null;
var contactCalled = null;
var contactInCall = null;
var session_data_url = location.origin + '/api/session/';
var user_data_url = location.origin + '/api/user_info/';
var token = token_temp;
var ws_system = null;
var ws_webrtc = null;
var initiator = false;
var remote_video_enabled = false;


var calling_sound = new Audio(location.origin + '/static/sound/' + 'calling_sound.wav');
calling_sound.loop = true;
var called_sound = new Audio(location.origin + '/static/sound/' + 'called_sound.wav');
called_sound.loop = true;


$(document).ready(function () {
    callPage.hide();
    smartglassList.show();
});


function session_data_ready(data) {
    ws_base_url = data.ws_base_url;
    ws_system_url = ws_base_url + data.ws_system_url;
    ice_servers = data.ice_servers;
    busy = false;

    ws_system = new start_ws_system_connection();

}


function user_data_ready(data) {
    user_id = data.id;
    username = data.username;
    first_name = data.first_name;
    last_name = data.last_name;

    const Http = new XMLHttpRequest();
    Http.onreadystatechange = (e) => {
        if (Http.readyState == 4 && Http.status == 200) {
            var data = JSON.parse(Http.responseText);
            session_data_ready(data);
        }
    }

    Http.open("GET", session_data_url, true);
    Http.setRequestHeader("AUTHORIZATION", 'Token ' + token)
    Http.send();

}


const Http = new XMLHttpRequest();
Http.onreadystatechange = (e) => {
    if (Http.readyState == 4 && Http.status == 200) {
        var data = JSON.parse(Http.responseText);
        user_data_ready(data);
    }
}

Http.open("GET", user_data_url, true);
Http.setRequestHeader("AUTHORIZATION", 'Token ' + token)
Http.send();

function startCall() {
    ws_webrtc = new start_ws_webrtc_connection()


}

function toggleSound(calling, called) {

    if (smartglassList.is(':visible')) {
        if (calling) {
            calling_sound.play();
            called_sound.pause();

        } else if (called) {
            calling_sound.pause();
            called_sound.play();
        } else {
            calling_sound.pause();
            called_sound.pause();
        }

    } else {
        calling_sound.pause();
        called_sound.pause();
    }

}





