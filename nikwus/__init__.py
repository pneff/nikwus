from PIL import Image
import cssutils
import os.path


DEFAULT_SPRITE_NAME = 'default'


def as_bool(value):
    """Converts a value into Boolean."""
    return str(value).lower() in ('1', 'true', 'on', 'yes')


class Sprite(object):
    # The name of this sprite
    name = None

    # Autosize set to True means we automatically add width and height
    # properties.
    autosize = True

    # The CSS declaration where the background image should be inserted.
    # If this is not set for a sprite, then the background image is inserted
    # for every declaration that uses any of the images in the sprite.
    selector_declaration = None

    # A list of CSS declarations which contain images for this sprite
    image_declarations = None

    def __init__(self, name=DEFAULT_SPRITE_NAME):
        self.name = name
        self.image_declarations = []

    def generate(self, directory):
        """Write an image for this sprite into the directory.
        """
        print 'writing {0} into {1}'.format(self.name, directory)

        target_width = target_height = 0
        images = []

        # Load images and determine the target image width/height
        for block, url in self.image_declarations:
            file_name = url.replace('file:///', '')
            print file_name
            img = Image.open(file_name)
            images.append(img)
            width, height = img.size
            target_width += width + 5
            target_height = max(target_height, height)
        target_width -= 5

        # Determine the width defined on the block
        default_width = default_height = ''
        if self.selector_declaration:
            default_width = self.selector_declaration.getPropertyValue('width')
            default_height = self.selector_declaration.getPropertyValue('height')

        # Create new image
        sprite_url = self.name + '.png'
        sprite = Image.new(mode='RGBA', size=(target_width, target_height),
                           color=(0, 0, 0, 0))
        vertical_offset = 0
        horizontal_offset = 0
        for block, url in self.image_declarations:
            img = images.pop(0)
            width, height = img.size
            sprite.paste(img, (horizontal_offset, vertical_offset))
            if self.selector_declaration:
                block.removeProperty('background')
                if vertical_offset > 0 or horizontal_offset > 0:
                    block.setProperty('background-position', '{0}px {1}'.format(
                        0 - horizontal_offset, vertical_offset))
            else:
                block.setProperty('background', 'url({2}) no-repeat {0}px {1}'.format(
                    0 - horizontal_offset, vertical_offset, sprite_url))

            if self.autosize:
                if not block.getPropertyValue('width') and not block.getPropertyValue('height'):
                    width_str = '{0}px'.format(width)
                    height_str = '{0}px'.format(height)
                    if width_str != default_width or height_str != default_height:
                        block.setProperty('width', width_str)
                        block.setProperty('height', height_str)

            horizontal_offset += width + 5

        if self.selector_declaration:
            self.selector_declaration.setProperty(
                'background', 'url({0}) no-repeat 0 0'.format(sprite_url))

        sprite.save(os.path.join(directory, sprite_url))


def sprite(directory, cssfile, outfile):
    style_sheet = cssutils.parseFile(cssfile, validate=False)
    sprites = get_sprites(style_sheet)
    for sprite in sprites:
        sprite.generate(directory)

    with open(outfile, 'wb') as f:
        f.write(style_sheet.cssText)

    return True


def get_sprites(style_sheet):
    """Returns a dict of all sprites that need to be created.

    The key is the name of the sprite, the value is a `Sprite` instance.
    """
    sprites = {}
    rules = style_sheet.cssRules.rulesOfType(cssutils.css.CSSRule.STYLE_RULE)
    for rule in rules:
        block = rule.style
        sprite_name = block.getPropertyValue('-sprite-name')
        sprite_autosize = block.getPropertyValue('-sprite-autosize')
        sprite_selector = block.getPropertyValue('-sprite-selector')
        sprite_on = block.getPropertyValue('-sprite')
        background = block.getPropertyCSSValue('background')
        background_image = None
        if background:
            for val in background:
                if isinstance(val, cssutils.css.URIValue):
                    background_image = val
                    break

        if not sprite_selector and not background_image:
            continue

        sprite_name = sprite_selector or sprite_name or DEFAULT_SPRITE_NAME
        sprite = sprites.setdefault(sprite_name, Sprite(sprite_name))

        block.removeProperty('-sprite-name')
        if sprite_selector:
            block.removeProperty('-sprite-selector')
            sprite.selector_declaration = block
        if sprite_autosize:
            block.removeProperty('-sprite-autosize')
            sprite.autosize = as_bool(sprite_autosize)
        if sprite_on:
            block.removeProperty('-sprite')

        if background_image:
            if sprite_on:
                sprite_on = as_bool(sprite_on)
            else:
                # Spriting is turned off by default for GIF images
                sprite_on = not background_image.absoluteUri.endswith('.gif')
            if sprite_on:
                sprite.image_declarations.append(
                    (block, background_image.absoluteUri))

    return sprites.values()
