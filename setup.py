from setuptools import setup

setup(name='pyactr',
      version='0.1.2',
      description='ACT-R in Python',
      url='https://github.com/jakdot/pyactr',
      author='jakdot',
      author_email='j.dotlacil@gmail.com',
      packages=['pyactr'],
      install_requires=['numpy', 'simpy', 'pyparsing'],
      zip_safe=False)
