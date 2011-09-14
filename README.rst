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

Getting Started
---------------

You can get started developing the website with::

  $ git clone git://github.com/magcius/sweettooth.git
  $ cd sweettooth
  $ virtualenv_ --no-site-packages ./venv
  $ . ./venv/bin/activate
  $ pip_ install -r requirements.txt
  $ # ... Database setup...
  $ python sweettooth/manage.py `runserver_plus`_

Create a superuser, and log in. You should be able to upload extensions and
review extensions. There isn't a link to the code review UI, but it's hidden
at /review/.

.. _runserver_plus: http://packages.python.org/django-extensions/
.. _virtualenv: http://www.virtualenv.org/
.. _pip: http://www.pip-installer.org/

Testing with the Shell
======================

If you have GNOME Shell, and you want to test the installation system, you're
going to have to hack your system. For security reasons, the browser plugin and
GNOME Shell both ping the URL https://extensions.gnome.org directly. The
easiest way to get around this is to make a development environment with the
proper things that it needs. Since the Django development server doesn't
natively support SSL connections, we need to install Apache. Follow the
instructions above to get a proper SweetTooth checkout, and then::

  # Install Apache
  $ sudo yum install httpd mod_wsgi mod_ssl

  # Generate a self-signed cert
  $ openssl req -new -nodes -out ego.csr -keyout extensions.gnome.org.key
  # Answer questions. The only one required is the Common Name. You must put
  # extensions.gnome.org -- the hostname -- as the answer.

  $ openssl x509 -req -in ego.csr -signkey extensions.gnome.org.key -out extensions.gnome.org.crt
  $ rm ego.csr
  $ chmod 600 extensions.gnome.org.key

  # Install it on your system.
  $ sudo cp extensions.gnome.org.crt /etc/pki/tls/certs/
  $ sudo cp --preserve=mode extensions.gnome.org.key /etc/pki/tls/private/

  # The shell will look for a special file called 'extensions.gnome.org.crt',
  # for development purposes. Otherwise it will use your system's CA bundle.
  $ mkdir -p ~/.local/share/gnome-shell
  $ cp extensions.gnome.org.crt ~/.local/share/gnome-shell/

  # Configure Apache.
  $ cp etc/sweettooth.wsgi.example ./sweettooth.wsgi
  $ $EDITOR ./sweettooth.wsgi

  $ cp etc/sweettooth.httpd.conf.example ./sweettooth.httpd.conf
  $ $EDITOR ./sweettooth.httpd.conf
  $ sudo cp sweettooth.httpd.conf /etc/httpd/conf.d/sweettooth.conf

  # Edit /etc/hosts
  $ sudo tee -a /etc/hosts <<< 'extensions.gnome.org 127.0.0.1'


Requirements
------------

  * django_
  * django-autoslug_
  * django-tagging_
  * Pygments_
  * sorl-thumbnail_
  * south_

I develop with PostgreSQL_ at home, but Django should be able to use SQLite_,
MySQL_, and others. South_ is used for migrations.

.. _django: http://www.djangoproject.com/
.. _django-autoslug: http://packages.python.org/django-autoslug/
.. _Pygments: http://www.pygments.org/
.. _sorl-thumbnail: http://thumbnail.sorl.net/
.. _PostgreSQL: http://www.postgresql.org/
.. _SQLite: http://www.sqlite.org/
.. _MySQL: http://www.mysql.com/
.. _south: http://south.aeracode.org/
