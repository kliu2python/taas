from setuptools import setup

setup(
    author='cloud solutions QA team',
    description='Test As A Service',
    install_requires=[
        'Appium-Python-Client==1.0.2',
        'allure-pytest==2.8.17',
        'in_place==0.4.0',
        'PyMySql==0.10.0',
        'numpy==1.19.1',
        'opencv_python==4.2.0.34',
        'paramiko==2.7.1',
        'paramiko-expect==0.2.8',
        'pytest==6.0.1',
        'pytest-dependency==0.5.1',
        'pytest-xdist==1.34.0',
        'requests==2.24.0',
        'singleton_decorator==1.0.0',
        'selenium==3.141.0',
        'pyscreenshot==2.2',
        'flask==1.1.2',
        'flask_restful==0.3.8',
        'PyYAML==5.3.1',
        'jsonschema==3.2.0',
        'pycryptodome==3.0',
        'pyotp==2.4.0',
        'GitPython==3.1.3',
        'Pillow==7.1.1',
        'imagehash',
        'zeep==4.0.0', 'redis'
    ],
    name='pytest_automation',
    version='0.9',
    zip_safe=False
)
