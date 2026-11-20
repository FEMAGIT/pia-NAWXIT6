function sendMessageInTextBox() {
    var message = messageTextBox[0].value;

    if (!isBlank(message)) {
        ws_webrtc.sendMessageText(message)

        messageTextBox[0].value = "";
        messageTextBox[0].focus();

        var msg = document.createElement('p');
        msg.textContent = message;
        msg.className = 'mine';
        msg.classList.add("triangle-right");
        msgHistory.append(msg);
        //msg.scrollIntoView();
        msgHistory.scrollTop(msgHistory[0].scrollHeight - msgHistory[0].clientHeight);

    }


}


messageTextBox.bind("enterKey", function (e) {
    var message = messageTextBox[0].value;
    sendMessageInTextBox();

});

messageTextBox.keyup(function (e) {
    if (e.keyCode == 13) {
        e.preventDefault();
        $(this).trigger("enterKey");
        return false;
    }
});

sendMessageTextBox.click(function (e) {
    sendMessageInTextBox()
});


sendLinkTextBox.click(function (e) {
    var message = messageTextBox[0].value;
    if (!isBlank(message)) {
        ws_webrtc.sendMessageLink(message)
        messageTextBox[0].value = "";
        messageTextBox[0].focus();

        var msg = document.createElement('img');
        msg.setAttribute("src", message);
        msg.setAttribute("alt", "l'immagine non esiste");
        msg.setAttribute("width", "100%");
        msg.setAttribute("height", "fit-content");
        //msg.className = event.from.connectionId === session.connection.connectionId ? 'mine' : 'theirs';
        var link = document.createElement('a');
        link.href = message;  // use realtive url
        link.download = 'MyImage.jpeg';
        link.appendChild(msg);
        msgHistory.append(link);
        //msg.scrollIntoView();
        msgHistory.scrollTop(msgHistory[0].scrollHeight - msgHistory[0].clientHeight);
    }

});

function isBlank(str) {
    return (!str || /^\s*$/.test(str));
}

