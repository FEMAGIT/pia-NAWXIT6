function onClickCall() {
    return function () {
        var button = $(this),
            tr = button.closest('tr');

        var id = tr.attr("data-id");

        contactToCall = contacts_list.find(x => x.id == id
        )
        ;
        if (contactToCall) {
            if (!contactToCall.calling) {
                initiator = true;
                ws_system.contactInfo(contactToCall)
            } else {
                acceptBtn.click();

            }
        }

    };
}


function onClickClose() {
    return function () {
        var button = $(this),
            tr = button.closest('tr');

        var id = tr.attr("data-id");
        contactToCall = null
        var contact = contacts_list.find(x => x.id == id
            )
        ;
        if (contact) {
            initiator = true;
            isCalledContact(contact, false)
            ws_system.closeCall(contact)


        }

    };
}



function onClickAccept() {
    return function () {
        var button = $(this),
            tr = button.closest('tr');

        var id = tr.attr("data-id");

        contactCalled = contacts_list.find(x => x.id == id
        )
        ;
        if (contactCalled) {
            initiator = false;
            ws_system.callAccept(contactCalled)


        }

    };
}



function onClickIgnore() {
    return function () {
        var button = $(this),
            tr = button.closest('tr');

        var id = tr.attr("data-id");

        var temp_contact = contacts_list.find(x => x.id == id
            )
        ;
        if (temp_contact) {
            ws_system.ignoreCall(temp_contact)
        }

    };
}


closeCallBtn.click(onClickClose());
callBtn.click(onClickCall());
acceptBtn.click(onClickAccept());
ignoreBtn.click(onClickIgnore());

$(document).on('click', '.close_call_btn', onClickClose());
$(document).on('click', '.start_call_btn', onClickCall());
$(document).on('click', '.accept_call_btn', onClickAccept());
$(document).on('click', '.ignore_call_btn', onClickIgnore());


function refreshContact(current, btns) {

    var id = current.id,
        name = current.name,
        online = current.online,
        busy = current.busy && online,
        calling = current.calling && online,
        called = false;
    if (contactToCall && online) {
        called = contactToCall.id == current.id;
    }


    var tableRow = $("tr").filter(function () {
        return $(this).attr("data-id") == id;
    }).closest("tr");

    if (tableRow.length === 0) {
        if (online) {
            var busy_str = '',
                calling_str = '',
                called_str = '';
            if (!busy) {
                busy_str = 'hidden'
            }
            ;
            if (!calling) {
                calling_str = 'hidden'
            }
            ;
            if (!called) {
                called_str = 'hidden'
            }
            ;


            var row = '<tr scope="row" data-id="' + id + '" class="even">\n' +
                '                        \n' +
                '                            <td class="pk" style="display:none;">' + id + '</td>\n' +
                '                        \n' +
                '                            <td class="name">' + name + '</td>\n' +
                '                        \n' +
                '                            <td class="online"><img class="inner_table online" src="/video/static/images/icons/online.png" style="display: none;"></td>\n' +
                '                        \n' +
                '                            <td class="busy"><img class="' + busy_str + ' inner_table busy" src="/video/static/images/icons/busy.png" style="display: none;"></td>\n' +
                '                        \n' +
                '                            <td class="calling"><img class="' + calling_str + ' inner_table calling" src="/video/static/images/icons/calling.png" style="display: none;"></td>\n' +
                '                        \n' +
                '                            <td class="called"><img class="' + called_str + ' inner_table called" src="/video/static/images/icons/called.png" style="display: none;"></td>\n' +
                '                        \n' +
                '                            <td valign="top"><button type="submit" class="btn btn-sm btn-responsive start_call_btn hidden btn-call btn-green" style="display: none;">Chiama</button><button type="submit" class="btn btn-sm btn-responsive close_call_btn hidden btn-close-call btn-red" style="display: none;">Chiudi</button><button type="submit" class="btn btn-sm btn-responsive accept_call_btn hidden btn-accept btn-green" style="display: none;">Rispondi</button><button type="submit" class="btn btn-sm btn-responsive ignore_call_btn hidden btn-ignore btn-red" style="display: none;">Ignora</button></td>\n' +
                '                        \n' +
                '                    </tr>';

            $('#smartglass tbody').append(row);
            contacts_list.push(current);

        }
    } else {
        if (online) {
            tableRow.find('td.name')[0].innerHTML = name;
            tableRow.find('td.online img').toggle(online);
            tableRow.find('td.busy img').toggle(busy);
            tableRow.find('td.calling img').toggle(calling);
            tableRow.find('td.called img').toggle(called);
            tableRow.find('.start_call_btn').toggle(online && !busy && !calling && !called);
            tableRow.find('.close_call_btn').toggle(called);
            tableRow.find('.accept_call_btn').toggle(calling);
            tableRow.find('.ignore_call_btn').toggle(calling);
            toggleSound(called, calling);
        } else {
            toggleSound(called, calling);
            tableRow.remove();

        }
    }

}

function displayContacts() {
    $('ul.list-group').empty();

    contacts_list.forEach(refreshContact);
}


function isCallingContact(current, calling) {
    var id = current.id;


    var tableRow = $("tr").filter(function () {
        return $(this).attr("data-id") == id;
    }).closest("tr");

    tableRow.find('td.calling img').toggle(calling);
    tableRow.find('.start_call_btn').toggle(!calling);
    tableRow.find('.close_call_btn').toggle(false);
    tableRow.find('.accept_call_btn').toggle(calling);
    tableRow.find('.ignore_call_btn').toggle(calling);
    if (calling)
        toggleSound(false, calling);


}

function isCalledContact(current, called) {
    var id = current.id;


    var tableRow = $("tr").filter(function () {
        return $(this).attr("data-id") == id;
    }).closest("tr");

    tableRow.find('td.called img').toggle(called);
    tableRow.find('.start_call_btn').toggle(!called);
    tableRow.find('.close_call_btn').toggle(called);
    tableRow.find('.accept_call_btn').toggle(false);
    tableRow.find('.ignore_call_btn').toggle(false);
    if (called)
        toggleSound(called, false);


}
