from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


setup(
    name='music_album_creator',
    version='0.5.3',
    description='A CLI application intending to automate offline music library building',
    long_description=readme(),
    keywords='music album automation youtube audio metadata download',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        # 'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Multimedia :: Sound/Audio :: Conversion',
        'Topic :: Multimedia :: Sound/Audio :: Editors',
        'Intended Audience :: Science/Research',
        ],
    # url='',
    # author='Konstantinos',
    # author_email='',
    license='GNU GPLv3',
    packages=find_packages(exclude=["*.testing", "*.tests.*", "tests.*", "tests"]),
    install_requires=['tqdm', 'click', 'sklearn', 'mutagen', 'PyInquirer', 'youtube_dl'],
    include_package_data=True,
    entry_points = {
        'console_scripts': ['create-album=music_album_creation.create_album:main'],
    },
    setup_requires=['pytest-runner>=2.0',],
    tests_require=['pytest',],
    # test_suite='',
    zip_safe=False
)

# needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
# pytest_runner = ['pytest-runner'] if needs_pytest else []

# setup_requires=[
#         ... (other setup requirements)
    # ] + pytest_runner,
