
from setuptools import setup, find_packages, Extension


setup(
    name='split-query',
    version='0.1.0',
    description='',
    url='',
    author='Simon Bowly',
    author_email='simon.bowly@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3'],
    packages=find_packages(where='.', include=['split_query']),
    install_requires=[],
    extras_require={})
