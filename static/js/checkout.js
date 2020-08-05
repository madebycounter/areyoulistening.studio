$('#mockup').on('load', () => {
    $('#mockup_loader').addClass('hidden')
    $('#mockup').removeClass('hidden')
})

$(() => {
    if ($('#mockup')[0].complete) $('#mockup').trigger('load')
})

// setInterval(() => {
//     if (['small', 'medium', 'large', 'extralarge'].indexOf($('#size').val()) != -1) {
//         console.log('allow')
//     } else {
//         console.log('deny')
//     }
// }, 100)

// function allow_paypal() {
//     $('#paypal_checkout').removeClass('hidden')
// }

// function hide_paypal() {
//     $('#paypal_checkout').addClass('hidden')
// }

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
                    value: '24.00',
                    currency: 'USD'
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
