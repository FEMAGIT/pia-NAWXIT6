'use strict';


function start_ws_webrtc_connection() {
    var conn = null
    var states = Object.freeze({"NEW": 1, "ALONE": 2, "REGISTERED": 3, "CLOSED": 4, "ERROR": 5})
    var msgType = Object.freeze({
        "TEXT_SIGNAL": "text-signal",
        "IMAGE_SIGNAL": "image-signal",
        "IMAGE64_SIGNAL": "base64-content-signal",
        "IMAGE64_BEGIN_SIGNAL": "base64-begin-signal",
        "IMAGE64_END_SIGNAL": "base64-end-signal",
        "SYSTEM_SIGNAL": "system",
        "VIDEO": "video",
        "VIDEO_STATUS": "video_status"
    })
    var state;
    var queue = [];
    var conn
    var sendChannel;
    state = states.NEW;
    var MAX_LENGTH = 60000;


    function WebsoketInizialization() {
        conn = new WebSocket(ws_room_url + "?token=" + token);
        console.log("QUI344444444444444444444444444444444444444444444444444444444444444444444");
        console.log(conn);
        conn.onopen = function (event) {
            console.log("WebSocket of webrtc is open now.");
            console.log("connected");
            state = states.ALONE;
            send_ping();
        };

        conn.onclose = function (e) {
            console.log('Disconnected!');
            if (state != states.CLOSED) {
                this.handleLeave;
            }
        };


        //when we got a message from a signaling server
        conn.onmessage = function (msg) {
            console.log("Got message", msg.data);
            var data = JSON.parse(msg.data);
            if (user_id != data.user_id) {
                if (data.hasOwnProperty('cmd')) {

                    switch (data.cmd) {
                        case "ping":
                            send_pong();
                            break;
                        //when somebody wants to call us
                        case "pong":
                            pong_received();
                            break;
                        default:
                            break;
                    }

                } else if (data.hasOwnProperty('msg')) {
                    if (data.msg !== "") {
                        data = JSON.parse(data.msg);
                        if (data.hasOwnProperty('type')) {
                            switch (data.type) {
                                case "offer":
                                    handleOffer(data);
                                    break;
                                case "answer":
                                    handleAnswer(data);
                                    break;
                                //when a remote peer sends an ice candidate to us
                                case "candidate":
                                    handleCandidate(data);
                                    break;
                                case "bye":
                                    this.handleLeave;
                                    break;
                                default:
                                    break;
                            }
                        }
                    }
                }
            }
        };

        conn.onerror = function (err) {
            console.log("Got error", err);
            if (!alert('Errore,  assicurarsi di essere connessi ad internet e premere ok')) {
                window.location.reload();
            }
        };

    };
    //******
    //UI selectors block
    //******

    var yourConn;
    var stream;

    this.remote_video = function (video) {
        this.sendMessageVideo(video)

    }

    this.mute = function () {
        var track = stream && stream.getAudioTracks()[0];
        if (!track) return null;
        if (track.enabled) {
            track.enabled = false;
            return !false;

        } else {
            track.enabled = true;
            return !true;
        }
    }


    this.sendMessageVideo = function (message) {
        sendMessageJson(message, msgType.VIDEO);
    }


    this.sendImageBase64 = function (message) {

        var messages = split(message, MAX_LENGTH)

        sendMessageImageBase64Begin()

        var i;
        for (i = 0; i < messages.length; i++) {
            sendMessageImageBase64(messages[i]);

        }

        sendMessageImageBase64End();

    }


    function sendMessageImageBase64(message) {
        sendMessageJson(message, msgType.IMAGE64_SIGNAL);
    }

    function sendMessageImageBase64Begin() {
        var message = '';
        sendMessageJson(message, msgType.IMAGE64_BEGIN_SIGNAL);
    }

    function sendMessageImageBase64End() {
        var message = '';
        sendMessageJson(message, msgType.IMAGE64_END_SIGNAL);
    }


    this.sendMessageText = function (message) {
        sendMessageJson(message, msgType.TEXT_SIGNAL);
    }
    this.sendMessageLink = function (message) {
        sendMessageJson(message, msgType.IMAGE_SIGNAL);
    }


    function sendMessageJson(message, msgType) {
        let obj = {
            "type": msgType,
            "msg": message
        }
        sendMessage(JSON.stringify(obj));
    }


    function sendMessage(message) {
        sendChannel.send(message);


    }


    //alias for sending JSON encoded messages
    function send(message) {
        if (state == states.REGISTERED) {
            message = {
                user_id: user_id,
                msg: JSON.stringify(message)
            }
            conn.send(JSON.stringify(message));
        } else if (state == states.NEW || state == states.ALONE) {
            queue.push(message);
        }

    };


    function onStreamReady(myStream) {
        stream = myStream;

        var configuration =
            {
                "iceServers": ice_servers

            };

        yourConn = new RTCPeerConnection(configuration);


        const dataChannelOptions = {
            "ordered": true,
            "maxPacketLifeTime": 3000,
            "protocol": "json",
            "negotiated": false,
            "id": 1,

        };
        if (initiator) {
            sendChannel = yourConn.createDataChannel("messageChannel", dataChannelOptions);
            sendChannel.onopen = handleSendChannelStatusChange;
            sendChannel.onclose = handleSendChannelStatusChange;
            sendChannel.onmessage = handleReceiveMessage;

        } else {
            yourConn.ondatachannel = receiveChannelCallback;
        }


        // setup stream listening
        yourConn.addStream(stream);

        //when a remote user adds stream to the peer connection, we display it
        yourConn.ontrack = function (e) {
            remoteVideo.srcObject = e.streams[0];

        };

        yourConn.oniceconnectionstatechange = function (e) {

            if (yourConn.iceConnectionState === "failed" ||
                yourConn.iceConnectionState === "disconnected" ||
                yourConn.iceConnectionState === "closed") {
                // Handle the failure
                this.handleLeave;
            }
        };


        // Setup ice handling
        yourConn.onicecandidate = function (event) {
            if (event.candidate) {
                send({
                    type: "candidate",
                    label: event.candidate.sdpMLineIndex,
                    id: event.candidate.sdpMid,
                    candidate: event.candidate.candidate
                });
            }
        };
        WebsoketInizialization();
        if (initiator) {
            startCallInternal();
        }


    }


    function handleSendChannelStatusChange(event) {
        if (sendChannel) {
            var state = sendChannel.readyState;

            if (state === "open") {

                messageTextBox.prop("disabled", false);
                sendMessageTextBox.prop("disabled", false);
                sendLinkTextBox.prop("disabled", false);
                //messageTextBox.focus();
                //sendButton.disabled = false;
                messageTextBox[0].value = "";

            } else {
                messageTextBox[0].value = "";
                messageTextBox.prop("disabled", true);
                sendMessageTextBox.prop("disabled", true);
                sendLinkTextBox.prop("disabled", true);
            }
        }
    }

    function handleReceiveMessage(event) {

        var data = JSON.parse(event.data);

        switch (data.type) {
            case msgType.VIDEO_STATUS:
                remote_video_enabled = data.msg;
                disable_cam_gui(remote_video_enabled)
                break;
            default:
                break;
        }


    }


    function receiveChannelCallback(event) {
        sendChannel = event.channel;
        sendChannel.onmessage = handleReceiveMessage;
        sendChannel.onopen = handleSendChannelStatusChange;
        sendChannel.onclose = handleSendChannelStatusChange;
    }


    function setPeerConnection() {
        //**********************
        //Starting a peer connection
        //**********************
        //getting local video stream
        navigator.mediaDevices.getUserMedia({video: false, audio: true}).then(function (myStream) {
            onStreamReady(myStream)
        }).catch(function (error) {
            console.log(error);
            if (!alert("Errore durante l'accesso alle fotocamera e al microfono, la pagina verrà ricaricata")) {
                window.location.reload();
            }
        });


    };

    //initiating a call
    function startCallInternal() {

        // create an offer
        var offerOptions = {offerToReceiveVideo: true, offerToReceiveAudio: true};
        yourConn.createOffer(function (offer) {
            send(
                offer
            );

            yourConn.setLocalDescription(offer);
        }, function (error) {
            if (!alert("Errore durante la creazione dell'offerta, la pagina verrà ricaricata")) {
                window.location.reload();
            }
        }, offerOptions);


    };

    //when somebody sends us an offer
    function handleOffer(offer) {

        yourConn.setRemoteDescription(new RTCSessionDescription(offer));

        //create an answer to an offer
        yourConn.createAnswer(function (answer) {
            yourConn.setLocalDescription(answer);

            send(
                answer
            );

        }, function (error) {
            if (!alert("Errore durante la creazione della risposta, la pagina verrà ricaricata")) {
                window.location.reload();
            }
        });
    };

    //when we got an answer from a remote user
    function handleAnswer(answer) {

        yourConn.setRemoteDescription(new RTCSessionDescription(answer));
    };

    //when we got an ice candidate from a remote user
    function handleCandidate(candidate) {

        //yourConn.addIceCandidate(new RTCIceCandidate(candidate));
        yourConn.addIceCandidate(new RTCIceCandidate({
            candidate: candidate.candidate,
            sdpMLineIndex: candidate.label,
            sdpMid: candidate.id
        }));
    };

    this.handleLeave = function () {
        contactInCall = null;
        remoteVideo.src = null;

        if (yourConn != null) {
            yourConn.close();
            yourConn.onicecandidate = null;
            yourConn.onaddstream = null;
        }
        send({type: "bye"});
        state = states.CLOSED;
        if (conn != null) {
            conn.close();
        }
        let tracks = stream.getTracks();
        tracks.forEach(function (track) {
            track.stop();
        });
        //location.reload();
        reset_call();

    };


    function send_pong() {
        var message = {
            cmd: "pong",
            user_id: user_id,
        };
        conn.send(JSON.stringify(message));
        not_alone_anymore();
    };

    function send_ping() {
        var message = {
            cmd: "ping",
            user_id: user_id,
        };
        conn.send(JSON.stringify(message));
    };


    function pong_received() {
        not_alone_anymore();

    };


    function not_alone_anymore() {
        state = states.REGISTERED;
        while (queue.length > 0) {
            send(queue.shift())
        }
    }

    setPeerConnection();

};


function split(str, size) {
    if (str == null) return [];
    str = String(str);
    size = ~~size;
    return size > 0 ? str.match(new RegExp('.{1,' + size + '}', 'g')) : [str];
}