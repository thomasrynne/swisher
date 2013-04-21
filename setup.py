from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='swisher',
    version='0.1',
    description='An RFID music player',
    long_description=readme(),
    keywords='mpd RFID music raspberrypi',
    url='https://github.com/thomasrynne/swisher',
    author='Thomas Rynne',
    author_email='swisher@thomasrynne.co.uk',
    license='GPLv3',
    packages=['swisher'],
    include_package_data=True,
    install_requires=[
        'evdev','cherrypy','mako','reportlab', 'pyyaml',
        'pyinotify','python-mpd2'],
    zip_safe=False,
    platforms=["linux"],
    entry_points = {
        'console_scripts': ['swisher=swisher.init:main'],
    })
