"use strict";

function start_ws_system_connection() {
  var conn = null;
  var states = Object.freeze({
    NEW: 1,
    ALONE: 2,
    REGISTERED: 3,
    CLOSED: 4,
    ERROR: 5,
  });
  var messages = Object.freeze({
    REFUSE_CALL: "refuse_call",
    ACCEPT_CALL: "accept_call",
    CLOSE_CALL: "close_call",
    CALLED: "called",
    CONTACT: "contact",
    CONTACTS: "contacts",
    CONTACT_REFRESH: "contact_refresh",
    STATUS: "status",
    ACCEPTED_CALL: "accepted_call",
  });
  var state;
  var queue = [];
  conn = new WebSocket(ws_system_url + "?Token=" + token);
  state = states.NEW;
  reset_call();

  conn.onopen = function (event) {
    console.log("WebSocket whith system is open now.");
    console.log("connected");
    setReloadAttempts(0);
    state = states.ALONE;
    send_ping();
  };

  // Se il WebSocket di sistema cade la pagina non riceve piu' le chiamate:
  // si ricarica da sola (prima aspettava il clic su OK di un alert).
  // Durante una chiamata aspetta che finisca, per non interromperla.
  // L'attesa raddoppia a ogni tentativo fallito (3s, 6s, 12s... fino a 60s),
  // cosi' con il server giu' la pagina non si ricarica a raffica.
  var RELOAD_KEY = "videocall_reload_attempts";
  var reloadScheduled = false;
  function getReloadAttempts() {
    try {
      return parseInt(sessionStorage.getItem(RELOAD_KEY) || "0", 10) || 0;
    } catch (e) {
      return 0;
    }
  }
  function setReloadAttempts(n) {
    try {
      sessionStorage.setItem(RELOAD_KEY, String(n));
    } catch (e) {}
  }
  function scheduleReload() {
    if (reloadScheduled) {
      return;
    }
    reloadScheduled = true;
    var attempts = getReloadAttempts();
    var delay = Math.min(60000, 3000 * Math.pow(2, attempts));
    console.log(
      "Connessione di sistema persa: ricarico la pagina tra " +
        delay / 1000 +
        " s."
    );
    setTimeout(function tryReload() {
      if (contactInCall == null) {
        setReloadAttempts(attempts + 1);
        window.location.reload();
      } else {
        setTimeout(tryReload, 2000);
      }
    }, delay);
  }

  conn.onclose = function (e) {
    console.log("Disconnected!", e.code, e.reason);
    state = states.CLOSED;
    scheduleReload();
  };

  //when we got a message from a signaling server
  conn.onmessage = function (msg) {
    console.log("Got message", msg.data);
    var data = JSON.parse(msg.data);

    if (data.hasOwnProperty("cmd")) {
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
    } else if (data.hasOwnProperty("type")) {
      switch (data.type) {
        case messages.REFUSE_CALL:
          refuseCallMessageHandler(data);
          break;
        //when somebody wants to call us
        case messages.ACCEPT_CALL:
          acceptCallMessageHandler(data);
          break;
        case messages.CLOSE_CALL:
          closeCallMessageHandler(data);
          break;
        //when a remote peer sends an ice candidate to us
        case messages.CALLED:
          calledMessageHandler(data);
          break;
        case messages.CONTACT:
          contactMessageHandler(data);
          break;
        case messages.CONTACTS:
          contactsMessageHandler(data);
          break;
        case messages.CONTACT_REFRESH:
          contactRefreshMessageHandler(data);
          break;
        case messages.STATUS:
          statusMessageHandler(data);
          break;
        case messages.ACCEPTED_CALL:
          acceptedCallMessageHandler(data);
          break;
        default:
          break;
      }
    }
  };

  // Un errore del WebSocket e' sempre seguito da onclose, che ricarica la pagina.
  conn.onerror = function (err) {
    console.log("Got error", err);
  };

  this.sendStatus = function () {
    status();
  };

  //alias for sending JSON encoded messages
  function send(message) {
    if (state == states.REGISTERED) {
      message = {
        //cmd:"send",
        user_id: user_id,
        msg: JSON.stringify(message),
      };
      conn.send(JSON.stringify(message));
    } else if (state == states.NEW || state == states.ALONE) {
      queue.push(message);
    }
  }

  function send_pong() {
    var message = {
      cmd: "pong",
    };
    conn.send(JSON.stringify(message));
    not_alone_anymore();
    contactsList();
  }

  function send_ping() {
    var message = {
      cmd: "ping",
    };
    conn.send(JSON.stringify(message));
  }

  function pong_received() {
    not_alone_anymore();
    contactsList();
  }

  function not_alone_anymore() {
    state = states.REGISTERED;
    while (queue.length > 0) {
      send(queue.shift());
    }
  }

  function statusMessageHandler(json) {
    status();
  }

  function refuseCallMessageHandler(json) {
    var json_msg = json.msg;
    var contact_from = json_msg.from;
    var contact_to = json_msg.to;
    if (contactToCall != null) {
      if (contact_from.id == contactToCall.id) {
        contactInCall = null;
        contactToCall = null;
        contactCalled = null;
        busy = false;
        status();
        calling_sound.pause();
        isCalledContact(contact_from, false);
      }
    }
  }

  function acceptCallMessageHandler(json) {
    var json_msg = json.msg;
    var contact_from = json_msg.from;
    var contact_to = json_msg.to;
    if (contact_from.id == contactToCall.id) {
      ws_room_url = json_msg.ws_room_url;
      ws_room_url = ws_base_url + ws_room_url;
      startCall();
      initiator = true;
      contactInCall = contactToCall;
      contactToCall = null;
      contactCalled = null;
      busy = true;
      status();
      callPage.show();

      startRecording();
      smartglassList.hide();
      toggleSound(false, false);
      startCallGui();
    }
  }

  function acceptedCallMessageHandler(json) {
    var json_msg = json.msg;
    var contact_from = json_msg.from;
    var contact_to = json_msg.to;
    ws_room_url = json_msg.ws_room_url;
    ws_room_url = ws_base_url + ws_room_url;
    startCall();
    initiator = false;
    contactInCall = contactCalled;
    contactToCall = null;
    contactCalled = null;
    busy = true;
    status();
    callPage.show();
    //console.log('cazzo in fica');
    smartglassList.hide();
    toggleSound(false, false);
    startCallGui();
  }

  function closeCallMessageHandler(json) {
    var json_msg = json.msg;
    var contact_from = json_msg.from;
    var contact_to = json_msg.from;
    if (contactInCall && contact_from.id == contactInCall.id) {
      contactInCall = null;
      contactToCall = null;
      busy = false;
      status();
      callPage.hide();
      smartglassList.show();
      if (ws_webrtc != null) {
        ws_webrtc.handleLeave();
      }

      toggleSound(false, false);
    } else {
    }
    isCalledContact(contact_from, false);
    toggleSound(false, false);
    stopRecording();
  }

  function contactRefreshMessageHandler(json) {
    var json_msg = json.msg;
    if (!json_msg.online) {
      if (contactToCall != null && json_msg.id == contactToCall.id) {
        refreshContact(json_msg);
        contactToCall = null;
      }
      if (contactInCall != null && json_msg.id == contactInCall.id) {
        if (ws_webrtc != null) {
          ws_webrtc.handleLeave();
        }
        refreshContact(json_msg);
      }
      if (contactCalled != null && json_msg.id == contactCalled.id) {
        toggleSound(false, false);
        contactCalled = null;
        refreshContact(json_msg);
      }
    }

    refreshContact(json_msg);
  }

  function calledMessageHandler(json) {
    var json_msg = json.msg;
    var contact_from = json_msg.from;
    var contact_to = json_msg.to;

    if (busy) {
      this.ignoreCall(contact_from);
    } else {
      status();
      callPage.hide();
      smartglassList.show();
      isCallingContact(contact_from, true);
      toggleSound(false, true);
    }
  }

  function contactMessageHandler(json) {
    if ("error" in json) {
      var error = json.error;
    } else {
      error = null;
    }
    json = json.msg;
    ws_room_url = null;
    var contact = null;
    if (error == null || !error) {
      ws_room_url = ws_base_url + json.ws_room_url;
      contactToCall = json;
      busy = true;
      status();
      isCalledContact(json, true);
      toggleSound(true, false);
    } else {
      alert(json.error);
    }
  }

  function contactsMessageHandler(json) {
    contacts_list = json.msg;
    displayContacts();
  }

  function contactsList() {
    var message = {
      type: messages.CONTACTS,
    };
    send(message);
  }

  function status() {
    var message = {
      type: messages.STATUS,
      msg: { busy: busy },
    };
    send(message);
  }

  this.contactInfo = function (contact) {
    var message = {
      type: messages.CONTACT,
      msg: {
        id: contact.id,
        busy: busy,
      },
    };
    send(message);
  };

  function contactRefresh(contact) {
    var message = {
      type: messages.CONTACT_REFRESH,
      msg: {
        id: contact.id,
        busy: busy,
      },
    };
    send(message);
  }

  this.closeCall = function (contact) {
    var message = {
      type: messages.CLOSE_CALL,
      msg: {
        id: contact.id,
        busy: busy,
      },
    };
    send(message);
    busy = false;
  };

  this.callAccept = function (contact) {
    var message = {
      type: messages.ACCEPT_CALL,
      msg: {
        id: contact.id,
        busy: busy,
      },
    };
    send(message);
  };

  this.ignoreCall = function (contact) {
    toggleSound(false, false);
  };

  function CallRefuse(contact) {
    var message = {
      type: messages.REFUSE_CALL,
      msg: {
        id: contact.id,
        busy: busy,
      },
    };
    send(message);
  }
}
