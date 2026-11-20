
var ctx;
var mousePressed = false;
var touchPressed =   false;
var lastX, lastY;

screenshotBtn.click(function(e) {
    var ctx = canvas[0].getContext('2d');
    ctx.drawImage(remoteVideo, 0, 0, canvas[0].width, canvas[0].height);
    var dataURI = canvas[0].toDataURL('image/jpeg');
    canvasDiv.show();
    });


   screenshotBtn.click(function(e) {
    ctx = canvas[0].getContext('2d');
    ctx.drawImage(remoteVideo, 0, 0, canvas[0].width, canvas[0].height);
     drawingSurfaceImageData = ctx.getImageData(0, 0,canvas[0].width,canvas[0].height);
    InitThis()
    canvasDiv.show();

    });


closeCanvasBtn.click(function(e) {

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height)
    canvasDiv.hide();


    });

sendCanvasBtn.click(function(e) {
    var dataURI = canvas[0].toDataURL('image/png');
        console.log(dataURI)
        ws_webrtc.sendImageBase64(dataURI)



    var msg = document.createElement('img');
    msg.setAttribute("src", dataURI);
	msg.setAttribute("width", "100%");
    msg.className = 'screenshot_message';

	var link = document.createElement('a');
	link.href = dataURI;  // use realtive url
	link.download = 'MyImage.jpeg';
	link.appendChild(msg);
    msgHistory.appendChild(link);
    msg.scrollIntoView();
	image = '';


    });


eraseCanvasBtn.click(function(e) {
   clearArea();
    });





function InitThis() {

    canvas.mousedown(function (e) {
        mousePressed = true;
        Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, false);
    });

    canvas.mousemove(function (e) {
        if (mousePressed) {
            Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, true);
        }
    });

    canvas.mouseup(function (e) {
        mousePressed = false;
    });
	    canvas.mouseleave(function (e) {
        mousePressed = false;
    });





        canvas.touchstart(function (e) {
        touchPressed = true;

        Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, false);
    });

    canvas.touchmove(function (e) {
        if (touchPressed) {
            Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, true);
        }
    });

    canvas.touchend(function (e) {
        touchPressed = false;
    });
	    canvas.touchcancel(function (e) {
        touchPressed = false;
    });



    document.body.addEventListener("touchstart", function (e) {
    if (e.target == canvas[0]) {
        e.preventDefault();
    }
    }, false);
    document.body.addEventListener("touchend", function (e) {
    if (e.target == canvas[0]) {
        e.preventDefault();
    }
    }, false);
    document.body.addEventListener("touchmove", function (e) {
    if (e.target == canvas[0]) {
        e.preventDefault();
    }
    }, false);

}

function Draw(x, y, isDown) {
    if (isDown) {
        ctx.beginPath();
        ctx.strokeStyle = "red";
        ctx.lineWidth = 7;
        ctx.lineJoin = "round";
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(x, y);
        ctx.closePath();
        ctx.stroke();
    }
    lastX = x; lastY = y;
}

function clearArea() {
    // Use the identity matrix while clearing the canvas
     ctx.putImageData(drawingSurfaceImageData, 0, 0);

}