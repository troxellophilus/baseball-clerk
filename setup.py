from setuptools import setup, find_packages

from baseballclerk import __version__ as VERSION


setup(
    name='baseballclerk',  # Required
    version=VERSION,  # Required
    description='Baseball play by play and more for Reddit.',  # Optional
    url='https://gitlab.com/dtrox/baseball-clerk',  # Optional
    author='Drew Troxell',  # Optional
    author_email='code@trox.space',
    classifiers=[  # Optional
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),  # Required
    install_requires=['praw', 'requests']  # Optional
)
