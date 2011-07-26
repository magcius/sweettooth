==============
SweetTooth-Web
==============

**SweetTooth-Web** is a Django-powered web application that, in co-operation
with some co-horts in GNOME Shell and other places, allows users to install,
upgrade and enable/disable their own Shell Extensions. All operations with
the Shell are done through a special NPAPI plugin, sweettooth-plugin_, which
proxies over to the Shell by DBus.

Since extensions can be dangerous, all extensions uploaded to the repository
must go through code review and testing.

.. _sweettooth-plugin: https://github.com/magcius/sweettooth-plugin

Requirements
------------

For now, we require:

  * django_
  * django-autoslug_
  * django-extensions_
  * django-tagging_
  * sorl-thumbnail_

I develop with PostgreSQL_ at home, but Django should be able to use
SQLite_, MySQL_, and others.

.. _django: http://www.djangoproject.com/
.. _django-autoslug: http://packages.python.org/django-autoslug/
.. _django-extensions: http://packages.python.org/django-extensions/
.. _django-tagging: http://code.google.com/p/django-tagging/
.. _sorl-thumbnail: http://thumbnail.sorl.net/
.. _PostgreSQL: http://www.postgresql.org/
.. _SQLite: http://www.sqlite.org/
.. _MySQL: http://www.mysql.com/
