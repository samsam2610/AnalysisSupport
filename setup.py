from setuptools import setup, find_packages

setup(
    # Needed to silence warnings (and to be a worthwhile package)
    name='Analysis Support',
    url='https://github.com/samsam2610/AnalysisSupport',
    author='Sam Tran',
    author_email='quocsam93@gmail.com',
    # Needed to actually package something
    packages=find_packages(),
    # Needed for dependencies
    install_requires=['numpy',
                      'opencv-contrib-python==3.4.17.63',
                      'psycopg2-binary',
                      'Click'],
    entry_points={  # Optional
        'console_scripts': [
            'setup_package = setup_package.setup_package:main',
            'aniposesupport = analysissupport.aniposesupport:cli',
            'dlcsupport = analysissupport.dlcsupport:cli',
        ],
    },

    # *strongly* suggested for sharing
    version='0.1',
    description='Support functions for deeplabcut and anipose',
    # We will also need a readme eventually (there will be a warning)
    # long_description=open('README.txt').read(),
)