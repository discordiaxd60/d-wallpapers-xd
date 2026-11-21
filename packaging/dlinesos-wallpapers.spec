Name:           dlinesos-wallpapers
Version:        1.0
Release:        %{release_number}%{?dist}
Summary:        Official wallpapers for D-LinesOS-XD
License:        GPL-3.0-only
BuildArch:      noarch
BuildRequires:  python3
Source0:        %{name}-%{version}.tar.gz

%description
The official wallpaper collection for D-LinesOS-XD.

%prep
%setup -q -n %{name}-%{version}

%build

%install
mkdir -p %{buildroot}%{_datadir}/wallpapers/dlinesos
cp -a src-wallpapers/. %{buildroot}%{_datadir}/wallpapers/dlinesos/
python3 scripts/install_kde_wallpapers.py \
  --wallpaper-dir %{buildroot}%{_datadir}/wallpapers/dlinesos
python3 scripts/install_kde_wallpapers.py \
  --wallpaper-dir %{buildroot}%{_datadir}/wallpapers/dlinesos --check
install -D -m 644 packaging/desktop-backgrounds/dlinesos-wallpapers.xml \
  %{buildroot}%{_datadir}/gnome-background-properties/dlinesos-wallpapers.xml
install -D -m 644 packaging/desktop-backgrounds/dlinesos-wallpapers.xml \
  %{buildroot}%{_datadir}/cinnamon-background-properties/wallpapers-dlinesos.xml
install -D -m 644 packaging/desktop-backgrounds/dlinesos-wallpapers.xml \
  %{buildroot}%{_datadir}/mate-background-properties/dlinesos-wallpapers.xml

%files
%license LICENSE
%{_datadir}/wallpapers/dlinesos/
%{_datadir}/wallpapers/dlinesos-*/
%{_datadir}/gnome-background-properties/dlinesos-wallpapers.xml
%{_datadir}/cinnamon-background-properties/wallpapers-dlinesos.xml
%{_datadir}/mate-background-properties/dlinesos-wallpapers.xml
