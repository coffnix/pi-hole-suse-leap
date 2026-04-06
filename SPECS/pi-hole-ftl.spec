#
# spec file for package pi-hole-ftl
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

%define _lto_cflags %{nil}

Name:           pi-hole-ftl
Version:        6.6
Release:        1.1
Summary:        Network-wide ad blocking via your own Linux hardware
License:        EUPL-1.1
Group:          System/Management
Url:            https://pi-hole.net/

# https://github.com/pi-hole/FTL
Source0:        %{name}-%{version}.tar.xz
# https://raw.githubusercontent.com/pi-hole/pi-hole/development-v6/advanced/Templates/pihole-FTL.systemd
Source1:        pihole-ftl.service
Source2:        pihole-FTL.conf.in
Source3:        permissions
Source4:        rpmlintrc
Source6:        override.conf
# https://github.com/pi-hole/pi-hole/blob/master/advanced/06-rfc6761.conf
Source9:        06-rfc6761.conf

Patch1:         001_%{name}_fix_warnings_as_errors.patch
Patch2:         002_%{name}_version.patch
Patch3:         003_%{name}_fix_build_mbedtls_3.5.6.patch
Patch4:         004_pi-hole-ftl_fix_build_with_nettle4.patch
Patch5:			005_pi-hole-ftl_fix_build_with_nettle4_sha256.patch
Patch6:			006_pi-hole-ftl_fix_build_with_nettle4_dnssec.patch

BuildRequires:  cmake
BuildRequires:  libnettle-devel >= 3.9
BuildRequires:  pkgconfig(libidn2)
BuildRequires:  libidn2
BuildRequires:  pkgconfig(zlib)
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  sqlite3-devel
BuildRequires:  gmp-devel
BuildRequires:  mbedtls-devel
BuildRequires:  systemd-rpm-macros
BuildRequires:  xz
BuildRequires:  vim
BuildRequires:  libunistring-devel

PreReq:         permissions
Requires:       pi-hole >= 6.0
Requires:       user(pihole) group(pihole)
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
%systemd_requires

%description
FTLDNS™ (pihole-FTL) provides an interactive API and also generates statistics for Pi-hole®'s Web interface.

* Fast: stats are read directly from memory by coupling our codebase closely with dnsmasq
* Versatile: upstream changes to dnsmasq can quickly be merged in without much conflict
* Lightweight: runs smoothly with minimal hardware and software requirements such as Raspberry Pi Zero
* Interactive: our API can be used to interface with your projects
* Insightful: stats normally reserved inside of dnsmasq are made available so you can see what's really happening on your network

%prep
%autosetup -p1 -n %{name}-%{version}

# Remove comments from pihole-FTL.conf to cause pihole bash script behave properly.
sed '/^;/d' %{S:2} > pihole-FTL.conf

%build
export CC=/usr/bin/gcc-15
export CXX=/usr/bin/g++-15
export NO_BRP_STALE_LINK_ERROR=yes
%cmake \
  -DUSE_MBED_TLS=ON \
  -DUSE_READLINE=ON \
  -DCMAKE_C_COMPILER=/usr/bin/gcc-15 \
  -DCMAKE_CXX_COMPILER=/usr/bin/g++-15

%cmake_build

%install
export NO_BRP_STALE_LINK_ERROR=yes
%cmake_install

install -D -m 0644 %{S:1} %{buildroot}%{_unitdir}/%{name}.service
install -d -m 0775 %{buildroot}%{_datadir}/pi-hole/
install -D -m 0644 pihole-FTL.conf %{buildroot}%{_sysconfdir}/pihole/pihole-FTL.conf
install -D -m 0644 %{S:3} %{buildroot}%{_sysconfdir}/permissions.d/%{name}
install -d -m 0775 %{buildroot}/var/log/pihole
install -d -m 0775 %{buildroot}%{_sysconfdir}/dnsmasq.d/
install -D -m 0644 %{S:9} %{buildroot}%{_sysconfdir}/dnsmasq.d/06-rfc6761.conf

# create tmpfile conf
install -d -m 0755 %{buildroot}%{_tmpfilesdir}
echo "d /run/pihole 0750 pihole pihole" > %{buildroot}%{_tmpfilesdir}/%{name}.conf

%if 0%{?suse_version} <= 1600
# SUSE policy wants to have this symlink.
install -d -m 0755 %{buildroot}%{_sbindir}
ln -s service %{buildroot}%{_sbindir}/rc%{name}
%endif

# Nice-Level
install -d -m 0755 %{buildroot}%{_unitdir}/%{name}.service.d
install -m 0644 %{SOURCE6} %{buildroot}%{_unitdir}/%{name}.service.d/override.conf

%pre
%service_add_pre %{name}.service

%post
%tmpfiles_create %{_tmpfilesdir}/%{name}.conf
%service_add_post %{name}.service
%set_permissions /usr/bin/pihole-FTL

# Disable the DNSStubListener to unbind it from port 53
# Note that this breaks dns functionality on host until FTL is up and running
if [ ! -d /etc/systemd/resolved.conf.d ]; then
  mkdir -p /etc/systemd/resolved.conf.d
fi

if [ ! -f /etc/systemd/resolved.conf.d/90-pi-hole-disable-stub-listener.conf ]; then
cat > /etc/systemd/resolved.conf.d/90-pi-hole-disable-stub-listener.conf << EOF
[Resolve]
DNSStubListener=no
EOF
fi

if command -v systemctl >/dev/null 2>&1; then
  systemctl reload-or-restart systemd-resolved || true
fi

if [ -x /usr/bin/pihole ]; then
  /usr/bin/pihole -g || true
fi

%preun
%service_del_preun %{name}.service

%postun
%service_del_postun %{name}.service

%verifyscript
%verify_permissions -e /usr/bin/pihole-FTL

%files
%defattr(-,root,root)
%license LICENSE
%verify(not user) %attr(0755, root, root) %{_bindir}/pihole-FTL
%{_unitdir}/%{name}.service
%dir %{_unitdir}/%{name}.service.d
%{_unitdir}/%{name}.service.d/override.conf
%config(noreplace) %attr(0644, pihole, pihole) %{_sysconfdir}/pihole/pihole-FTL.conf
%attr(0755, root, root) %dir /var/log/pihole
%config %{_sysconfdir}/permissions.d/pi-hole-ftl
%{_tmpfilesdir}/%{name}.conf
%if 0%{?suse_version} <= 1600
%{_sbindir}/rc%{name}
%endif
%dir %{_datadir}/pi-hole
%dir %{_sysconfdir}/dnsmasq.d
%config(noreplace) %{_sysconfdir}/dnsmasq.d/06-rfc6761.conf
%ghost %attr(0750,pihole,pihole) /run/pihole

%changelog
