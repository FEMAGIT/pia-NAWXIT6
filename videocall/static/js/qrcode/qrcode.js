    function download_svg()
    {


img = new Image(),
        serializer = new XMLSerializer(),
        svgStr = serializer.serializeToString(document.querySelector('svg'));

    img.src = 'data:image/svg+xml;base64,'+window.btoa(svgStr);

    // You could also use the actual string without base64 encoding it:
    //img.src = "data:image/svg+xml;utf8," + svgStr;

    var canvas = document.createElement("canvas");

    var w=800;
    var h=800;

    canvas.width = w;
    canvas.height = h;
    canvas.getContext("2d").drawImage(img,0,0,w,h);

    var imgURL = canvas.toDataURL("image/png");


var dlLink = document.createElement('a');
    dlLink.download = "image";
    dlLink.href = imgURL;
    dlLink.dataset.downloadurl = ["image/png", dlLink.download, dlLink.href].join(':');

    document.body.appendChild(dlLink);
    dlLink.click();
    document.body.removeChild(dlLink);
    }


        function download()
    {


img = new Image(),
        serializer = new XMLSerializer(),
        svgStr = serializer.serializeToString(document.querySelector('svg'));

    img.src = 'data:image/svg+xml;base64,'+window.btoa(svgStr);

    // You could also use the actual string without base64 encoding it:
    //img.src = "data:image/svg+xml;utf8," + svgStr;

    var canvas = document.createElement("canvas");

    var w=800;
    var h=800;

    canvas.width = w;
    canvas.height = h;
    canvas.getContext("2d").drawImage(img,0,0,w,h);

    var imgURL = canvas.toDataURL("image/png");


var dlLink = document.createElement('a');
    dlLink.download = "image";
    dlLink.href = imgURL;
    dlLink.dataset.downloadurl = ["image/png", dlLink.download, dlLink.href].join(':');

    document.body.appendChild(dlLink);
    dlLink.click();
    document.body.removeChild(dlLink);
    }