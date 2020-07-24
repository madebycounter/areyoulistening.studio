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
        url: '/api/top',
        success: callback, 
        dataType: 'json'
    })
}

// DYNAMIC
var selected_album, cover_data
function update_albums(list) {
    $('#results').empty()

    $('#search_loader').removeClass('hidden')
    $('#results').addClass('hidden')

    var check_loaded = () => {
        if (loaded_count == list.length) {
            $('#search_loader').addClass('hidden')
            $('#results').removeClass('hidden')
        }
    }

    var loaded_count = 0;
    list.forEach((album) => {
        var elem = $(`<img src="${album.image}" class="album" title="${album.name}" artist="${album.artist}" image_large="${album.image_large}"></img>`)
        $(elem).on('error', () => { $(elem).remove(); loaded_count++; check_loaded() })
        $(elem).on('load', () => { loaded_count++; check_loaded() })
        $('#results').append(elem)

        $(elem).on('click', (e) => {
            selected_album = elem;
            enable_close_view()
            // disable_fullscreen_search()
        })
    })

    if (list.length == 0) {
        $('#results').append($(`<p id="noresult">no results found :(</p>`))
        $('#search_loader').addClass('hidden')
        $('#results').removeClass('hidden')
    }
}

function do_search() {
    var query = $('#query').val()
    $('#query').blur()
    album_search(query, update_albums)
}

$('#query').keypress((event) => {
    if (event.which == 13) do_search()
});

// SQUARES
var config = {
    layout: { h: 3, v: 3 },
    offset: { x: 0, y: 260 },
    zoom_offset: -10,
    size: 83,
    gap: 10,
}

function get_square(x, y) {
    return $(`[xpos=${x}][ypos=${y}]`)
}

function init_squares() {
    $('#squares').empty()
    cover_data = []

    for (var x = 0; x < config.layout.h; x++) {
        cover_data.push([])
        for (var y = 0; y < config.layout.v; y++) {
            var elem = $(`<div class="square" xpos="${x}" ypos="${y}"></div>`)
            $('#squares').append(elem)
            cover_data[x].push({
                image: '',
                title: '',
                artist: ''
            })

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

                    selected_album = null
                    disable_close_view()
                } else {
                    $('#shirt').click()
                }
            })
        }
    }
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
var is_desktop = true
function desktop_render() {
    var right_width = $(window).width() - $('#search').width()
    var max_height = $(window).height() - $('#header').height() - 30

    $('#header').css('right', (right_width - $('#header').width()) / 2)
    $('#header').css('display', 'block')
    $('#help').css('left', $('#search').width() + 20)

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
    console.log(shirt_top)
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
})

$(window).resize(update_display)
$(window).on('load', () => {
    init_squares()
    update_display()
})

get_top_albums(update_albums)

// MODALS
function close_modal(id) {
    $(`#${id}`).css('display', 'none')
}

function present_modal(id) {
    $(`#${id}`).css('display', 'block')
}

var order_id;
function generate_order() {
    present_modal('confirm_order')

    $.ajax({
        url: '/api/order/create',
        contentType: 'application/json',
        method: 'POST',
        data: JSON.stringify(cover_data),
        dataType: 'json',
        success: (d) => {
            order_id = d.order
            $('#preview .spinner').addClass('hidden')
            $('#preview_buttons').removeClass('hidden')
            $('#preview').css('background-image', `url(/api/order/mockup/${d.order}?width=700)`)
            $('#preview').css('background-color', 'white')
            $('#preview_tooltip').text('Please confirm your design')
        },
    })
}

function reset_confirm() {
    close_modal('confirm_order')
    $('#preview .spinner').removeClass('hidden')
    $('#preview_buttons').addClass('hidden')
    $('#preview').css('background-image', 'none')
    $('#preview').css('background-color', 'rgba(0, 0, 0, 0.2)')
    $('#preview_tooltip').text('Your design is being generated...')
    order_id = null
}

function checkout() {
    window.location.href = '/checkout/' + order_id
}

$('#reset').click(() => {
    present_modal('confirm_reset', () => {})
})

$('#order').click(() => {
    var all_filled = true
    for (var x = 0; x < config.layout.h; x++) {
        for (var y = 0; y < config.layout.v; y++) {
            opacity = get_square(x, y).css('opacity')
            if (opacity != 0.9) all_filled = false
        }
    }

    if (!all_filled) present_modal('confirm_incomplete')
    else generate_order()
})