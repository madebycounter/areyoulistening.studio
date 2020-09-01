$('#mockup').on('load', () => {
    $('#mockup_loader').addClass('hidden')
    $('#mockup').removeClass('hidden')
})

$('select').on('change textInput input', () => {
    update_pricing_ui()
})

$('#promo_code').on('change textInput input', () => {
    update_pricing_ui(true)
})

$(() => {
    if ($('#mockup')[0].complete) $('#mockup').trigger('load')
    var params = new URLSearchParams(window.location.search)
    $('#promo_code').val(params.get('promo'))

    update_pricing_ui()
})

function calculate_discount(promo, price) {
    var deduction = 0
    if (promo['type'] == 'percent') deduction = price * promo['amount'] / 100
    else if (promo['type'] == 'deduction') deduction = promo['amount']

    if (deduction > price) deduction = price
    return Math.round(deduction)
}

function to_dollar_price(value) {
    return '$' + (value / 100).toFixed(2)
}

function calculate_pricing(allow_confetti) {
    confetti.stop()
    var prices = {lines: [], total: null, order_total: 0}
    var promo_code = get_promo_code()
    var shipping_type = get_shipping_type()
    var promo = null

    if (promo_code in ITEM_DETAILS['promos']) {
        promo = ITEM_DETAILS['promos'][promo_code]
    }

    var item_price = ITEM_DETAILS['price']
    var shipping_price = ITEM_DETAILS['shipping'][shipping_type]

    var item_discount = 0
    var shipping_discount = 0

    if (promo && promo['affects'] == 'shipping')
        shipping_discount = calculate_discount(promo, shipping_price)
    if (promo && promo['affects'] == 'price')
        item_discount = calculate_discount(promo, item_price)

    prices.lines.push({
        'text': 'price',
        'style': 'color: black',
        'value': to_dollar_price(item_price)
    })

    if (item_discount != 0) {
        if (promo['type'] == 'percent') {
            prices.lines.push({
                'text': promo['amount'] + '% discount',
                'style': 'color: green',
                'value': '-' + to_dollar_price(item_discount)
            })
        } else {
            prices.lines.push({
                'text': 'discount',
                'style': 'color: green',
                'value': '-' + to_dollar_price(item_discount)
            })
        }
    }

    if (shipping_price - shipping_discount == 0) {
        prices.lines.push({
            'text': 'shipping',
            'style': 'color: green',
            'value': 'Free'
        })
    } else {
        if (shipping_discount != 0) {
            prices.lines.push({
                'text': 'shipping (discounted)',
                'style': 'color: green',
                'value': to_dollar_price(shipping_price - shipping_discount)
            })
        } else {
            prices.lines.push({
                'text': 'shipping',
                'style': 'color: black',
                'value': to_dollar_price(shipping_price)
            })
        }
    }

    if (allow_confetti && promo != null) {
        $('#promo_code').blur()
        confetti.start()
        setTimeout(confetti.stop, 1000)
    }

    prices.total = to_dollar_price((item_price + shipping_price) - (item_discount + shipping_discount))
    prices.order_total = item_price - item_discount
    return prices
}

function update_pricing_ui(allow_confetti) {
    var pricing = calculate_pricing(allow_confetti)
    
    $('#shipping_table').empty()
    for (var i in pricing.lines) {
        var line = pricing.lines[i]
        $('#shipping_table').append(`
            <tr>
                <th class="dashed">${line.text}</th>
                <td class="dashed" style="${line.style}">${line.value}</td>
            </tr>
        `)
    }

    $('#total').text(pricing.total)
}

function get_promo_code() {
    var promo = $('#promo_code').val()
    if (promo) return promo.toLowerCase()
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
                order_amount: calculate_pricing().order_total
            })
        }).then((res) => {
            return res.json()
        }).then((details) => {
            return details.order_id
        })
    },

    onApprove: (data) => {
        present_modal('modal_processing')
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
            close_modal('modal_processing')
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
                    value: ((calculate_pricing().order_total / 100) + shipping_price).toFixed(2),
                    breakdown: {
                        item_total: {
                            currency_code: 'USD',
                            value: (calculate_pricing().order_total / 100).toFixed(2)
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
