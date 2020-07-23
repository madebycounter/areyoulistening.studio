$('#mockup').on('load', () => {
    $('#mockup_loader').addClass('hidden')
    $('#mockup').removeClass('hidden')
})

$(() => {
    if ($('#mockup')[0].complete) $('#mockup').trigger('load')
})

$('select').click((e) => {
    $('#default').remove()
})

$('select').change((e) => {
    $('#paypal_checkout').removeClass('hidden')

    setTimeout(() => {
        $('html, body').animate({ scrollTop: 200 })
    }, 100)
})

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
        actions.order.capture().then((details) => {
            var size = $('select').val()
            $.ajax({
                method: 'GET',
                url: '/api/order/process/' + details.id + '/' + ORDER_ID + '/' + size,
                dataType: 'json',
                success: (resp) => {
                    console.log(resp)
                }
            })
        });
    }
}).render('#paypal_buttons');
