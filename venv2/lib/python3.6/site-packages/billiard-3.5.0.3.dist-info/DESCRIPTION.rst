========
billiard
========
:version: 3.5.0.2

|build-status-lin| |build-status-win| |license| |wheel| |pyversion| |pyimp|

.. |build-status-lin| image:: https://secure.travis-ci.org/celery/billiard.png?branch=master
    :alt: Build status on Linux
    :target: https://travis-ci.org/celery/billiard

.. |build-status-win| image:: https://ci.appveyor.com/api/projects/status/github/celery/billiard?png=true&branch=master
    :alt: Build status on Windows
    :target: https://ci.appveyor.com/project/ask/billiard

.. |license| image:: https://img.shields.io/pypi/l/billiard.svg
    :alt: BSD License
    :target: https://opensource.org/licenses/BSD-3-Clause

.. |wheel| image:: https://img.shields.io/pypi/wheel/billiard.svg
    :alt: Billiard can be installed via wheel
    :target: http://pypi.python.org/pypi/billiard

.. |pyversion| image:: https://img.shields.io/pypi/pyversions/billiard.svg
    :alt: Supported Python versions.
    :target: http://pypi.python.org/pypi/billiard

.. |pyimp| image:: https://img.shields.io/pypi/implementation/billiard.svg
    :alt: Support Python implementations.
    :target: http://pypi.python.org/pypi/billiard

About
-----

`billiard` is a fork of the Python 2.7 `multiprocessing <http://docs.python.org/library/multiprocessing.html>`_
package. The multiprocessing package itself is a renamed and updated version of
R Oudkerk's `pyprocessing <http://pypi.python.org/pypi/processing/>`_ package.
This standalone variant draws its fixes/improvements from python-trunk and provides
additional bug fixes and improvements.

- This package would not be possible if not for the contributions of not only
  the current maintainers but all of the contributors to the original pyprocessing
  package listed `here <http://pyprocessing.berlios.de/doc/THANKS.html>`_

- Also it is a fork of the multiprocessing backport package by Christian Heims.

- It includes the no-execv patch contributed by R. Oudkerk.

- And the Pool improvements previously located in `Celery`_.

- Billiard is used in and is a dependency for `Celery`_ and is maintained by the
  Celery team.

.. _`Celery`: http://celeryproject.org

Bug reporting
-------------

Please report bugs related to multiprocessing at the
`Python bug tracker <http://bugs.python.org/>`_. Issues related to billiard
should be reported at http://github.com/celery/billiard/issues.


