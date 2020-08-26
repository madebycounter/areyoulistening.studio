// COOKIES
function load_shirt_data() {
    $.cookie.raw = true
    cover_data = JSON.parse(atob($.cookie('shirt-data')))
    return cover_data
}

function save_shirt_data() {
    $.cookie.raw = true
    $.cookie('shirt-data', btoa(JSON.stringify(cover_data)))
    return $.cookie('shirt-data')
}

// API
function album_search(query, callback) {
    $.ajax({
        method: 'GET',
        url: '/api/search/' + query,
        success: callback, 
        dataType: 'json'
    })
}

function get_top_albums(callback) {
    $.ajax({
        method: 'GET',
        url: '/api/search/',
        success: callback, 
        dataType: 'json'
    })
}

// DYNAMIC
var selected_album, cover_data
function update_albums(list) {
    $('#results').empty()

    var check_loaded = () => {
        if (loaded_count == list.length) {
            $('#search_loader').addClass('hidden')
            $('#results').removeClass('hidden')
        }
    }

    var loaded_count = 0

    setTimeout(() => {
        if (loaded_count != list.length) {
            $('#search_loader').removeClass('hidden')
            $('#results').addClass('hidden')    
        }
    }, 100)

    list.forEach((album) => {
        var elem = $(`<img src="${album.image}" class="album" title="${album.name}" artist="${album.artist}" image_large="${album.image_large}"></img>`)
        $(elem).on('error', () => { $(elem).remove(); loaded_count++; check_loaded() })
        $(elem).on('load', () => { loaded_count++; check_loaded() })
        $('#results').append(elem)

        $(elem).on('click', (e) => {
            selected_album = elem;
            enable_close_view()
            pause_blink()
            // disable_fullscreen_search()
        })
    })

    if (list.length == 0) {
        $('#results').append($(`<p id="noresult">no results found :(</p>`))
        $('#search_loader').addClass('hidden')
        $('#results').removeClass('hidden')
    }
}

function do_search(dont_blur) {
    var query = $('#query').val()
    if (!dont_blur) $('#query').blur()
    album_search(query, update_albums)
}

$('#query').keypress((e) => {
    if (e.which == 13) do_search()
})

$('#query').on('input', (e) => {
    console.log($('#query').val())
    do_search(true)
})

// SQUARES
var config = {
    layout: { h: 3, v: 3 },
    offset: { x: 0, y: 260 },
    zoom_offset: 90,
    size: 83,
    gap: 10,
}

function get_square(x, y) {
    return $(`[xpos=${x}][ypos=${y}]`)
}

function init_squares() {
    $('#squares').empty()
    var use_cookie = $.cookie('shirt-data')

    try {
        cover_data = load_shirt_data()
    }
    catch (err) {
        console.log(err)
        use_cookie = false
    }

    if (!use_cookie) {
        cover_data = []
    }

    for (var x = 0; x < config.layout.h; x++) {
        if (!use_cookie) cover_data.push([])

        for (var y = 0; y < config.layout.v; y++) {
            var elem = $(`<div class="square" xpos="${x}" ypos="${y}"></div>`)
            $('#squares').append(elem)

            if (use_cookie) {
                var h_img = cover_data[x][y].hasOwnProperty('image')
                var h_artist = cover_data[x][y].hasOwnProperty('artist')
                var h_title = cover_data[x][y].hasOwnProperty('title')
                if (!(h_img && h_artist && h_title)) {
                    cover_data[x][y] = {
                        image: '',
                        title: '',
                        artist: ''
                    }
                } else {
                    if (cover_data[x][y]['image']) {
                        $(elem).css('background-image', `url(${cover_data[x][y]['image']})`)
                        $(elem).css('opacity', 0.9)
                    }
                }
            } else {
                cover_data[x].push({
                    image: '',
                    title: '',
                    artist: ''
                })
            }

            $(elem).click((e) => {
                if (selected_album && close_enabled) {
                    var url = $(selected_album).attr('src')
                    $(e.target).css('background-image', `url(${url})`)
                    $(e.target).css('opacity', 0.9)

                    var x = $(e.target).attr('xpos')
                    var y = $(e.target).attr('ypos')
                    cover_data[x][y] = {
                        image: $(selected_album).attr('image_large'),
                        title: $(selected_album).attr('title'),
                        artist: $(selected_album).attr('artist')
                    }

                    save_shirt_data()

                    selected_album = null
                    disable_close_view()



                    if (is_complete()) start_blink()
                } else {
                    $('#shirt').click()
                }
            })
        }
    }
}

function is_complete() {
    for (var x = 0; x < config.layout.h; x++)
        for (var y = 0; y < config.layout.v; y++)
            if (!cover_data[x][y].image)
                return false
    return true
}

function reset_squares() {
    $('.square').css('background-image', 'none')
    $('.square').css('opacity', 0.3)
    for (var x = 0; x < config.layout.h; x++) {
        for (var y = 0; y < config.layout.v; y++) {
            cover_data[x][y] = {
                image: '',
                title: '',
                artist: ''
            }
        }
    }
    
    stop_blink()
    save_shirt_data()
}

function update_squares() {
    var middle = ($('#design').width() / 2) + config.offset.x
    var height = $('#shirt').height()
    var size = height * config.size / 1000
    var gap = height * config.gap / 1000

    var top_left = {
        x: middle - (size * 1.5) - gap,
        y: height * config.offset.y / 1000
    }

    $('#shirt_title').css('width', 105 * height / 1000)
    $('#shirt_title').css('top', top_left.y + (config.layout.h * (size + gap) * 0.98))

    for (var x = 0; x < config.layout.h; x++) {
        for (var y = 0; y < config.layout.v; y++) {
            get_square(x, y).css('left', top_left.x + (x * (size + gap)))
            get_square(x, y).css('top', top_left.y + (y * (size + gap)))
            get_square(x, y).css('height', size)
            get_square(x, y).css('width', size)
        }
    }
}

// desktop
var is_desktop = false
function desktop_render() {
    var right_width = $(window).width() - $('#search').width()
    var max_height = $(window).height() - $('#header').height() - 30

    $('#header').css('right', (right_width - $('#header').width()) / 2)
    $('#header').css('display', 'block')
    $('#help').css('left', $('#search').width() + 20)
    $('#insta').css('right', right_width - $('#insta').width() - 15)

    if (right_width - 20 < max_height) $('#design').width(right_width - 20)
    else {
        $('#design').width(max_height)
        $('#design').css('right', (right_width - max_height) / 2)
    }
}

// RENDER
function enable_fullscreen_search() {
    var offset = $('#search').offset().top + $('body').scrollTop() + 1
    $('html, body').animate({ scrollTop: offset })
}

function disable_fullscreen_search() {
    $('html, body').animate({ scrollTop: 0 })
}

var close_enabled = false;
var currently_zooming = false;
function enable_close_view() {
    currently_zooming = true;

    var shirt_top = $('#shirt').offset().top + document.body.scrollTop
    var target_width = 1000

    var middle = ($(window).width() / 2) + config.offset.x
    var height = target_width
    var size = height * config.size / 1000
    var gap = height * config.gap / 1000

    var top_left = {
        y: height * config.offset.y / 1000
    }

    var scroll_target = top_left.y + (1 * (size + gap)) + shirt_top - ($(window).height() / 2)

    if (!is_desktop) {
        $('html, body').animate({ scrollTop: scroll_target + config.zoom_offset })
        $('#shirt').animate({ width: target_width }, {
            progress: update_display,
            complete: () => {
                close_enabled = true
                currently_zooming = false
            }
        })
    } else {
        close_enabled = true
        currently_zooming = false
    }

    if (selected_album) {
        var title = $(selected_album).attr('title')
        var artist = $(selected_album).attr('artist')
        $('#selected').text(`${title} - ${artist}`)
        $('#help').removeClass('hidden')
    }
}

function disable_close_view() {
    currently_zooming = true;

    if (!is_desktop) {
        $('#shirt').animate({ width: '100%' }, {
            progress: update_display,
            complete: () => { close_enabled = false; currently_zooming = false }
        })

        $('html, body').animate({ scrollTop: 0 })
    } else {
        close_enabled = false
        currently_zooming = false
    }

    $('#help').addClass('hidden')
}

function update_display() {
    is_desktop = $(window).width() > 1050

    if (is_desktop) desktop_render()
    $('#design').height($('#shirt').height())
    
    update_squares()
}

$('#shirt').on('click', (e) => {
    if (!currently_zooming && close_enabled) disable_close_view()
    if (!currently_zooming && !close_enabled) enable_close_view()
})

$('#query').on('focus click', (e) => {
    e.preventDefault()
    enable_fullscreen_search()
    pause_blink()
})

$(window).resize(update_display)

get_top_albums(update_albums)

var order_id;
function generate_order() {
    $('#preview_tooltip').text('Your design is being generated...')
    present_modal('order_loading')

    $.ajax({
        url: '/api/design/create',
        contentType: 'application/json',
        method: 'POST',
        data: JSON.stringify({
            cover_data: cover_data
        }),
        dataType: 'json',
        success: (d) => {
            order_id = d.order_id
            window.location.href = '/checkout/' + order_id
        },
        error: (e) => {
            close_modal('order_loading')
            present_modal('modal_error')
        }
    })
}

// fart blink
var blink_interval_id
function start_blink() {
    if (blink_interval_id) return
    var rate = 1000
    blink_interval_id = setInterval(() => {
        $('#order').css('background-color', 'lightgreen')
        setTimeout(() => {
            $('#order').css('background-color', '')                
        }, rate * 0.5)
    }, rate * 2)
}

function stop_blink() {
    clearTimeout(blink_interval_id)
    blink_interval_id = null
}

function pause_blink() {
    if (!blink_interval_id) return

    var delay = 5000
    stop_blink()
    setTimeout(start_blink, 5000)
}

// SHIRT SAVING DISABLED
// function save_order() {
//     var email = $('#email').val()
//     $('#preview_tooltip').text('Saving your design...')
//     present_modal('order_loading')
//     close_modal('save_design')

//     $.ajax({
//         url: '/api/order/save/' + email,
//         contentType: 'application/json',
//         method: 'POST',
//         data: JSON.stringify(cover_data),
//         dataType: 'json',
//         success: (d) => {
//             $('#saved_email').text(d.email)
//             close_modal('order_loading')
//             present_modal('design_saved')
//             console.log(d)
//         },
//         error: (e) => {
//             close_modal('order_loading')
//             present_modal('modal_error')
//         }
//     })
// }

function reset_confirm() {
    close_modal('order_loading')
    order_id = null
}

function checkout() {
    window.location.href = '/checkout/' + order_id
}

$('#reset').click(() => {
    present_modal('confirm_reset', () => {})
})

$('#order').click(() => {
    stop_blink()
    generate_order()
})

$(window).on('load', () => {
    $.cookie.raw = true
    init_squares()
    update_display()

    var params = new URLSearchParams(window.location.search)
    if (params.get('loaded') == 'true') present_modal('order_loaded')

    if (is_complete()) {
        console.log('fart')
        start_blink()
    }
})