from setuptools import setup, find_packages

setup(
    name='networking-virtualbox',
    version='1.0.0',

    packages=find_packages(
        include=[
            'networking_vbox',
            'networking_vbox.*'
        ]
    ),

    python_requires='>=3.10',

    install_requires=[
        'neutron-lib',
        'oslo.config',
        'oslo.log',
    ],

    entry_points={
        'neutron.ml2.mechanism_drivers': [
            'virtualbox = networking_vbox.mechanism_driver:VirtualBoxMechanismDriver',
        ],
    },
)