#!/usr/bin/env python

import setuptools

setuptools.setup(
  name = 'redant',
  version = '0.0.1',
  description = '',
  author = 'redant',
  license = 'GPL-3.0',
  url = 'https://github.com/acegik/redant',
  download_url = 'https://github.com/acegik/redant/downloads',
  keywords = ['tiny-messaging-platform', 'chatbot'],
  install_requires = open("requirements.txt").readlines(),
  python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*",
  package_dir = {'':'src'},
  packages = setuptools.find_packages('src'),
)
