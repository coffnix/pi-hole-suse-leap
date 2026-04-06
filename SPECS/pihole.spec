#
# spec file for package pi-hole
#
# Copyright (c) 2020 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.
#
# Please submit bugfixes or comments via http://bugs.opensuse.org/
#

Name:           pi-hole
Version:        6.4.1
Release:        1.1
Summary:        A black hole for Internet advertisements
License:        EUPL-1.1
Group:          Productivity/Networking/Other
Url:            https://pi-hole.net/
# https://github.com/pi-hole/pi-hole
Source0:        %{name}-%{version}.tar.xz
Source5:        system-user-pihole.conf
# The adlists.list file is created from basic-install.sh script
Source7:        adlists.list
# dns-servers.conf seems to be needed at least by AdminLTE, for configuration.
Source8:        dns-servers.conf
Source12:       pihole_unbound.conf
# https://docs.pi-hole.net/guides/dns/unbound/
Source13:       99-edns.conf
Source14:       %{name}.sudo
Patch10:        010_pi-hole_logrotate_config.patch

BuildRequires:  sysuser-tools
BuildRequires:  sudo
BuildRequires:  unbound
BuildRequires:  xz
%if 0%{?suse_version} > 1500
%ifarch aarch64
BuildRequires:  -post-build-checks
%endif
%endif

Requires:       cronie
Requires:       findutils
Requires:       sudo
Requires:       unzip
Requires:       psmisc
Requires:       libcap2
Requires:       ncat
Requires:       jq
Requires:       lshw
Requires:       curl
Requires:       sqlite3
Requires:       bind-utils
Requires:       netcat-openbsd
Requires:       pi-hole-ftl
Requires:       pi-hole-web
Requires:       logrotate
Requires:       user(pihole) group(pihole)
Requires(post): %fillup_prereq
Requires(post): iproute2

BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch
Recommends:     pi-hole-bash-completion

%description
The Pi-hole® is a DNS sinkhole that protects your devices from unwanted content, without installing any client-side software.

* Easy-to-install: our versatile installer walks you through the process, and takes less than ten minutes
* Resolute: content is blocked in non-browser locations, such as ad-laden mobile apps and smart TVs
* Responsive: seamlessly speeds up the feel of everyday browsing by caching DNS queries
* Lightweight: runs smoothly with minimal hardware and software requirements
* Robust: a command line interface that is quality assured for interoperability
* Insightful: a beautiful responsive Web Interface dashboard to view and control your Pi-hole
* Versatile: can optionally function as a DHCP server, ensuring all your devices are protected automatically
* Scalable: capable of handling hundreds of millions of queries when installed on server-grade hardware
* Modern: blocks ads over both IPv4 and IPv6
* Free: open source software which helps ensure you are the sole person in control of your privacy

%package -n system-user-pihole
Summary:        System user and group pihole
%if %{with systemd}
%{?sysusers_requires}
%endif

%description -n system-user-pihole
System user and group used by pi-hole

%package bash-completion
Summary:        Bash Completion for %{name}
Group:          System/Management
Requires:       %{name} = %{version}
Supplements:    packageand(%{name}:bash-completion)
BuildArch:      noarch

%description bash-completion
Bash command line completion support for %{name} .

%package config-unbound
Summary:        Unbound configuration for %{name}
Group:          System/Management
Requires:       %{name} = %{version}
Requires:       unbound
Supplements:    packageand(%{name}:config-unbound)
BuildArch:      noarch

%description config-unbound
Unbound configuration if you want to use unbound as DNS for %{name}.

%prep
%autosetup -n %{name}-%{version} -p1

# Move datadir
find . -type f -exec sed -i 's/\/opt\/\pihole/\/usr\/share\/pi-hole/g' {} +
# Fix shebang
find . -type f -exec sed -i 's|#!/bin/sh|#!/bin/bash|g' {} +
find . -type f -exec sed -i 's/\/usr\/bin\/env sh/\/bin\/bash/g' {} +
find . -type f -exec sed -i 's/\/usr\/bin\/env bash/\/bin\/bash/g' {} +
# Move bindir
find . -type f -exec sed -i 's/\/usr\/local\/bin/\/usr\/bin/g' {} +
# Move gitdir
find . -type f -exec sed -i 's/\/etc\/\.pihole/\/usr\/share\/pi-hole/g' {} +
# service to systemctl
sed -i 's|service pihole-FTL restart|systemctl restart pihole-ftl|' pihole
# Other path fixes
find . -type f -exec sed -i 's|/automated install/basic-install.sh|/basic-install.sh|' {} +
sed -i 's|advanced/Scripts/database_migration/gravity-db.sh|database_migration/gravity-db.sh|' gravity.sh
sed -i 's|advanced/Templates/gravity.db.sql|database_migration/templates/gravity.db.sql|' gravity.sh
sed -i 's|advanced/Templates/gravity_copy.sql|database_migration/templates/gravity_copy.sql|' gravity.sh
sed -i 's|advanced/Scripts/database_migration/gravity|database_migration/gravity|' advanced/Scripts/database_migration/gravity-db.sh
# Have logs in /var/log/pihole dir.
sed -i "s|/var/log/pihole.log|/var/log/pihole/pihole.log|" advanced/Templates/logrotate
sed -i "s|/var/log/pihole-FTL.log|/var/log/pihole/pihole-FTL.log|" advanced/Templates/logrotate

%build
%sysusers_generate_pre %{SOURCE5} pihole

%install
# Manual install of Pi-hole scripts, configs and man pages
install -Dm0755 pihole %{buildroot}%{_bindir}/pihole
install -d -m0755 %{buildroot}%{_datadir}/%{name}
install -Dm0644 advanced/Scripts/COL_TABLE %{buildroot}%{_datadir}/%{name}/COL_TABLE
install -Dm0755 "automated install"/basic-install.sh %{buildroot}%{_datadir}/%{name}/basic-install.sh
install -Dm0755 gravity.sh %{buildroot}%{_datadir}/%{name}/gravity.sh
install -Dm0755 advanced/Scripts/*.sh %{buildroot}%{_datadir}/%{name}/
install -Dm0640 advanced/Templates/logrotate %{buildroot}%{_sysconfdir}/logrotate.d/pihole
install -d -m 0755 %{buildroot}%{_datadir}/%{name}/database_migration/gravity
install -d -m 0755 %{buildroot}%{_datadir}/%{name}/database_migration/templates
install -Dm0755 advanced/Scripts/database_migration/gravity-db.sh %{buildroot}%{_datadir}/%{name}/database_migration/gravity-db.sh
install -Dm0644 advanced/Scripts/database_migration/gravity/*.sql %{buildroot}%{_datadir}/%{name}/database_migration/gravity/
install -Dm0644 advanced/Templates/*.sql %{buildroot}%{_datadir}/%{name}/database_migration/templates/
install -d -m 0755 %{buildroot}%{_sysconfdir}/sudoers.d/
install -Dm0640 %{S:14} %{buildroot}%{_sysconfdir}/sudoers.d/pihole
install -Dm0644 /dev/null %{buildroot}%{_sysconfdir}/pihole/dhcp.leases

# Bash Completion
install -Dm0644 advanced/bash-completion/pihole.bash %{buildroot}%{_datadir}/bash-completion/completions/pihole
install -Dm0644 advanced/bash-completion/pihole-ftl.bash %{buildroot}%{_datadir}/bash-completion/completions/pihole-ftl

# Unbound Configuration
mkdir -p %{buildroot}%{_sysconfdir}/unbound/conf.d
install -Dm0640 %{S:12} %{buildroot}%{_sysconfdir}/unbound/conf.d/01-pihole.conf
install -d -m 0755 %{buildroot}%{_sysconfdir}/dnsmasq.d/
install -Dm0644 %{S:13} %{buildroot}%{_sysconfdir}/dnsmasq.d/

# Install man pages
install -Dm0644 manpages/pihole.8 %{buildroot}%{_mandir}/man8/pihole.8

# openSUSE/SUSE specific files
install -d -m 0755 %{buildroot}%{_sysusersdir}
install -m 644 %{S:5} %{buildroot}%{_sysusersdir}/system-user-pihole.conf

# Install advertisement list Url file
install -Dm0644 %{S:7} %{buildroot}%{_sysconfdir}/pihole/adlists.list
install -Dm0644 %{S:8} %{buildroot}%{_sysconfdir}/pihole/dns-servers.conf

%pre -n system-user-pihole -f pihole.pre

%post
%fillup_only -n pihole

%files
%defattr(-,root,root,-)
%doc CONTRIBUTING.md
%license LICENSE
%dir %{_sysconfdir}/dnsmasq.d
%attr(0775, pihole, pihole) %dir %{_sysconfdir}/pihole
%config(noreplace) %attr(0664, pihole, pihole) %{_sysconfdir}/pihole/adlists.list
%config(noreplace) %attr(0664, pihole, pihole) %{_sysconfdir}/pihole/dns-servers.conf
%attr(0664, pihole, www) %{_sysconfdir}/pihole/dhcp.leases
%attr(0640, root, root) %config %{_sysconfdir}/logrotate.d/pihole
%config(noreplace) %attr(0640, root, root) %{_sysconfdir}/sudoers.d/pihole
%{_bindir}/pihole
%{_mandir}/man8/pihole.8*
%attr(0775, pihole, pihole) %dir %{_datadir}/%{name}
%attr(0775, pihole, pihole) %{_datadir}/%{name}/*
%ghost %attr(0775, pihole, pihole) %dir /run/pihole
%ghost %attr(0664, pihole, pihole) /etc/pihole/gravity*.db

%files -n system-user-pihole
%defattr(-,root,root)
%{_sysusersdir}/system-user-pihole.conf

%files bash-completion
%defattr(-,root,root)
%{_datadir}/bash-completion/completions/pihole
%{_datadir}/bash-completion/completions/pihole-ftl

%files config-unbound
%defattr(-,root,root)
%attr(0775, root, unbound) %dir %{_sysconfdir}/unbound/conf.d
%config(noreplace) %attr(0660, root, unbound) %{_sysconfdir}/unbound/conf.d/01-pihole.conf
%config(noreplace) %attr(0644, root, root) %{_sysconfdir}/dnsmasq.d/99-edns.conf

%changelog
