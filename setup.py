import os
from setuptools import setup, find_packages


try:
    f = open(os.path.join(os.path.dirname(__file__), 'README.md'))
    long_description = f.read().strip()
    f.close()
except IOError:
    long_description = None

setup(
    name='sleepy.mongoose',
    version='0.1',
    url='https://github.com/kchodorow/sleepy.mongoose',
    description='A REST interface for MongoDB',
    long_description=long_description,
    author='Kristina Chodorow',
    author_email='kristina@10gen.com',
    license='BSD',
    keywords='mongo http rest json proxy'.split(),
    platforms='any',
    entry_points = {
        'console_scripts': [
            'httpd = sleepymongoose.httpd:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
    packages=find_packages(exclude=['t']),
    include_package_data=True,
)

