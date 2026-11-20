$('.delete').click(function () {
    var button = $(this),
        tr = button.closest('tr');

    var id = tr.attr("data-id");
    console.log('clicked button with id', id);

    var data = { id: id,
                 csrfmiddlewaretoken : csrf_token,
     };

    // ask confirmation
    if (confirm('Are you sure you want to delete this entry?')) {
        console.log('sending request');
        // delete record only once user has confirmed
        $.post(delete_AJAX, data, function (res) {
            console.log('received response', res);
            // we want to delete the table row only we received a response back saying that it worked
            console.log('response status', res.success);
            if (res.success) {
                console.log('deleting TR');
                tr.remove();
            }
        }, 'json');
    }
});


$('.send_mail').click(function () {
    var button = $(this),
        tr = button.closest('tr');

    var id = tr.attr("data-id");
    console.log('clicked button with id', id);

    var data = { id: id,
                 csrfmiddlewaretoken : csrf_token,
     };

    // ask confirmation
    if (confirm('Sicuro di voler mandare il link via mail?')) {
        $.post(send_mail_AJAX, data, function (res) {
            console.log('received response', res);
            // we want to delete the table row only we received a response back saying that it worked
            console.log('response status', res.success);
            if (res.success) {
                button.disable();
            }
        }, 'json');
    }
});