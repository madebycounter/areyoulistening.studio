$('#mockup').on('load', () => {
    $('#mockup_loader').addClass('hidden')
    $('#mockup').removeClass('hidden')
})

$('select').on('change textInput input', () => {
    update_pricing()
})

$('#promo_code').on('change textInput input', () => {
    update_pricing(true)
})

$(() => {
    if ($('#mockup')[0].complete) $('#mockup').trigger('load')

    update_pricing()
})

var order_price = {}
var shipping_price = {}
var default_order_price = {}
var default_shipping_price = {}
function update_pricing(allow_confetti) {
    $.ajax({
        method: 'GET',
        url: '/api/order/price?item=shirt&promo=' + get_promo_code(),
        dataType: 'json',
        success: (d1) => {
            if (!d1.success) reset_pricing()

            order_price = {
                base_price: d1.base_price,
                final_price: d1.final_price,
                discount: d1.discount    
            }
    
            var country = get_shipping_type() == 'domestic' ? 'US' : 'OTHER'

            $.ajax({
                method: 'GET',
                url: '/api/order/shipping?country=' + country + '&item=shirt&promo=' + get_promo_code(),
                dataType: 'json',
                success: (d2) => {
                    if (!d2.success) return
                    shipping_price = {
                        price: d2.shipping_price,
                        discount: d2.discount
                    }

                    if (get_promo_code() == '') {
                        default_order_price = order_price
                        default_shipping_price = shipping_price
                    }

                    if (promo_code && allow_confetti) {
                        confetti.start()
                        $('#promo_code').blur()
                        setTimeout(confetti.stop, 1000)
                    }

                    update_pricing_ui()            
                }
            })
        }
    })
}

function reset_pricing() {
    order_price = default_order_price
    shipping_price = default_shipping_price

    update_pricing_ui()
}

function update_pricing_ui() {
    $('#shipping_table').empty()

    var base_price = (order_price.base_price / 100).toFixed(2)
    $('#shipping_table').append(`
        <tr>
            <th class="dashed">price</th>
            <td class="dashed">$${base_price}</td>
        </tr>
    `)

    if (order_price.discount != 0) {
        var discount = (order_price.discount / 100).toFixed(2)
        $('#shipping_table').append(`
            <tr>
                <th class="dashed">discount</th>
                <td class="dashed" style="color: green">-$${discount}</td>
            </tr>
        `)
    }

    var shipping_total = shipping_price.price == 0 ? 'Free' : `$${(shipping_price.price / 100).toFixed(2)}`
    var shipping_style = shipping_price.price == 0 ? 'style="color: green"' : ''
    if (shipping_price.price != 0 && shipping_price.discount != 0) {
        shipping_total += ` (-$${(shipping_price.discount / 100).toFixed(2)})`
        shipping_style = 'style="color: green"'
    }
    $('#shipping_table').append(`
        <tr>
            <th class="dashed">shipping</th>
            <td class="dashed" ${shipping_style}>${shipping_total}</td>
        </tr>
    `)

    $('#total').text(`$${((order_price.final_price + shipping_price.price) / 100).toFixed(2)}`)
}

function get_promo_code() {
    var promo = $('#promo_code').val()
    if (promo) return promo
    else return ''
}

function get_shirt_size() {
    return $('#size').val()
}

function get_shipping_type() {
    return $('#shipping').val()
}

paypal.Buttons({
    style: {
        height: 45,
        color: 'black',
        fundingicons: 'true'
    },

    createOrder: () => {
        return fetch('/api/order/create', {
            method: 'post',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                order_amount: order_amount
            })
        }).then((res) => {
            return res.json()
        }).then((details) => {
            return details.order_id
        })
    },

    onApprove: (data) => {
        return fetch('/api/order/finalize', {
            method: 'post',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
                order_id: data.orderID,
                item: 'shirt',
                promo: get_promo_code(),
                details: {
                    shirt_size: get_shirt_size(),
                    design_id: DESIGN_ID
                }
            })
        }).then((res) => {
            return res.json()
        }).then((details) => {
            if (!details.success) {
                $('#error_message').text(resp.message)
                present_modal('modal_error')
            } else {
                window.location.href = '/complete/' + details.order_id
            }
        })
    },

    onShippingChange: (data, actions) => {
        return fetch('/api/order/shipping?country=' + data.shipping_address.country_code + '&item=shirt&promo=' + get_promo_code(), {
            method: 'get'
        }).then((res) => {
            return res.json()
        }).then((details) => {
            var shipping_price = details.shipping_price / 100
            return actions.order.patch([{
                op: 'replace',
                path: '/purchase_units/@reference_id==\'default\'/amount',
                value: {
                    currency_code: 'USD',
                    value: ((order_amount / 100) + shipping_price).toFixed(2),
                    breakdown: {
                        item_total: {
                            currency_code: 'USD',
                            value: (order_amount / 100).toFixed(2)
                        },
                        shipping: {
                            currency_code: 'USD',
                            value: shipping_price.toFixed(2)
                        }
                    }
                }
            }])
        })
    }
}).render('#paypal_buttons');
