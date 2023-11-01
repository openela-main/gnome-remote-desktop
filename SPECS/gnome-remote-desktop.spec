%global systemd_unit gnome-remote-desktop.service

Name:           gnome-remote-desktop
Version:        0.1.8
Release:        3%{?dist}
Summary:        GNOME Remote Desktop screen share service

License:        GPLv2+
URL:            https://gitlab.gnome.org/jadahl/gnome-remote-desktop
Source0:        https://gitlab.gnome.org/jadahl/gnome-remote-desktop/uploads/20e4965351cdbd8dc32ff9801e884b91/gnome-remote-desktop-0.1.8.tar.xz

# Fix black screen on Wayland
Patch1:         0001-vnc-pipewire-stream-Handle-stride-mismatch.patch

# Anon TLS encryption support
Patch2:         anon-tls-support.patch

# Don't crash on metadata only buffers (#1847062)
Patch3:         0001-stream-log-a-warning-on-error.patch
Patch4:         0002-vnc-pipewire-stream-Only-try-to-copy-frame-pixels-if.patch
Patch5:         0001-vnc-pipewire-stream-Remove-assert.patch

# Cursor only frame fixes (#1837406)
Patch6:         cursor-only-frame-fixes.patch

BuildRequires:  git
BuildRequires:  gcc
BuildRequires:  meson >= 0.36.0
BuildRequires:  pkgconfig
BuildRequires:  pkgconfig(glib-2.0) >= 2.32
BuildRequires:  pkgconfig(gio-unix-2.0) >= 2.32
BuildRequires:  pkgconfig(libpipewire-0.3) >= 0.3.4
BuildRequires:  pkgconfig(libvncserver) >= 0.9.11-7
BuildRequires:  pkgconfig(libsecret-1)
BuildRequires:  pkgconfig(libnotify)
BuildRequires:  pkgconfig(gnutls)
BuildRequires:  python3-devel

%{?systemd_requires}
BuildRequires:  systemd

Requires:       pipewire >= 0.3.4

%description
GNOME Remote Desktop is a remote desktop and screen sharing service for the
GNOME desktop environment.


%prep
%autosetup -S git


%build
%meson
%meson_build


%install
%meson_install


%post
%systemd_user_post %{systemd_unit}


%preun
%systemd_user_preun %{systemd_unit}


%postun
%systemd_user_postun_with_restart %{systemd_unit}


%files
%license COPYING
%doc README
%{_libexecdir}/gnome-remote-desktop-daemon
%{_userunitdir}/gnome-remote-desktop.service
%{_datadir}/glib-2.0/schemas/org.gnome.desktop.remote-desktop.gschema.xml
%{_datadir}/glib-2.0/schemas/org.gnome.desktop.remote-desktop.enums.xml


%changelog
* Wed Jul 15 2020 Jonas Ådahl <jadahl@redhat.com> - 0.1.8-3
- Backport cursor only frame fixes
  Related: #1837406

* Thu Jun 18 2020 Jonas Ådahl <jadahl@redhat.com> - 0.1.8-2
- Don't crash on metadata only buffers
  Resolves: #1847062

* Wed May 20 2020 Jonas Ådahl <jadahl@redhat.com> - 0.1.8-1
- Rebase to 0.1.8
  Resolves: #1837406

* Wed Nov 27 2019 Jonas Ådahl <jadahl@redhat.com> - 0.1.6-8
- Update patch to handle older libvncserver at build time
  Resolves: #1684729

* Wed Nov 27 2019 Jonas Ådahl <jadahl@redhat.com> - 0.1.6-7
- Handle auth settings changes
  Resolves: #1684729

* Wed Nov 27 2019 Jonas Ådahl <jadahl@redhat.com> - 0.1.6-6
- Fix initial black content issue
  Resolves: #1765448

* Thu May 30 2019 Tomáš Popela <tpopela@redhat.com> - 0.1.6-5
- Bump the version to make gating happy - that's bug 1681618
- Resolves: rhbz#1713330

* Fri May 24 2019 Jonas Ådahl <jadahl@redhat.com> - 0.1.6-4
- Backport password override test helper (rhbz#1713330)

* Thu Jan 3 2019 Jonas Ådahl <jadahl@redhat.com> - 0.1.6-3
- Backport various fixes (rhbz#1659118)

* Mon Oct 1 2018 Jonas Ådahl <jadahl@redhat.com> - 0.1.6-2
- Don't crash when PipeWire disconnects (rhbz#1627469)

* Tue Aug 7 2018 Jonas Ådahl <jadahl@redhat.com> - 0.1.6
- Update to 0.1.6
- Apply ANON-TLS patch
- Depend on pipewire 0.2.2

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
