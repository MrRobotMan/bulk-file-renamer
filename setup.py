from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='rename-utility',
    version='0.1',
    author='Davis Weiss',
    author_email='dweiss2@gmail.com',
    packages=['renamer'],
    scripts=['renamer/renamer'],
    url='https://gitlab.com/dweiss2/bulk-renamer.git',
    license='MIT',
    description='Bulk file rename tool',
    long_description=long_description,
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT',
        'Operating System :: OS Independent',
    ]
)
