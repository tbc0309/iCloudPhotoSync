# Build & Release Guide

## Prerequisites

- **WSL2** with Ubuntu 24.04 (or a native Linux system)
- `/bin/sh` must be **bash**, not dash:
  ```bash
  sudo ln -sf bash /bin/sh
  ```
- Clean Linux PATH (no Windows entries with spaces):
  ```bash
  export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  ```
- Required packages:
  ```bash
  sudo apt-get install build-essential git cmake meson automake autoconf \
      libtool pkg-config python3 python3-pip imagemagick gh
  ```

## Repository Setup (one-time)

Clone the SynoCommunity/spksrc framework and add the fork as remote:

```bash
cd ~
git clone https://github.com/SynoCommunity/spksrc.git
cd spksrc
git remote add fork git@github.com:Euphonique/spksrc.git
```

Install the spksrc toolchain requirements:

```bash
sudo pip3 install -r requirements.txt
```

The iCloud Photo Sync package lives in these directories within spksrc:

| Directory | Purpose |
|---|---|
| `cross/heif-convert/` | HEIC/HEIF conversion tools (libheif 1.18.2) |
| `cross/Lerc/` | Limited Error Raster Compression library |
| `cross/libdeflate/` | Fast deflate/zlib/gzip compression |
| `spk/icloudphotosync/` | The SPK package itself |

## Building an SPK

Build for a specific architecture (e.g. x64 for DSM 7.2):

```bash
cd ~/spksrc
make -C spk/icloudphotosync arch-x64-7.2
```

Common architecture targets:

| Target | NAS Hardware |
|---|---|
| `arch-x64-7.2` | Intel/AMD (most desktop models) |
| `arch-aarch64-7.2` | ARM 64-bit (e.g. DS220j, DS223) |
| `arch-armv7-7.2` | ARM 32-bit (older models) |

The built SPK file appears in:
```
spk/icloudphotosync/packages/icloudphotosync_<arch>_<version>.spk
```

To clean build artifacts and rebuild from scratch:
```bash
make -C spk/icloudphotosync clean
make -C cross/heif-convert clean   # if cross-package changed
```

## Releasing a New Version

### 1. Bump the version

Edit `spk/icloudphotosync/Makefile`:

```makefile
SPK_VERS = 1.5.0      # new version (X.Y.Z: major.minor.bugfix)
SPK_REV  = 1          # reset to 1 for new version, increment for same-version rebuilds
CHANGELOG = ...        # describe what changed
```

### 2. Update the application files

Copy updated source files into `spk/icloudphotosync/src/`:

- `src/bin/` — Python entry points (scheduler.py, sync_runner.py, move_runner.py)
- `src/lib/` — Python library modules and handlers
- `src/lib/vendor/` — Vendored dependencies (pyicloud_ipd, srp, six)
- `src/app/` — DSM web UI (HTML, JS, CGI, icons, translations)
- `src/conf/` — DSM privilege and resource config
- `src/requirements-pure.txt` — Python wheel dependencies

### 3. Build and test

```bash
make -C spk/icloudphotosync arch-x64-7.2
```

Install the resulting `.spk` on a test NAS via **Package Center > Manual Install** and verify:
- Package starts without errors
- Web UI loads at `http://<NAS>:5000/webman/3rdparty/icloudphotosync/`
- iCloud login and 2FA work
- Photo sync runs correctly
- HEIC-to-JPEG conversion works

### 4. Commit and push

```bash
cd ~/spksrc
git checkout -b update/icloudphotosync-<version>
git add spk/icloudphotosync/
git commit -m "icloudphotosync: update to <version>"
git push fork update/icloudphotosync-<version>
```

### 5. Create a Pull Request

```bash
gh pr create --repo SynoCommunity/spksrc \
    --base master \
    --head Euphonique:update/icloudphotosync-<version> \
    --title "icloudphotosync: update to <version>" \
    --body "Summary of changes..."
```

Once merged by SynoCommunity maintainers, the package becomes available in Synology Package Center for all users with the SynoCommunity repository configured.

## Updating Cross-Compilation Dependencies

If you need to update `cross/heif-convert`, `cross/Lerc`, or `cross/libdeflate`:

1. Update `PKG_VERS` in the package's `Makefile`
2. Regenerate checksums in `digests`:
   ```bash
   # Download the new source archive, then:
   sha1sum <archive>
   sha256sum <archive>
   md5sum <archive>
   ```
3. Verify `PLIST` still matches the installed files (build once and check `work-<arch>/install/`)
4. Include the cross-package changes in the same PR

## Troubleshooting

| Problem | Solution |
|---|---|
| `Syntax error: "(" unexpected` | `/bin/sh` is dash, not bash. Run `sudo ln -sf bash /bin/sh` |
| Build fails with Windows path errors | Export clean Linux PATH without Windows entries |
| `meson` version too old | `pip3 install --upgrade meson` (need >= 1.4.0) |
| Drive A: not visible in WSL | `sudo mount -t drvfs A: /mnt/a` |
| heif-convert is a dangling symlink | The `POST_INSTALL_TARGET` in cross/heif-convert/Makefile handles this automatically |
