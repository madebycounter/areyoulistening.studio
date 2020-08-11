// MODALS
function close_modal(id) {
    $(`#${id}`).css('display', 'none')
}

function present_modal(id) {
    $(`#${id}`).css('display', 'block')
}

function decode_flask_cookie(val) {
    if (val.indexOf('\\') === -1) return val

    val = val.slice(1, -1).replace(/\\"/g, '"')
    val = val.replace(/\\(\d{3})/g, (match, octal) => {
        return String.fromCharCode(parseInt(octal, 8))
    })

    return val.replace(/\\\\/g, '\\')
}