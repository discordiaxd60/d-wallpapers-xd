#!/bin/sh
set -eu

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)
source_dir="$script_dir/../src-wallpapers"
destination=${1:-/usr/share/wallpapers/dlinesos}

if [ ! -d "$source_dir" ]; then
    printf 'Wallpaper files were not found relative to this script.\n' >&2
    exit 1
fi

install -d "$destination"
cp -a "$source_dir/." "$destination/"

legacy_metadata="$destination/metadata.desktop"
if [ -f "$legacy_metadata" ]; then
    if tr -d '\r' < "$legacy_metadata" | grep -Fqx 'Name=D-LinesOS Wallpapers' &&
        tr -d '\r' < "$legacy_metadata" | grep -Fqx 'X-KDE-PluginInfo-Name=dlinesos'; then
        rm "$legacy_metadata"
    else
        printf 'Cannot register KDE wallpapers: unexpected metadata file at %s\n' "$legacy_metadata" >&2
        exit 1
    fi
fi

legacy_catalog="$destination/catalog.json"
if [ -f "$legacy_catalog" ] &&
    grep -Fqx '  "schema_version": 1,' "$legacy_catalog" &&
    grep -Fqx '  "images": [' "$legacy_catalog"; then
    rm "$legacy_catalog"
fi

remove_generated_packages() {
    package_root=$1
    [ -d "$package_root" ] && [ ! -L "$package_root" ] || return 0

    for package_dir in "$package_root"/dlinesos-*; do
        [ -d "$package_dir" ] && [ ! -L "$package_dir" ] || continue
        package_name=${package_dir##*/}
        package_metadata="$package_dir/metadata.json"
        if [ -f "$package_metadata" ] &&
            grep -Fqx '  "KPackageStructure": "Wallpaper/Images",' "$package_metadata" &&
            grep -Fqx "    \"Id\": \"$package_name\"," "$package_metadata"; then
            rm -r "$package_dir"
        fi
    done
}

remove_generated_packages "$(dirname "$destination")"
legacy_package_root="$destination-kde"
remove_generated_packages "$legacy_package_root"
rmdir "$legacy_package_root" 2>/dev/null || :

if [ "$destination" = /usr/share/wallpapers/dlinesos ]; then
    for legacy_catalog in \
        /usr/share/gnome-background-properties/dlinesos-wallpapers.xml \
        /usr/share/mate-background-properties/dlinesos-wallpapers.xml \
        /usr/share/cinnamon-background-properties/wallpapers-dlinesos.xml
    do
        if [ -f "$legacy_catalog" ] &&
            grep -Fq '<wallpapers>' "$legacy_catalog" &&
            grep -Fq '/usr/share/wallpapers/dlinesos/' "$legacy_catalog"; then
            rm "$legacy_catalog"
        fi
    done
fi
printf 'Installed wallpapers to %s\n' "$destination"
