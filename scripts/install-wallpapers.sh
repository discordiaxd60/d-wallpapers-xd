#!/bin/sh
set -eu

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)
source_dir="$script_dir/../src-wallpapers"
destination=${1:-/usr/share/wallpapers/dlinesos}

if [ ! -f "$source_dir/catalog.json" ] || [ ! -f "$source_dir/metadata.desktop" ]; then
    printf 'Wallpaper files were not found relative to this script.\n' >&2
    exit 1
fi

install -d "$destination"
cp -a "$source_dir/." "$destination/"
if [ "$destination" = /usr/share/wallpapers/dlinesos ]; then
    for properties_dir in \
        /usr/share/gnome-background-properties \
        /usr/share/mate-background-properties
    do
        install -d "$properties_dir"
        install -m 644 "$script_dir/../packaging/desktop-backgrounds/dlinesos-wallpapers.xml" \
            "$properties_dir/dlinesos-wallpapers.xml"
    done
    install -d /usr/share/cinnamon-background-properties
    install -m 644 "$script_dir/../packaging/desktop-backgrounds/dlinesos-wallpapers.xml" \
        /usr/share/cinnamon-background-properties/wallpapers-dlinesos.xml
fi
printf 'Installed wallpapers to %s\n' "$destination"
