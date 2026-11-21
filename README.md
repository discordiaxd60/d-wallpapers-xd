# D-LinesOS-XD Wallpapers

The official wallpaper collection for **D-LinesOS-XD**. Browse the images in [`src-wallpapers`](src-wallpapers) and enjoy them on your desktop.

## Install with APT

Add the repository to your APT sources:

```sh
echo "deb [trusted=yes] https://discordiaxd60.github.io/d-wallpapers-xd/ ./" \
  | sudo tee /etc/apt/sources.list.d/dlinesos-wallpapers.list
```

Then install the wallpaper collection:

```sh
sudo apt update
sudo apt install dlinesos-wallpapers
```

The wallpapers are installed under `/usr/share/wallpapers/dlinesos`. To receive future collection updates:

```sh
sudo apt update
sudo apt upgrade
```

> **Note:** This APT repository currently uses unsigned packages. Only add it if you trust this project.

## Install on Fedora with DNF

Add the Fedora repository:

```sh
sudo tee /etc/yum.repos.d/dlinesos-wallpapers.repo >/dev/null <<'EOF'
[dlinesos-wallpapers]
name=D-LinesOS-XD Wallpapers
baseurl=https://discordiaxd60.github.io/d-wallpapers-xd/fedora/
enabled=1
gpgcheck=0
repo_gpgcheck=0
EOF
```

Install the wallpaper collection:

```sh
sudo dnf install dlinesos-wallpapers
```

The wallpapers are installed under `/usr/share/wallpapers/dlinesos`. To receive future collection updates:

```sh
sudo dnf upgrade dlinesos-wallpapers
```

> **Note:** The Fedora RPMs and repository metadata are currently unsigned. Only add this repository if you trust this project.

## Other Linux distributions

These installation options are **Untested yet**.

### Arch Linux and Manjaro (Untested yet)

Install the build tools, clone the repository, and build the package locally:

```sh
sudo pacman -S --needed base-devel git
git clone https://github.com/discordiaxd60/d-wallpapers-xd.git
cd d-wallpapers-xd/packaging/arch
makepkg -si
```

### openSUSE (Untested yet)

Use the Fedora RPM repository with Zypper. Its metadata and RPMs are unsigned, and this command disables GPG checks; only use it if you trust this project:

```sh
sudo zypper addrepo --refresh --no-gpgcheck \
  https://discordiaxd60.github.io/d-wallpapers-xd/fedora/ dlinesos-wallpapers
sudo zypper refresh
sudo zypper install dlinesos-wallpapers
```

### Other distributions (Untested yet)

Clone the repository and use the distro-neutral installer:

```sh
git clone https://github.com/discordiaxd60/d-wallpapers-xd.git
cd d-wallpapers-xd
sudo sh scripts/install-wallpapers.sh
```

To install just for your user, pass a destination under your home directory instead:

```sh
sh scripts/install-wallpapers.sh "$HOME/.local/share/wallpapers/dlinesos"
```

The generic installer requires Python 3 to generate KDE Plasma's per-wallpaper packages.

## Desktop environment integration

The APT, Fedora (including openSUSE), Arch, and default system-wide manual installations register the collection in the background pickers for **GNOME**, **Cinnamon**, and **MATE**. KDE Plasma gets a separate wallpaper package for each image, so its picker can show each title and credited author. In GNOME, open **Settings → Background**; in Cinnamon, **System Settings → Background**; in MATE, **Control Center → Appearance → Background**.

XFCE, LXQt, and other desktops without a shared wallpaper-catalog format can still use the images: choose `/usr/share/wallpapers/dlinesos` in the desktop's wallpaper folder picker, or browse to an image. User-local and custom-destination installs should be selected manually.

## Wallpaper collection

New wallpapers are published through the APT and Fedora repositories as the collection grows.

Please enjoy these wallpapers for personal use, but do not republish them elsewhere.

## Wallpaper metadata

[`src-wallpapers/catalog.json`](src-wallpapers/catalog.json) contains searchable metadata for every image, including its display title, author, description, tags, dimensions, aspect ratio, orientation, format, and MIME type. Authors are included where credited; unknown authors and image-specific licenses are left `null` rather than guessed. Display titles are cleaned up independently of the original filenames. The catalog is also installed at `/usr/share/wallpapers/dlinesos/catalog.json`.

For example, use `jq` to find wallpapers by a tag:

```sh
jq '.images[] | select(.tags | index("gradient"))' src-wallpapers/catalog.json
```
