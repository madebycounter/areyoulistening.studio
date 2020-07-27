from PIL import Image, ImageDraw
import io

def create_print(design, cache=None, album_size=300,
                 design_size=2.75, design_gap=0.375,
                 album_layout=(3, 3), background=(255, 255, 255),
                 border=(0, 0, 0), border_size=2, 
                 logo_file='logo.png', logo_width=395,
                 logo_y_position=985):
    if not cache: raise Exception('cache argument required')
    logo = resize_image(Image.open(logo_file), width=logo_width)
    album_gap = int((design_gap / design_size) * album_size)
    total_size = album_size + album_gap + (2 * border_size)
    art_height = (total_size * album_layout[1]) - album_gap
    height = logo_y_position + logo.size[1]
    width = (total_size * album_layout[0]) - album_gap
    logo_x_position = int((width - logo.size[0]) / 2)

    img = Image.new('RGBA', (width, height), background)
    img.paste(logo, (logo_x_position, logo_y_position))
    draw = ImageDraw.Draw(img)
    for x in range(album_layout[0]):
        for y in range(album_layout[1]):
            if design[x][y]['image']:
                path = cache.get_image(design[x][y]['image'])
                album = Image.open(path)

                bounds = [
                    x * total_size,
                    y * total_size,
                    (x * total_size) + album_size + (2 * border_size) - 1,
                    (y * total_size) + album_size + (2 * border_size) - 1
                ]
                draw.rectangle(bounds, fill=border)

                bounds = [
                    (x * total_size) + border_size,
                    (y * total_size) + border_size,
                    (x * total_size) + border_size + album_size,
                    (y * total_size) + border_size + album_size
                ]
                img.paste(album.resize((album_size, album_size)), bounds)

    return img

def create_mockup(design_bytes, blank_path, title_path, b_position=(916, 653), b_width=668, t_position=(1113, 1331), t_width=262):
    design = Image.open(io.BytesIO(design_bytes)).convert('RGBA')
    blank = Image.open(blank_path)
    # title = Image.open(title_path)

    b_resized = resize_image(design, width=b_width)
    # t_resized = resize_image(title, width=t_width)
    blank.paste(b_resized, b_position, mask=b_resized)
    # blank.paste(t_resized, t_position, mask=t_resized)
    return blank

def resize_image(image, width=None, height=None):
    i_width, i_height = image.size
    ratio = i_width / i_height
    if not width: width = int(ratio * height)
    if not height: height = int(width / ratio)
    return image.resize((width, height))