from setuptools import setup, find_packages


# dependencies
with open('requirements.txt') as f:
    deps = f.read().splitlines()

setup(name='treestatus_stats',
      version=0.1,
      description="A tool for getting information on the health of the tree that also produces",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='mozilla',
      author='David Burns',
      author_email='david.burns@theautomatedtester.co.uk',
      url='https://developer.mozilla.org/en-US/docs/Marionette',
      license='MPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      entry_points={'console_scripts': [
          'treestatus = treestatus_stats']},
      install_requires=deps)
