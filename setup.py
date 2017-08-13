from distutils.core import setup

try:
    long_desc = open('./README.rst').read()
except IOError:
    long_desc = 'See:https://github.com/EstudioNexos/getout/blob/master/README.md'

setup(
    name='Getout',
    version='0.1',
    author='Estudio Nexos - Néstor Díaz',
    author_email='hola@estudionexos.com',
    url='https://github.com/EstudioNexos/getout',
    install_requires=[
    "slugify",
    "requests",
    "beautifulsoup4",
    "lookupy",
    ],
    packages=['getout',],
    license='MIT License',
    description='Programmatic API in Python to interact with CDMON domain provider website.',
    long_description=long_desc,
)
