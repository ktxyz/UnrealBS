from setuptools import setup

setup(
    name='UnrealBS',
    version='0.0.1',
    packages=['UnrealBS', 'UnrealBS.Common', 'UnrealBS.Server', 'UnrealBS.Worker'],
    url='https://github.com/ktxyz/UnrealBS',
    license='GNU LGPL 2.1',
    author='ktxyz',
    author_email='opensource@tokarski.xyz',
    description='simple build service for Unreal Engine 4',

    entry_points={
        'console_scripts': [
            'UnrealBS = UnrealBS.__main__:Main',
            'UnrealBS-Server = UnrealBS.Server.__main__:Main',
            'UnrealBS-Worker = UnrealBS.Worker.__main__:Main',
        ]
    }
)
