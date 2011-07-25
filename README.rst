==============
SweetTooth-Web
==============

**SweetTooth-Web** is a Django-powered web application that, in co-operation
with some co-horts in GNOME Shell and other places, allows users to install,
upgrade and enable/disable their own Shell Extensions. All operations with
the Shell are done through special DBus proxies that have been developed
for SweetTooth: these include an NPAPI plugin and a local HTTP server.

Since extensions can be dangerous, all extensions uploaded to the repository
must go through code review and testing.

Proxies
-------

The DBus proxies are being developed in several forms. The initial prototype
was developed as a Python-based HTTP server. See `Bug #653212`_ for more details.

The NPAPI-based plugin, `sweettooth-plugin`_, is another alternative.

.. _Bug #653212: https://bugzilla.gnome.org/show_bug.cgi?id=653212
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
