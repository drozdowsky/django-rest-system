import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()

setup(
    name='django-rest-system',
    version='0.0.1',
    packages=['drs'],
    description="Django REST based on django's {values}",
    long_description=README,
    long_description_content_type='text/markdown',
    author='drozdowsky',
    author_email='hdrozdow+github@pm.me',
    url='https://github.com/drozdowsky/django-rest-system/',
    license='MIT',
    install_requires=[
        'Django>=1.11',
    ]
)
