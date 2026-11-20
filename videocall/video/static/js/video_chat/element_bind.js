var callBtn = $('.start_call_btn');
var closeCallBtn = $('.close_call_btn');
var acceptBtn = $('.accept_call_btn');
var ignoreBtn = $('.ignore_call_btn');

var hangUpBtn = $('#hangUpBtn');
var controls = document.querySelector('.controls');
var fullBtn = $('#fullscreen');
var micBtn = $("#mic");
var audioBtn = $("#audio");
var camBtn = $("#cam")

var timerWrapper = document.querySelector('.timer');
var timer = document.querySelector('.timer span');
var timerBar = document.querySelector('.timer div');
var remoteVideo = document.querySelector('#remoteVideo');


var msgHistoryDivToSave = $('#history div')
var msgHistory = $('#history');
var messageTextBox = $('#msgTxt');
var sendMessageTextBox = $('#send');
var sendLinkTextBox = $('#right');

var screenshotBtn = $('#screenshot');
var closeCanvasBtn = $('#close-canvas');
var eraseCanvasBtn = $('#erase-canvas');
var sendCanvasBtn = $('#send-canvas');

var canvas = document.getElementById("canvas");
var canvasDiv = $("#canvasDiv");
var callPage = $("#callPage");
var smartglassList = $("#smartglassList");
var buttorQRCodeGenerate = $("#buttorQRCodeGenerate");


var calling_sound = $('#calling_sound')[0];
var called_sound = $('#called_sound')[0];

var togglePipButton = document.getElementById('picture-in-picture');