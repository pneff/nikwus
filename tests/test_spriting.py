import glob
import os.path
from nikwus import sprite


def test_sprites():
    for directory in glob.glob(os.path.dirname(__file__) + '/*'):
        if os.path.isdir(directory + '/css'):
            yield check_sprites_dir, directory + '/css', directory + '/img'
        elif os.path.isdir(directory):
            yield check_sprites_dir, directory, directory


def check_sprites_dir(css_directory, sprite_directory):
    """Run tests on a single test directory."""
    input_file = os.path.join(css_directory, 'test.css')
    out_file = os.path.join(css_directory, 'test-out.css')
    expected_file = os.path.join(css_directory, 'test-expected.css')
    res = sprite(sprite_directory, input_file, out_file, offset=5)
    assert res, res
    assert os.path.exists(out_file)
    assert_same_contents(out_file, expected_file)


def assert_same_contents(file1, file2):
    """Assert that two files have the same content."""
    line_no = 0
    with open(file1) as f1:
        with open(file2) as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()
            while lines1:
                if not lines2:
                    assert False, 'file2 contains more lines than file1 at line {0}'.format(line_no)
                line1 = lines1.pop(0).strip()
                line2 = lines2.pop(0).strip()
                assert line1 == line2, '{0!r} != {1!r} at line {2}'.format(line1, line2, line_no)
                line_no += 1
            if lines2:
                assert False, 'file1 contains more lines than file2 at line {0}'.format(line_no)
