from setuptools import setup


# Read the long description from README.rst
with open('README.rst') as f:
    long_description = f.read()


setup(
    name='paramiko-expect',
    version='0.3.2',
    url='https://github.com/fgimian/paramiko-expect',
    license='MIT',
    author='Fotis Gimian',
    author_email='fgimiansoftware@gmail.com',
    description='An expect-like extension for the Paramiko SSH library',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    platforms='Posix',
    py_modules=['paramiko_expect'],
    install_requires=[
        'paramiko>=1.10.1',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Intended Audience :: Developers'
    ]
)
