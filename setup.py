import os
from setuptools import setup, find_packages



my_dir = os.path.dirname(os.path.realpath(__file__))

def readme():
    with open(os.path.join(my_dir, 'README.rst')) as f:
        return f.read()


setup(
    name='music_album_creation',
    version='1.0.8a',
    description='A CLI application intending to automate offline music library building',
    long_description=readme(),
    keywords='music album automation youtube audio metadata download',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Multimedia :: Sound/Audio :: Conversion',
        'Topic :: Multimedia :: Sound/Audio :: Editors',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        ],
    url='https://github.com/boromir674/music-album-creator',
    author='Konstantinos Lampridis',
    author_email='k.lampridis@hotmail.com',
    license='GNU GPLv3',
    packages=find_packages(where='src'),
    package_dir={'':'src'},
    install_requires=['tqdm', 'click', 'sklearn', 'mutagen', 'PyInquirer', 'youtube_dl'],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'create-album = music_album_creation.create_album:main',
        ]
    },
    setup_requires=['pytest-runner>=2.0',],
    tests_require=['pytest',],
    # test_suite='',
    zip_safe=False
)
