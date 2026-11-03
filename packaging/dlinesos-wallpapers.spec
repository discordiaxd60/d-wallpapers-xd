Name:           dlinesos-wallpapers
Version:        1.0
Release:        %{release_number}%{?dist}
Summary:        Official wallpapers for D-LinesOS-XD
License:        GPL-3.0-only
BuildArch:      noarch
Source0:        %{name}-%{version}.tar.gz

%description
The official wallpaper collection for D-LinesOS-XD.

%prep
%setup -q -n %{name}-%{version}

%build

%install
mkdir -p %{buildroot}%{_datadir}/wallpapers/dlinesos
cp -a src-wallpapers/. %{buildroot}%{_datadir}/wallpapers/dlinesos/

%files
%license LICENSE
%{_datadir}/wallpapers/dlinesos/
