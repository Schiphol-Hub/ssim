from distutils.core import setup

setup(
    name='ssim',
    packages=['ssim'],
    package_dir={'ssim': 'ssim'},
    version='0.1.21',
    description='IATA SSIM (Standard Schedules Information Manual) file parser is a tool to read the standard IATA '
                'file format.',
    author='Rok Mihevc, Ramon Van Schaik, Howard Riddiough, Kevin Haagen',
    author_email='rok.mihevc@gmail.com',
    url='https://github.com/rok/ssim',
    keywords=['parsing', 'ssim', 'data'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6'
    ],
    entry_points={
        'console_scripts': [
            'ssim = ssim.__main__:main'
        ]
    }
)
