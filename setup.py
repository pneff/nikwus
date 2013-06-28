from setuptools import setup, find_packages

long_description = None
try:
    with open('README.rst') as f:
        long_description = f.read()
except Exception:
    print 'Could not open README file for long_description'

setup(
    name='Nikwus',
    version='0.5.1',
    description="Automatically sprite images in CSS files",
    long_description=long_description,
    author=", ".join([
        "Patrice Neff <mail@patrice.ch>",
    ]),
    packages=find_packages(),
    install_requires=[
        'cssutils',
        'Pillow',
    ],
    tests_require=[
        'nose',
    ],
    test_suite='nose.collector',
    license='BSD',
    classifiers=[
    ]
)
