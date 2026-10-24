This repository contains the official D-LinesOS-XD wallpapers and **D-Gallery-XD**, a Linux desktop app for browsing and setting them. New wallpaper metadata and images are published in the APT packages when changes land on `main`.

## APT repository

The GitHub Pages workflow publishes the `dlinesos-wallpapers` and `d-gallery-xd` packages at:

```text
https://discordiaxd60.github.io/d-wallpapers-xd/
```

Add the repository and install the gallery on Debian or Ubuntu:

```sh
echo "deb [trusted=yes] https://discordiaxd60.github.io/d-wallpapers-xd/ ./" \
  | sudo tee /etc/apt/sources.list.d/d-gallery-xd.list
sudo apt update
sudo apt install d-gallery-xd
```

The repository currently publishes unsigned package indexes; `trusted=yes` is required for APT to accept them. Only add this source if you trust this project. Once installed, `sudo apt update && sudo apt upgrade` picks up newer wallpaper collections and app releases.

## D-Gallery-XD

Launch **D-Gallery-XD** from your applications menu. **Home** shows wallpapers by upload date; **All** shows a compact grid. Select an image in the grid or search results to open its Home banner. **Set Wallpaper** works on GNOME and KDE Plasma.

Wallpaper dates use the first Git commit that added each image. Descriptions are intentionally blank in `src-wallpapers/wallpapers.json` until supplied; the app shows a placeholder for empty descriptions. Add new wallpaper metadata to that file when adding images.

The wallpaper collection is distributed here as its official package. Please do not republish the wallpapers elsewhere.
