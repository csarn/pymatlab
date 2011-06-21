#!/usr/bin/python
# vim: set fileencoding=utf-8 :
from setuptools import setup,find_packages
from os.path import join
setup(
        name='pymatlab',
        version='0.2.0',
        description = 'A pythonic interface to MATLAB',
        long_description=open("README.txt").read() + "\n" + 
            open(join("docs", "CHANGELOG.txt")).read(),
        packages = find_packages('src'),
        package_dir={'':'src'},
        classifiers=['Development Status :: 3 - Alpha',
                        'Intended Audience :: End Users/Desktop',
                        'Intended Audience :: Developers',
                        'Intended Audience :: Science/Research',
                        'License :: OSI Approved :: GNU General Public License (GPL)',
                        'Operating System :: POSIX',
                        'Programming Language :: C',
                        'Programming Language :: Python',
                          ],
        test_suite='tests.alltests.test_suite',
        url = 'http://pymatlab.sourceforge.net/',
        zip_safe=False,
        author='Joakim Moller',
        author_email='joakim.moller@chalmers.se',
        install_requires=['setuptools','numpy'],
        #tests_require=['setuptools'],
)

