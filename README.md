Docker Build Service
====================

Docker build service for Fedora. It will be integrated with koji (and copr) build system, fedmsg, Taskotron and other tools in Fedora infrastructure.

We are _not_ trying to compete with Docker Hub. Quite opposite. We would like to create an environment where Fedora users could very easily build images using Fedora infrastructure, test them and push them wherever they want (To Docker Hub for example).

Installation
------------

DBS is designed for Fedora 21.
Enable copr repository:

    sudo dnf copr enable jdornak/DBuildService

Install packages:

    sudo dnf install dbs-server

Check the configuration files:

    sudo vim /etc/httpd/conf.d/dbs.conf
    sudo vim /etc/dbs/site_settings

Use the commandline interface to create user:

    sudo dbs createsuperuser

If you want build images, you need to have worker running and need to have build image. Easiest way to get a build image is to clone [dock](https://github.com/DBuildService/dock) and do `make build-buildimage`.


Development Instance
--------------------

DBS is designed for Fedora 21.
Follow the **installation** steps. You do not need package
*dbs-server* itself, but you need all it's requirements.

Clone the git repository:

    git clone git@github.com:DBuildService/dbs-server.git
    cd dbs-server

Initialize development database:

    ./manage.py syncdb

Run a local Docker registry in order to store the built images:

    docker run -p 5000:5000 registry

Run development server:

    ./manage.py runserver

Run worker:

    ./manage.py celery worker -l INFO

Voilà!

For connecting from different machine, listen on all networks and open port
in Firewall. For Fedora 21 this can be done so:

    firewall-cmd --permanent --add-port=8000/tcp
    ./manage.py runserver 0.0.0.0:8000

Manipulate with the data
------------------------

In the future we will start using [Django migrations](https://docs.djangoproject.com/en/1.7/topics/migrations/)
but now it is easier to always drop and rebuild the database
with the current schema. To keep the data, you need to dump
it and then load it back:

    # dump data
    ./manage.py dumpdata --indent=4 > data.json

    # make some changes to the models
    # ...

    # rebuild the database
    rm data/db.sqlite3; ./manage.py syncdb --noinput

    # load data (you may need to edit data.json to match updated schema)
    ./manage.py loaddata data.json


RPM build
---------

Install tito and mock:

    dnf install tito mock

To build RPM locally:

    # build from the latest tagged release
    tito build --rpm
    # or build from the latest commit
    tito build --rpm --test

To build RPM using mock:

    SRPM=`tito build --srpm --test | egrep -o '/tmp/tito/dbs-server-.*\.src\.rpm'`
    sudo mock -r fedora-21-x86_64 $SRPM


Submit Build in Copr
-------------

First you need to set up rel-eng/releasers.conf:

    sed "s/<USERNAME>/$USERNAME/" < rel-eng/releasers.conf.template > rel-eng/releasers.conf

To submit build from the latest commit type:

    tito release copr-test

To submit build from the latest tag type:

    tito release copr

