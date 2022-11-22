from setuptools import setup

setup(
    author='cloud solutions QA team(Zheng Nie)',
    email='znie@fortinet.com',
    description='Test As A Service Cli client',
    install_requires=[
        'requests==2.24.0',
        'PyYAML==5.3.1',
    ],
    name='taascli',
    version='0.2',
    scripts=["taas"]
)
