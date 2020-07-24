$('#mockup').on('load', () => {
    $('#mockup_loader').addClass('hidden')
    $('#mockup').removeClass('hidden')
})

$(() => {
    if ($('#mockup')[0].complete) $('#mockup').trigger('load')
})

var select_open = false
var click_count = 0
$('select').click((e) => {
    $('#default').remove()
    select_open = !select_open
    click_count += 1
})

$('select').on('blur', (e) => {
    select_open = false
    close_select()
})

$(document).keyup(function(e) {
    if (e.keyCode == 27) {
        select_open = false
        close_select()
    }
})

function close_select() {
    if (!select_open && click_count != 0) allow_paypal()
}


$('select').change((e) => {
    allow_paypal()
})

function allow_paypal() {
    $('#paypal_checkout').removeClass('hidden')

    setTimeout(() => {
        $('html, body').animate({ scrollTop: 200 })
    }, 100)
}

paypal.Buttons({
    style: {
        height: 45,
        color: 'black',
        fundingicons: 'true'
    },

    createOrder: (data, actions) => {
        return actions.order.create({
            purchase_units: [{
                amount: {
                    value: '24'
                }
            }]
        });
    },

    onApprove: (data, actions) => {
        present_modal('modal_processing')
        actions.order.capture().then((details) => {
            var size = $('select').val()
            $.ajax({
                method: 'GET',
                url: '/api/order/process/' + details.id + '/' + ORDER_ID + '/' + size,
                dataType: 'json',
                success: (resp) => {
                    if (!resp.success) {
                        $('#error_message').text(resp.message)
                        present_modal('modal_error')
                    } else {
                        window.location.href = '/complete/' + ORDER_ID
                    }
                }
            })
        });
    }
}).render('#paypal_buttons');
