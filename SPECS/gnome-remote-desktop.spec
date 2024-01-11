%global systemd_unit gnome-remote-desktop.service

%global tarball_version %%(echo %{version} | tr '~' '.')

%if 0%{?rhel} >= 9
%global bundle_libvncserver 1
%global enable_rdp 0
%else
%global bundle_libvncserver 0
%global enable_rdp 1
%endif

%global libvncserver_name LibVNCServer
%global libvncserver_version 0.9.13

Name:           gnome-remote-desktop
Version:        40.0
Release:        10%{?dist}
Summary:        GNOME Remote Desktop screen share service

License:        GPLv2+
URL:            https://gitlab.gnome.org/jadahl/gnome-remote-desktop
Source0:        https://download.gnome.org/sources/gnome-remote-desktop/40/%{name}-%{tarball_version}.tar.xz
Source1:        https://github.com/LibVNC/libvncserver/archive/refs/tags/%{libvncserver_name}-%{libvncserver_version}.tar.gz

### gnome-remote-desktop patches
# Adds encryption support (requires patched LibVNCServer)
Patch0:         gnutls-anontls.patch

# Backport upstream leak fix (rhbz#1951129)
Patch1:         0001-pipewire-stream-Don-t-leak-GSource-s.patch

### LibVNCServer patches
## TLS security type enablement patches
# https://github.com/LibVNC/libvncserver/pull/234
Patch1000: 0001-libvncserver-Add-API-to-add-custom-I-O-entry-points.patch
Patch1001: 0002-libvncserver-Add-channel-security-handlers.patch
# https://github.com/LibVNC/libvncserver/commit/87c52ee0551b7c4e76855d270d475b9e3039fe08
Patch1002: 0003-libvncserver-auth-don-t-keep-security-handlers-from-.patch
# Fix crash on all runs after the first
# https://github.com/LibVNC/libvncserver/pull/444
# https://bugzilla.redhat.com/show_bug.cgi?id=1882718
Patch1003: 0004-zlib-Clear-buffer-pointers-on-cleanup-444.patch
# Fix another crasher
# https://gitlab.gnome.org/GNOME/gnome-remote-desktop/-/issues/45
# https://bugzilla.redhat.com/show_bug.cgi?id=1882718
Patch1004: 0001-libvncserver-don-t-NULL-out-internal-of-the-default-.patch

## downstream patches
Patch2000: libvncserver-LibVNCServer-0.9.13-system-crypto-policy.patch
Patch2001: libvncserver-LibVNCServer-0.9.13-static-library-link.patch

## Don't compile SHA1 support
Patch2100: 0001-crypto-Don-t-compile-SHA1-support-when-Websockets-ar.patch


BuildRequires:  git
BuildRequires:  gcc
BuildRequires:  meson >= 0.36.0
BuildRequires:  pkgconfig
BuildRequires:  pkgconfig(cairo)
BuildRequires:  pkgconfig(glib-2.0) >= 2.32
BuildRequires:  pkgconfig(gio-unix-2.0) >= 2.32
BuildRequires:  pkgconfig(libpipewire-0.3) >= 0.3.0
%if 0%{?enable_rdp}
BuildRequires:  pkgconfig(freerdp2)
BuildRequires:  pkgconfig(winpr2)
BuildRequires:  pkgconfig(fuse3)
%endif
BuildRequires:  pkgconfig(xkbcommon)
BuildRequires:  pkgconfig(libsecret-1)
BuildRequires:  pkgconfig(libnotify)
BuildRequires:  pkgconfig(gnutls)
%if 0%{?bundle_libvncserver}
BuildRequires:  cmake
BuildRequires:  lzo-devel
BuildRequires:  lzo-minilzo
%else
BuildRequires:  pkgconfig(libvncserver) >= 0.9.11-7
%endif

%{?systemd_requires}
BuildRequires:  systemd

Requires:       pipewire >= 0.3.0

Obsoletes:      vino < 3.22.0-21
%if 0%{?bundle_libvncserver}
Provides:       bundled(libvncserver) = %{libvncserver_version}
%endif

%description
GNOME Remote Desktop is a remote desktop and screen sharing service for the
GNOME desktop environment.


%prep

## Setup libvncserver

%if 0%{?bundle_libvncserver}
%setup -b 1 -n libvncserver-%{libvncserver_name}-%{libvncserver_version}
%patch1000 -p1 -b .tls-1
%patch1001 -p1 -b .tls-2
%patch1002 -p1 -b .handlers
%patch1003 -p1 -b .pointers
%patch1004 -p1 -b .cursor_null
%patch2000 -p1 -b .crypto_policy
%patch2001 -p1 -b .static
%patch2100 -p1 -b .no-sha1

# Nuke bundled minilzo
rm -fv common/lzodefs.h common/lzoconf.h commmon/minilzo.h common/minilzo.c

# Fix encoding
for file in ChangeLog ; do
    mv ${file} ${file}.OLD && \
    iconv -f ISO_8859-1 -t UTF8 ${file}.OLD > ${file} && \
    touch --reference ${file}.OLD $file
done
%endif

## Setup gnome-remote-desktop

%setup -n %{name}-%{tarball_version}
%patch0 -p1
%patch1 -p1


%build

## Build libvncserver

%if 0%{?bundle_libvncserver}
pushd ../libvncserver-%{libvncserver_name}-%{libvncserver_version}
mkdir -p %{_builddir}/libvncserver/
%global libvncserver_install_dir %{buildroot}%{_builddir}/libvncserver
%cmake \
  -DCMAKE_INSTALL_PREFIX=%{libvncserver_install_dir} \
  -DINCLUDE_INSTALL_DIR=%{libvncserver_install_dir}/include \
  -DLIB_INSTALL_DIR:PATH=%{libvncserver_install_dir}/%{_lib} \
  -DSYSCONF_INSTALL_DIR=%{libvncserver_install_dir}/etc \
  -DWITH_FFMPEG=OFF -DWITH_GTK=OFF -DWITH_OPENSSL=OFF -DWITH_GNUTLS=ON \
  -DWITH_SDL=OFF -DWITH_X11=OFF -DWITH_WEBSOCKETS=OFF \
  -DLIBVNCSERVER_WITH_WEBSOCKETS=OFF -DBUILD_SHARED_LIBS=OFF
%cmake_build
%__cmake --install "%{__cmake_builddir}"
popd
%endif

## Build gnome-remote-desktop

%if 0%{?bundle_libvncserver}
%global pkg_config_path_override --pkg-config-path %{buildroot}/%{_builddir}/libvncserver/%{_lib}/pkgconfig
%endif

%if 0%{?enable_rdp}
%global rdp_configuration -Drdp=true
%else
%global rdp_configuration -Drdp=false
%endif

%meson %{?pkg_config_path_override} %{rdp_configuration}
%meson_build


%install
%meson_install

%if 0%{?bundle_libvncserver}
pushd ../libvncserver-%{libvncserver_name}-%{libvncserver_version}
cp COPYING %{_builddir}/%{name}-%{tarball_version}/COPYING.libvncserver
popd
%endif


%post
%systemd_user_post %{systemd_unit}


%preun
%systemd_user_preun %{systemd_unit}


%postun
%systemd_user_postun_with_restart %{systemd_unit}


%files
%license COPYING
%if 0%{?bundle_libvncserver}
%license COPYING.libvncserver
%endif
%doc README
%{_libexecdir}/gnome-remote-desktop-daemon
%{_userunitdir}/gnome-remote-desktop.service
%{_datadir}/glib-2.0/schemas/org.gnome.desktop.remote-desktop.gschema.xml
%{_datadir}/glib-2.0/schemas/org.gnome.desktop.remote-desktop.enums.xml


%changelog
* Wed Jul 19 2023 Jonas Ådahl <jadahl@redhat.com> - 40.0-10
- Don't compile in SHA1 support again
  Resolves: #2223925

* Wed Jul 19 2023 Jonas Ådahl <jadahl@redhat.com> - 40.0-9
- Bump version number
  Related: rhbz#2188174

* Wed Apr 19 2023 Yaakov Selkowitz <yselkowi@redhat.com> - 40.0-8
- Do not provide libvncserver.so.1
  Resolves: rhbz#2188174

* Mon Oct 25 2021 Jonas Ådahl <jadahl@redhat.com> - 40.0-7
- Don't compile in SHA1 support
  Resolves: #1936594

* Mon Aug 09 2021 Mohan Boddu <mboddu@redhat.com> - 40.0-6
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Tue Jun 15 2021 Jonas Ådahl <jadahl@redhat.com> - 40.0-5
- Backport leak fix
  Resolves: #1951129

* Mon May 17 2021 Ondrej Holy <oholy@redhat.com> - 40.0-4
- Rebuild for updated FreeRDP (#1951123).

* Thu Apr 22 2021 Jonas Ådahl <jadahl@redhat.com> - 40.0-3
- Bundle libvncserver
- Disable RDP support

* Thu Apr 15 2021 Mohan Boddu <mboddu@redhat.com> - 40.0-2
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Mon Mar 22 2021 Kalev Lember <klember@redhat.com> - 40.0-1
- Update to 40.0

* Thu Mar 18 2021 Michael Catanzaro <mcatanzaro@redhat.com> - 40.0~rc-2
- Add Obsoletes: vino

* Mon Mar 15 2021 Kalev Lember <klember@redhat.com> - 40.0~rc-1
- Update to 40.rc

* Thu Mar 04 2021 Jonas Ådahl <jadahl@redhat.com> - 40.0~beta-1
- Bump to 40.beta

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.9-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Mon Sep 14 2020 Jonas Ådahl <jadahl@redhat.com> - 0.1.9-2
- Copy using the right destination stride

* Mon Sep 14 2020 Jonas Ådahl <jadahl@redhat.com> - 0.1.9-1
- Update to 0.1.9
- Backport race condition crash fix
- Rebase anon-tls patches

* Thu Aug 27 2020 Ray Strode <rstrode@redhat.com> - 0.1.8-3
- Fix crash
  Related: #1844993

* Mon Jun 1 2020 Felipe Borges <feborges@redhat.com> - 0.1.8-2
- Fix black screen issue in remote connections on Wayland

* Wed Mar 11 2020 Jonas Ådahl <jadahl@redhat.com> - 0.1.8-1
- Update to 0.1.8

* Tue Jan 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.7-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Mon Mar 4 2019 Jonas Ådahl <jadahl@redhat.com> - 0.1.7-1
- Update to 0.1.7

* Thu Jan 31 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.6-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Tue Oct 2 2018 Jonas Ådahl <jadahl@redhat.com> - 0.1.6-2
- Don't crash when PipeWire disconnects (rhbz#1632781)

* Tue Aug 7 2018 Jonas Ådahl <jadahl@redhat.com> - 0.1.6
- Update to 0.1.6
- Apply ANON-TLS patch
- Depend on pipewire 0.2.2

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Wed May 30 2018 Jonas Ådahl <jadahl@redhat.com> - 0.1.4-1
- Update to new version

* Fri Feb 09 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.1.2-5
- Escape macros in %%changelog

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Tue Aug 29 2017 Jonas Ådahl <jadahl@redhat.com> - 0.1.2-3
- Use %%autosetup
- Install licence file

* Tue Aug 22 2017 Jonas Ådahl <jadahl@redhat.com> - 0.1.2-2
- Remove gschema compilation step as that had been deprecated

* Mon Aug 21 2017 Jonas Ådahl <jadahl@redhat.com> - 0.1.2-1
- Update to 0.1.2
- Changed tabs to spaces
- Added systemd user macros
- Install to correct systemd user unit directory
- Compile gsettings schemas after install and uninstall

* Mon Aug 21 2017 Jonas Ådahl <jadahl@redhat.com> - 0.1.1-1
- First packaged version
