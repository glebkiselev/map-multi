from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='mapmulti',
    version='1.0.0',
    packages=['mapmulti', 'mapmulti.grounding', 'mapmulti.pddl', 'mapmulti.search', 'mapmulti.agent', 'mapmulti.hddl'],
    package_dir={'mapmulti': 'src'},
    url='http://cog-isa.github.io/mapplanner/',
    license='',
    author='KiselevGA',
    author_email='kiselev@isa.ru',
    long_description=open('README.md').read(),
    install_requires=required,
    include_package_data=True
)