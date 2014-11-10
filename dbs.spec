%global  dbs_statedir   %{_sharedstatedir}/dbs
%global  dbs_confdir    %{_sysconfdir}/dbs
%global  httpd_confdir  %{_sysconfdir}/httpd/conf.d

Name:           dbs
Version:        0.2
Release:        1%{?dist}

Summary:        Docker Build Service
Group:          Development Tools
License:        BSD
URL:            https://github.com/orgs/DBuildService/dashboard
Source0:        http://github.srcurl.net/DBuildService/%{name}/%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python-devel
BuildRequires:  python-setuptools
BuildRequires:  systemd

Requires:       dock
Requires:       httpd
Requires:       mod_ssl
Requires:       mod_wsgi
Requires:       python-celery
Requires:       python-django >= 1.7
Requires:       python-django-celery
Requires(pre):  /usr/sbin/useradd


%description
Docker Build Service


%package server
Summary:        Docker Build Service Web
Group:          Development Tools
Requires:       %{name}

%description server
Docker Build Service Web


%package worker
Summary:        Docker Build Service Worker
Group:          Development Tools
Requires:       %{name}
Requires:       docker
Requires:       systemd
Requires:       GitPython
Requires:       docker-registry
Requires:       redis
Requires(preun):    systemd-units
Requires(postun):   systemd-units
Requires(post):     systemd-units

%description worker
Docker Build Service Worker



%prep
%setup -q


%build
# prepare config file
rm dbs/site_settings.py
mv dbs/site_settings-production.py site_settings

# move wsgi to document root
mv dbs/wsgi.py htdocs/

# build python package
%{__python} setup.py build


%install
# install python package
%{__python} setup.py install --skip-build --root %{buildroot}

# install config file as target of site_settings.py symlink
install -p -D -m 0644 site_settings \
    %{buildroot}%{dbs_confdir}/site_settings
ln -s %{dbs_confdir}/site_settings \
    %{buildroot}%{python_sitelib}/dbs/site_settings.py

# install commandline interface with bash completion
install -p -D -m 0755 manage.py %{buildroot}%{_bindir}/dbs
install -p -D -m 0644 dbs_bash_completion \
    %{buildroot}%{_sysconfdir}/bash_completion.d/dbs_bash_completion

# install httpd config file and wsgi config file
install -p -D -m 0644 conf/httpd/dbs.conf \
    %{buildroot}%{httpd_confdir}/dbs.conf
install -p -D -m 0644 htdocs/wsgi.py \
    %{buildroot}%{dbs_statedir}/htdocs/wsgi.py

# install worker unit file
install -p -D -m 0644 conf/systemd/dbs-worker.service %{buildroot}%{_unitdir}/dbs-worker.service

# install directories for static content and site media
install -p -d -m 0775 htdocs/static \
    %{buildroot}%{dbs_statedir}/htdocs/static
install -p -d -m 0775 htdocs/media \
    %{buildroot}%{dbs_statedir}/htdocs/media

# install separate directory for sqlite db
install -p -d -m 0775 data \
     %{buildroot}%{dbs_statedir}/data

# remove .po files
find %{buildroot} -name "*.po" | xargs rm -f


%pre
# add the dbs user
/usr/sbin/useradd -c "DBuildService" -s /sbin/nologin -r -d %{dbs_statedir} dbs 2> /dev/null || :

%post
# create secret key
if [ ! -e       %{dbs_statedir}/secret_key ]; then
    touch       %{dbs_statedir}/secret_key
    chown dbs   %{dbs_statedir}/secret_key
    chgrp dbs   %{dbs_statedir}/secret_key
    chmod 0400  %{dbs_statedir}/secret_key
    dd bs=1k of=%{dbs_statedir}/secret_key if=/dev/urandom count=5
fi

# install / update database
dbs syncdb --noinput || :


%posttrans server
# link default certificate
if [ ! -e               %{_sysconfdir}/pki/tls/certs/dbs.crt ]; then
    ln -s localhost.crt %{_sysconfdir}/pki/tls/certs/dbs.crt
fi

# link default private key
if [ ! -e               %{_sysconfdir}/pki/tls/private/dbs.key ]; then
    ln -s localhost.key %{_sysconfdir}/pki/tls/private/dbs.key
fi

# link default chain file
if [ ! -e               %{_sysconfdir}/pki/tls/certs/dbs.CA.crt ]; then
    ln -s localhost.crt %{_sysconfdir}/pki/tls/certs/dbs.CA.crt
fi

# allow httpd read from htdocs and secret_key
chcon    -t httpd_sys_content_t /var/lib/dbs/secret_key
chcon    -t httpd_sys_content_t /var/lib/dbs/htdocs
chcon    -t httpd_sys_content_t /var/lib/dbs/htdocs/wsgi.py*
chcon -R -t httpd_sys_content_t /var/lib/dbs/htdocs/static

# allow httpd write to data and media
chcon -R -t httpd_sys_rw_content_t /var/lib/dbs/data
chcon -R -t httpd_sys_rw_content_t /var/lib/dbs/htdocs/media

# allow httpd network connect
setsebool httpd_can_network_connect on

# collect static files
dbs collectstatic --noinput || :

# restart httpd
test -f /etc/sysconfig/dbs-disable-posttrans || \
    /bin/systemctl try-restart httpd.service >/dev/null 2>&1 || :


%post worker
# add user dbs to group docker
usermod -a -G docker dbs || :

# run systemd stuff
%systemd_post dbs-worker.service


%preun worker
# run systemd stuff
%systemd_preun dbs-worker.service


%postun worker
# run systemd stuff
%systemd_postun


%files
%doc README.md LICENSE
%{_bindir}/dbs
%{_sysconfdir}/bash_completion.d/dbs_bash_completion
%config(noreplace) %{dbs_confdir}/site_settings
%attr(775,root,dbs) %dir %{dbs_statedir}/data
%{python_sitelib}/dbs
%{python_sitelib}/dbs-%{version}-py2.*.egg-info


%files server
%config(noreplace) %{httpd_confdir}/dbs.conf
%{dbs_statedir}/htdocs/wsgi.py*
%attr(755,root,root)           %dir %{dbs_statedir}/htdocs/static
%attr(775,root,dbs) %dir %{dbs_statedir}/htdocs/media


%files worker
%doc README-worker.md
%{_unitdir}/dbs-worker.service


%changelog
* Mon Nov 10 2014 Tomas Tomecek <ttomecek@redhat.com> 0.2-1
- Better task list (thrcka@redhat.com)
- Enable task list (thrcka@drone-x240.localdomain)
- api,build: store list of rpms in DB (ttomecek@redhat.com)
- implement new api system (ttomecek@redhat.com)
- api: implement invalidation (ttomecek@redhat.com)
- api: implement move image, store data in DB (ttomecek@redhat.com)
- implement rebuild (ttomecek@redhat.com)
- import all models the same way (jdornak@redhat.com)
- default values for Task.status and Image.status (jdornak@redhat.com)
- new model dockerfile; store df in db after build (ttomecek@redhat.com)
- replace docker-io with docker (jdornak@redhat.com)

* Mon Nov 03 2014 Jakub Dorňák <jdornak@redhat.com> 0.1-1
- new package built with tito

* Wed Oct 22 2014 Jakub Dorňák <jdornak@redhat.com> - 0.1-1
- Initial package

