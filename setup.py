# import os
# import re
# from collections import OrderedDict

# from setuptools import find_packages, setup

# my_dir = os.path.dirname(os.path.realpath(__file__))



# # CONSTANTS
# src = 'src'
# name = 'music_album_creation'
# source_code_repo = 'https://github.com/boromir674/music-album-creator'
# changelog = '{}/blob/master/CHANGELOG.rst'.format(source_code_repo)


# def readme():
#     with open(os.path.join(my_dir, 'README.rst')) as f:
#         return f.read()
#     # return str(resource_string(__name__, 'README.rst'))

# with open(os.path.join(my_dir, src, name, '__init__.py')) as f:
#     _version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)


# setup(
#     name='music_album_creation',
#     version=_version,
#     description='A CLI application intending to automate offline music library building.',
#     long_description=readme(),
#     long_description_content_type='text/x-rst',
#     keywords='music automation download youtube metadata',

#     # rendered as 'HomePage' in Pypi
#     url=source_code_repo,

#     project_urls=OrderedDict([
#         # ("1-Tracker", "https://github.com/blahblah/gavgav/issues"),
#         ("1-Changelog", changelog),
#         ("2-Source", source_code_repo),
#         # ("4-Documentation", "https://blahblah.readthedocs.io/en/v{}/".format(_version)),
#     ]),

#     download_url='https://github.com/boromir674/music-album-creator/archive/v{}.tar.gz'.format(_version),  # help easy_install do its tricks
#     zip_safe=False,

#     # what packages/distributions (python) need to be installed when this one is. (Roughly what is imported in source code)
#     # install_requires=['attrs', 'tqdm', 'click', 'sklearn', 'mutagen', 'PyInquirer', 'youtube_dl', 'pyreadline', 'lxml'],

#     # A string or list of strings specifying what other distributions need to be present in order for the setup script to run.
#     # (Note: projects listed in setup_requires will NOT be automatically installed on the system where the setup script is being run.
#     # They are simply downloaded to the ./.eggs directory if they're not locally available already. If you want them to be installed,
#     # as well as being available when the setup script is run, you should add them to install_requires and setup_requires.)
#     # setup_requires=[],

#     # Folder where unittest.TestCase-like written modules reside. Specifying this argument enables use of the test command
#     # to run the specified test suite, e.g. via setup.py test.
#     test_suite='tests',

#     # Declare packages that the project's tests need besides those needed to install it. A string or list of strings specifying
#     # what other distributions need to be present for the package's tests to run. Note that these required projects will not be installed on the system where the
#     # tests are run, but only downloaded to the project's setup directory if they're not already installed locally.
#     # Use to ensure that a package is available when the test command is run.
#     tests_require=['pytest', 'mock'],

#     classifiers=[
#         'Development Status :: 5 - Production/Stable',
#         'Intended Audience :: End Users/Desktop',
#         'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
#         'Natural Language :: English',
#         'Operating System :: Microsoft :: Windows',
#         'Operating System :: POSIX :: Linux',
#         'Programming Language :: Python :: 2',
#         'Programming Language :: Python :: 2.7',
#         'Programming Language :: Python :: 3',
#         'Programming Language :: Python :: 3.5',
#         'Programming Language :: Python :: 3.6',
#         'Programming Language :: Python :: 3.7',
#         'Topic :: Home Automation',
#         'Topic :: Multimedia :: Video :: Conversion',
#         'Topic :: Multimedia :: Sound/Audio',
#     ],

#     author='Konstantinos Lampridis',
#     author_email='k.lampridis@hotmail.com',
#     license='GNU GPLv3',
#     packages=find_packages(where=src),
#     package_dir={'': src},  # this is required by distutils
#     # py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
#     include_package_data=True,  # Include all data files in packages that distutils are aware of through the MANIFEST.in file
#     # package_data={
#     #     # If any package contains *.txt or *.rst files, include them:
#     #     '': ['*.txt', '*.rst'],
#     #     'music_album_creation.format_classification': ['data/*.txt', 'data/model.pickle'],
#     # },
#     entry_points={
#         'console_scripts': [
#             'create-album = music_album_creation.create_album:main',
#         ]
#     },
#     # A dictionary mapping names of "extras" (optional features of your project: eg imports that a console_script uses) to strings or lists of strings
#     # specifying what other distributions must be installed to support those features.
#     # extras_require={},
# )
