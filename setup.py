from setuptools import setup, find_packages

long_description = None
try:
    with open('README.rst') as f:
        long_description = f.read()
except Exception:
    print 'Could not open README file for long_description'

setup(
    name='Nikwus',
    version='0.5.2',
    description="Automatically sprite images in CSS files",
    long_description=long_description,
    author=", ".join([
        "Patrice Neff <mail@patrice.ch>",
    ]),
    packages=find_packages(),
    install_requires=[
        'cssutils >= 1.0',
        'Pillow',
    ],
    tests_require=[
        'nose',
    ],
    test_suite='nose.collector',
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
    ]
)
