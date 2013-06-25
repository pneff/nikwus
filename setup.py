from setuptools import setup, find_packages
setup(
    name='Nikwus',
    version='0.0.1',
    description="Automatically sprite images in CSS files",
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
