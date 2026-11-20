var ctx;
var drawing = false;
var mousePos = { x:0, y:0 };
var lastPos = mousePos;
var drawingSurfaceImageData;


  screenshotBtn.click(function(e) {
  ctx = canvas.getContext('2d');
  resizeCanvas();
  ctx.drawImage(remoteVideo, 0, 0, canvas.width, canvas.height);
  drawingSurfaceImageData = ctx.getImageData(0, 0,canvas.width,canvas.height);
  canvasDiv[0].style.top = 100;
  canvasDiv[0].style.left = 100;
  InitThis()
  canvasDiv.show();

  });


  closeCanvasBtn.click(function(e) {

    if (typeof ctx !== 'undefined') {
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height)
      }
    canvasDiv.hide();

  });

  sendCanvasBtn.click(function(e) {
    var dataURI = canvas.toDataURL('image/png');
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
    msgHistory.append(link);
    //msg.scrollIntoView();
    msgHistory.scrollTop(msgHistory[0].scrollHeight - msgHistory[0].clientHeight);
    image = '';
  });


  function clearArea() {
    // Use the identity matrix while clearing the canvas
    ctx.putImageData(drawingSurfaceImageData, 0, 0);
  }


  eraseCanvasBtn.click(function(e) {
    clearArea();
  });


  function InitThis() {


    // Set up mouse events for drawing
    canvas.addEventListener("mousedown", function (e) {
      drawing = true;
      lastPos = getMousePos(canvas, e);
    }, false);

    canvas.addEventListener("mouseup", function (e) {
      drawing = false;
    }, false);

    canvas.addEventListener("mousemove", function (e) {
      mousePos = getMousePos(canvas, e);
      renderCanvas()
    }, false);

    // Get the position of the mouse relative to the canvas
    function getMousePos(canvas, evt) {
          var rect = canvas.getBoundingClientRect(), // abs. size of element
              scaleX = canvas.width / rect.width,    // relationship bitmap vs. element for X
              scaleY = canvas.height / rect.height;  // relationship bitmap vs. element for Y

          return {
            x: (evt.clientX - rect.left) * scaleX,   // scale mouse coordinates after they have
            y: (evt.clientY - rect.top) * scaleY     // been adjusted to be relative to element
          }
    }


    // Draw to the canvas
    function renderCanvas() {
      if (drawing) {

        ctx.beginPath();
        ctx.strokeStyle = "red";
        ctx.lineWidth = 3;
        ctx.lineJoin = "round";
        ctx.moveTo(lastPos.x, lastPos.y);
        ctx.lineTo(mousePos.x, mousePos.y);
        ctx.closePath();
        ctx.stroke();
        lastPos = mousePos;
      }
    }




    // Set up touch events for mobile, etc
    canvas.addEventListener("touchstart", function (e) {
      mousePos = getTouchPos(canvas, e);
      var touch = e.touches[0];
      var mouseEvent = new MouseEvent("mousedown", {
        clientX: touch.clientX,
        clientY: touch.clientY
      });
      canvas.dispatchEvent(mouseEvent);
    }, false);


    canvas.addEventListener("touchend", function (e) {
      var mouseEvent = new MouseEvent("mouseup", {});
      canvas.dispatchEvent(mouseEvent);
    }, false);


    canvas.addEventListener("touchmove", function (e) {
      var touch = e.touches[0];
      var mouseEvent = new MouseEvent("mousemove", {
        clientX: touch.clientX,
        clientY: touch.clientY
      });
      canvas.dispatchEvent(mouseEvent);
    }, false);


    // Get the position of a touch relative to the canvas
    function getTouchPos(canvas, evt) {
           var rect = canvas.getBoundingClientRect(), // abs. size of element
           scaleX = canvas.width / rect.width,    // relationship bitmap vs. element for X
           scaleY = canvas.height / rect.height;  // relationship bitmap vs. element for Y

          return {
            x: (evt.touches[0].clientX - rect.left) * scaleX,   // scale mouse coordinates after they have
            y: (evt.touches[0].clientY - rect.top) * scaleY     // been adjusted to be relative to element
          }
    }


    // Prevent scrolling when touching the canvas
    document.body.addEventListener("touchstart", function (e) {
      if (e.target == canvas) {
        e.preventDefault();
      }
    }, false);


    document.body.addEventListener("touchend", function (e) {
      if (e.target == canvas) {
        e.preventDefault();
      }
    }, false);

    
    document.body.addEventListener("touchmove", function (e) {
      if (e.target == canvas) {
        e.preventDefault();
      }
    }, false);

  }

  function resizeCanvas(){
        canvasDiv.width($( window ).width() * 0.40 )
        canvasDiv.height( canvasDiv.width()*remoteVideo.videoHeight/remoteVideo.videoWidth);
        canvas.style.width = canvasDiv.width() ;
        canvas.style.height = canvasDiv.height() ;
  }


  // Make the DIV element draggable:



  function dragMouseDown(e) {
    e = e || window.event;
    e.preventDefault();
    // get the mouse cursor position at startup:
    pos3 = e.clientX;
    pos4 = e.clientY;
    document.onmouseup = closeDragElement;
    // call a function whenever the cursor moves:
    document.onmousemove = elementDrag;
  }

  function elementDrag(e) {
    e = e || window.event;
    e.preventDefault();
    // calculate the new cursor position:
    pos1 = pos3 - e.clientX;
    pos2 = pos4 - e.clientY;
    pos3 = e.clientX;
    pos4 = e.clientY;
    // set the element's new position:
    canvasDiv[0].style.top = (canvasDiv[0].offsetTop - pos2);
   canvasDiv[0].style.left = (canvasDiv[0].offsetLeft - pos1);
  }

  function closeDragElement() {
    // stop moving when mouse button is released:
    document.onmouseup = null;
    document.onmousemove = null;
  }


    function dragTouchStart(e) {
    e = e || window.event;
    //e.preventDefault();
    // get the mouse cursor position at startup:
    pos3 = e.touches[0].clientX;
    pos4 = e.touches[0].clientY;
    document.getElementById("header-canvas").addEventListener("touchend", closeTouchDragElement);
    // call a function whenever the cursor moves:
    document.getElementById("header-canvas").addEventListener("touchmove", elementTouchDrag);
  }

  function elementTouchDrag(e) {
    e = e || window.event;
    //e.preventDefault();
    // calculate the new cursor position:
    pos1 = pos3 - e.touches[0].clientX;
    pos2 = pos4 - e.touches[0].clientY;
    pos3 = e.touches[0].clientX;
    pos4 = e.touches[0].clientY;
    // set the element's new position:
    canvasDiv[0].style.top = (canvasDiv[0].offsetTop - pos2);
   canvasDiv[0].style.left = (canvasDiv[0].offsetLeft - pos1);
  }

  function closeTouchDragElement() {
    // stop moving when mouse button is released:
    document.getElementById("header-canvas").removeEventListener("touchend", closeTouchDragElement);
    document.getElementById("header-canvas").removeEventListener("touchmove", elementTouchDrag);
  }


document.getElementById("header-canvas").onmousedown = dragMouseDown;
document.getElementById("header-canvas").addEventListener("touchstart", dragTouchStart);








  const element = document.querySelector(".resizable");
  const resizers = document.querySelectorAll(".resizable" + ' .resizer')
  const minimum_size = 20;
  let original_width = 0;
  let original_height = 0;
  let original_x = 0;
  let original_y = 0;
  let original_mouse_x = 0;
  let original_mouse_y = 0;
  for (let i = 0;i < resizers.length; i++) {
    const currentResizer = resizers[i];
    currentResizer.addEventListener('mousedown', function(e) {
      e.preventDefault()
      original_width = parseFloat(getComputedStyle(element, null).getPropertyValue('width').replace('px', ''));
      original_height = parseFloat(getComputedStyle(element, null).getPropertyValue('height').replace('px', ''));
      original_x = element.getBoundingClientRect().left;
      original_y = element.getBoundingClientRect().top;
      original_mouse_x = e.pageX;
      original_mouse_y = e.pageY;
      window.addEventListener('mousemove', resize)
      window.addEventListener('mouseup', stopResize)


    })


      currentResizer.addEventListener('touchstart', function(e) {
      e.preventDefault()
      original_width = parseFloat(getComputedStyle(element, null).getPropertyValue('width').replace('px', ''));
      original_height = parseFloat(getComputedStyle(element, null).getPropertyValue('height').replace('px', ''));
      original_x = element.getBoundingClientRect().left;
      original_y = element.getBoundingClientRect().top;
      original_mouse_x = e.touches[0].pageX;
      original_mouse_y = e.touches[0].pageY;
      currentResizer.addEventListener('touchmove', resizeTouch)
      currentResizer.addEventListener('touchend', stopTouchResize)


    })




    function resize(e) {
      if (currentResizer.classList.contains('bottom-right')) {
        const width = original_width + (e.pageX - original_mouse_x);
        const height = original_height + (e.pageY - original_mouse_y)
        if (width > minimum_size) {
          element.style.width = width + 'px'
        }
        if (height > minimum_size) {
          element.style.height = height + 'px'
        }
      }
      else if (currentResizer.classList.contains('bottom-left')) {
        const height = original_height + (e.pageY - original_mouse_y)
        const width = original_width - (e.pageX - original_mouse_x)
        if (height > minimum_size) {
          element.style.height = height + 'px'
        }
        if (width > minimum_size) {
          element.style.width = width + 'px'
          element.style.left = original_x + (e.pageX - original_mouse_x) + 'px'
        }
      }
      else if (currentResizer.classList.contains('top-right')) {
        const width = original_width + (e.pageX - original_mouse_x)
        const height = original_height - (e.pageY - original_mouse_y)
        if (width > minimum_size) {
          element.style.width = width + 'px'
        }
        if (height > minimum_size) {
          element.style.height = height + 'px'
          element.style.top = original_y + (e.pageY - original_mouse_y) + 'px'
        }
      }
      else {
        const width = original_width - (e.pageX - original_mouse_x)
        const height = original_height - (e.pageY - original_mouse_y)
        if (width > minimum_size) {
          element.style.width = width + 'px'
          element.style.left = original_x + (e.pageX - original_mouse_x) + 'px'
        }
        if (height > minimum_size) {
          element.style.height = height + 'px'
          element.style.top = original_y + (e.pageY - original_mouse_y) + 'px'
        }
      }


        canvas.style.width = canvasDiv.width() ;
        canvas.style.height = canvasDiv.height() ;
    }



    function stopResize() {
      window.removeEventListener('mousemove', resize)
    }


        function resizeTouch(e) {
      if (currentResizer.classList.contains('bottom-right')) {
        const width = original_width + (e.touches[0].pageX - original_mouse_x);
        const height = original_height + (e.touches[0].pageY - original_mouse_y)
        if (width > minimum_size) {
          element.style.width = width + 'px'
        }
        if (height > minimum_size) {
          element.style.height = height + 'px'
        }
      }
      else if (currentResizer.classList.contains('bottom-left')) {
        const height = original_height + (e.touches[0].pageY - original_mouse_y)
        const width = original_width - (e.touches[0].pageX - original_mouse_x)
        if (height > minimum_size) {
          element.style.height = height + 'px'
        }
        if (width > minimum_size) {
          element.style.width = width + 'px'
          element.style.left = original_x + (e.touches[0].pageX - original_mouse_x) + 'px'
        }
      }
      else if (currentResizer.classList.contains('top-right')) {
        const width = original_width + (e.touches[0].pageX - original_mouse_x)
        const height = original_height - (e.touches[0].pageY - original_mouse_y)
        if (width > minimum_size) {
          element.style.width = width + 'px'
        }
        if (height > minimum_size) {
          element.style.height = height + 'px'
          element.style.top = original_y + (e.touches[0].pageY - original_mouse_y) + 'px'
        }
      }
      else {
        const width = original_width - (e.touches[0].pageX - original_mouse_x)
        const height = original_height - (e.touches[0].pageY - original_mouse_y)
        if (width > minimum_size) {
          element.style.width = width + 'px'
          element.style.left = original_x + (e.touches[0].pageX - original_mouse_x) + 'px'
        }
        if (height > minimum_size) {
          element.style.height = height + 'px'
          element.style.top = original_y + (e.touches[0].pageY - original_mouse_y) + 'px'
        }
      }


        canvas.style.width = canvasDiv.width() ;
        canvas.style.height = canvasDiv.height() ;
    }



    function stopTouchResize() {
      currentResizer.removeEventListener('touchmove', resize)
    }
  }

