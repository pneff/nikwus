from PIL import Image
import cssutils
import logging
import os.path


SPRITE_OFFSET = 10


def as_bool(value):
    """Converts a value into Boolean."""
    return str(value).lower() in ('1', 'true', 'on', 'yes')


def normalize_filename(url):
    """
    Normalize file names from file URL to local file names.

    Filenames start with `file:///` on Windows and `file://` on Unix.
    """
    fname = url.replace('file://', '')
    if os.sep != '/' and not os.path.exists(fname):
        fname = fname.lstrip('/')
    return fname


class Sprite(object):
    # The name of this sprite
    name = None

    # Autosize set to True means we automatically add width and height
    # properties.
    autosize = True

    # The CSS declarations where the background image should be inserted.
    # For each resolution there is one entry in the dict.
    # If this is not set for a sprite, then the background image is inserted
    # for every declaration that uses any of the images in the sprite.
    selector_declarations = None

    # A list of CSS declarations which contain images for this sprite
    image_declarations = None

    # Horizontal spacing of icons
    space_x = SPRITE_OFFSET
    space_y = SPRITE_OFFSET

    def __init__(self, name):
        self.name = name
        self.image_declarations = []
        self.selector_declarations = {}

    def generate(self, directory, reldir, offset=None):
        """Write an image for this sprite into the directory.
        """
        print 'writing {0} into {1}'.format(self.name, directory)
        if offset is not None:
            self.space_x = self.space_y = offset

        if self.selector_declarations and not self.selector_declarations.get(1):
            raise ValueError('Missing sprite selector for default resolution')

        # Load images and determine the target image width/height
        if self.selector_declarations:
            resolutions = self.selector_declarations.keys()
        else:
            resolutions = [1]
        images = self._load_images(resolutions)
        distribution = self._calculate_distribution(images)

        # Create and save the sprites
        sprites = self._create_sprites(directory, reldir, resolutions,
                                       distribution)

        # Change the CSS rules for the sprite
        self._rewrite_css(distribution, sprites)

    def _load_images(self, resolutions=None):
        """Load the images from the image declarations. For each image
        we load every resolution.

        Checks that the images have the correct size, e.g. that an image of
        resolution 2 is in fact two times bigger than the original.
        """
        images = {}

        for block, url in self.image_declarations:
            file_name = normalize_filename(url)
            if file_name not in images:
                img_resolutions = {}
                img = Image.open(file_name)
                img_resolutions[1] = img
                width, height = img.size

                if resolutions:
                    for resolution in resolutions:
                        # Get the correct filename for this resolution
                        if resolution != 1:
                            root, ext = os.path.splitext(file_name)
                            res_file_name = '{root}-{resolution}x{ext}'.format(
                                root=root, resolution=resolution, ext=ext)

                            img = Image.open(res_file_name)
                            if img.size[0] / resolution != width:
                                raise ValueError('Invalid width for {0}'.format(
                                    res_file_name))
                            if img.size[1] / resolution != height:
                                raise ValueError('Invalid height for {0}'.format(
                                    res_file_name))
                            img_resolutions[resolution] = img

                images[file_name] = img_resolutions

        return images

    def _calculate_distribution(self, images):
        """Calculate the best distribution of the sprite image.
        """
        positions = {}
        target_width = target_height = 0
        for block, url in self.image_declarations:
            file_name = normalize_filename(url)
            if file_name in positions:
                positions[file_name]['blocks'].append(block)
            else:
                block_images = images[file_name]
                offset_x = target_width
                offset_y = 0

                width, height = block_images[1].size
                positions[file_name] = {
                    'x': offset_x, 'y': offset_y,
                    'width': width, 'height': height,
                    'file_name': file_name, 'images': block_images,
                    'blocks': [block]
                }

                target_width += width + self.space_x
                target_height = max(target_height, height)

        target_width -= self.space_x
        return {
            'width': target_width,
            'height': target_height,
            'positions': positions.values(),
        }

    def _create_sprites(self, directory, reldir, resolutions, distribution):
        if not distribution['positions']:
            return

        # Create sprite images
        sprites = {}
        for resolution in resolutions:
            if resolution == 1:
                sprite_fname = self.name + '.png'
            else:
                sprite_fname = '{0}-{1}x.png'.format(self.name, resolution)

            # Make the sprite URL relative to the CSS file
            if reldir:
                sprite_url = reldir + '/' + sprite_fname
            else:
                sprite_url = sprite_fname

            image = Image.new(
                mode='RGBA',
                size=(distribution['width'] * resolution,
                      distribution['height'] * resolution),
                color=(0, 0, 0, 0))

            # Place images on sprite and edit the CSS rules
            for pos in distribution['positions']:
                pos_x = pos['x']
                pos_y = pos['y']
                pos_img = pos['images'][resolution]
                image.paste(pos_img, (pos_x * resolution, pos_y * resolution))

            sprites[resolution] = {
                'url': sprite_url,
                'img': image,
            }

            image.save(os.path.join(directory, sprite_fname))

        return sprites

    def _rewrite_css(self, distribution, sprites):
        default_width, default_height = self._get_default_size()

        # Edit the CSS rules
        for pos in distribution['positions']:
            sprite_url = sprites[1]['url']
            for block in pos['blocks']:
                self._rewrite_css_block(block, pos, sprite_url, default_width,
                                        default_height)

        for resolution, decl in self.selector_declarations.iteritems():
            sprite_url = sprites[resolution]['url']
            if resolution == 1:
                decl.setProperty('background', 'url({0}) no-repeat 0 0'.format(
                    sprite_url))
            else:
                decl.setProperty('background-image', 'url({0})'.format(
                    sprite_url))
                decl.setProperty('background-size', '{0}px {1}px'.format(
                    distribution['width'], distribution['height']))

    def _rewrite_css_block(self, block, pos, sprite_url, default_width,
                           default_height):
        """Rewrite an individual block."""
        pos_x = pos['x']
        pos_y = pos['y']
        width = pos['width']
        height = pos['height']

        if self.selector_declarations:
            block.removeProperty('background')
            if pos_x > 0 or pos_y > 0:
                block.setProperty('background-position', '{0}px {1}'.format(
                    0 - pos_x, pos_y))
        else:
            block.setProperty('background', 'url({2}) no-repeat {0}px {1}'.format(
                0 - pos_x, pos_y, sprite_url))

        if self.autosize:
            if not block.getPropertyValue('width') and not block.getPropertyValue('height'):
                width_str = '{0}px'.format(width)
                height_str = '{0}px'.format(height)
                if width_str != default_width or height_str != default_height:
                    block.setProperty('width', width_str)
                    block.setProperty('height', height_str)

    def _get_default_size(self):
        """Return the default sizes of the icons.

        Used for autosizing to decide whether we need to include the
        width/height of the image in the block.
        """
        default_width = default_height = ''
        if self.selector_declarations:
            default_width = self.selector_declarations[1].getPropertyValue('width')
            default_height = self.selector_declarations[1].getPropertyValue('height')
        return default_width, default_height


def sprite(directory, cssfile, outfile=None, offset=SPRITE_OFFSET):
    logger = logging.getLogger('cssutils')
    logger.setLevel(logging.FATAL)
    cssutils.log.setLog(logger)

    if outfile is None:
        outfile = cssfile

    style_sheet = cssutils.parseFile(cssfile, validate=False)

    # Calculate relative directory name from CSS file to the output directory
    reldir = os.path.relpath(directory, os.path.dirname(cssfile))
    reldir = reldir.replace('\\', '/').rstrip('/')
    if reldir == '.':
        reldir = ''

    # Name the default sprite the same as the CSS file
    default_sprite_name, _ = os.path.splitext(os.path.basename(cssfile))

    sprites = get_sprites(style_sheet.cssRules, default_sprite_name)
    for sprite in sprites:
        sprite.generate(directory, reldir, offset=offset)

    with open(outfile, 'wb') as f:
        f.write(fixup_css(style_sheet.cssText))

    return True


def fixup_css(text):
    """Apply a workaround for CSSUtils, which replaces `\0` tokens in the code
    with actual 0-bytes. `\0` is used as a IE hack, e.g. by Twitter's
    Bootstrap.
    """
    return text.replace('\x00', '\\0')


def get_sprites(rules, default_sprite_name, sprites=None):
    """Returns a dict of all sprites that need to be created from the given
    rules.

    The key is the name of the sprite, the value is a `Sprite` instance.

    This is used recursively, in which case `sprites` is set to the dict
    that is returned in the end.
    """
    if sprites is None:
        sprites = {}

    for rule in rules:
        if hasattr(rule, 'style'):
            _process_rule(rule, sprites, default_sprite_name)
        if hasattr(rule, 'cssRules'):
            get_sprites(rule.cssRules, default_sprite_name, sprites)

    return sprites.values()


def _process_rule(rule, sprites, default_sprite_name):
    """Process an individual rule for sprite preparation.
    """
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
        return

    sprite_resolution = 1
    if sprite_selector and ' ' in sprite_selector:
        sprite_selector, sprite_resolution = sprite_selector.split(' ', 1)
        if not sprite_resolution.endswith('x'):
            raise ValueError('Invalid sprite resolution: {0}'.format(
                sprite_resolution))
        if not sprite_resolution[:-1].isnumeric():
            raise ValueError('Invalid sprite resolution: {0}'.format(
                sprite_resolution))
        sprite_resolution = int(sprite_resolution[:-1])

    sprite_name = sprite_selector or sprite_name or default_sprite_name
    if sprite_name == 'default':
        sprite_name = default_sprite_name

    sprite = sprites.setdefault(sprite_name, Sprite(sprite_name))

    block.removeProperty('-sprite-name')
    if sprite_selector:
        block.removeProperty('-sprite-selector')
        if sprite_resolution in sprite.selector_declarations:
            raise ValueError(
                'Multiple sprite-selectors for %s at resolution %d',
                sprite_selector, sprite_resolution)
        sprite.selector_declarations[sprite_resolution] = block
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
