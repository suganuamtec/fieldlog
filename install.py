#!/usr/bin/env python3
"""
FieldLog — Installer
Run once to install dependencies and create a desktop shortcut.

  python install.py          (Mac / Linux)
  python install.py          (Windows — run from cmd or PowerShell)
  python install.py --dmg    (Mac only — also build a DMG installer)
"""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

HERE    = Path(__file__).parent.resolve()
LAUNCH  = HERE / "launcher.py"
PYTHON  = sys.executable
SYSTEM  = platform.system()

ICON_PNG  = HERE / "assets" / "icon.png"
ICON_ICNS = HERE / "assets" / "icon.icns"


# ── Helpers ────────────────────────────────────────────────────────────────────

def banner(msg):
    width = 52
    print("=" * width)
    print(f"  {msg}")
    print("=" * width)


def step(msg):
    print(f"  {msg}")


# ── Dependency install ─────────────────────────────────────────────────────────

# Qt 6.5+ requires libxcb-cursor0 to load the xcb (X11) platform plugin.
_LINUX_APT_PACKAGES = ["libxcb-cursor0"]


def _install_linux_system_deps():
    """Install required apt packages on Linux, silently skipping if already present."""
    missing = []
    for pkg in _LINUX_APT_PACKAGES:
        r = subprocess.run(
            ["dpkg-query", "-W", "-f=${Status}", pkg],
            capture_output=True, text=True,
        )
        if "install ok installed" not in r.stdout:
            missing.append(pkg)

    if not missing:
        step("✓ System packages OK")
        return

    step(f"Installing system packages: {', '.join(missing)} ...")
    try:
        subprocess.check_call(
            ["sudo", "apt-get", "install", "-y"] + missing,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        step(f"✓ System packages installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        step(f"⚠  Could not auto-install: {', '.join(missing)}")
        step( "   Run manually:  sudo apt-get install -y " + " ".join(missing))


def _install_qt():
    """Install PySide6, falling back to PyQt5 if PySide6 is incompatible."""
    for pkg in ("PySide6>=6.5.0,<6.9", "PyQt5>=5.15"):
        try:
            subprocess.check_call(
                [PYTHON, "-m", "pip", "install", pkg],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            label = "PySide6" if "PySide6" in pkg else "PyQt5 (fallback)"
            step(f"✓ Qt installed     → {label}")
            return
        except subprocess.CalledProcessError:
            continue
    step("⚠  Could not install PySide6 or PyQt5 — launcher UI will not work.")


def install_deps(skip_qt: bool = False):
    if SYSTEM == "Linux":
        _install_linux_system_deps()
    step("Installing Python dependencies...")
    # Filter Qt packages — Qt is installed separately via _install_qt() with
    # PySide6 → PyQt5 fallback logic.  On Mac, mac_install.command already
    # handled Qt before calling install.py, so skip_qt=True avoids overwriting
    # the working fallback.
    non_qt = [
        l.strip() for l in (HERE / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if l.strip() and not l.startswith("#") and "PySide6" not in l and "PyQt5" not in l
    ]
    subprocess.check_call(
        [PYTHON, "-m", "pip", "install"] + non_qt,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    step("✓ Dependencies installed")
    if not skip_qt:
        _install_qt()


# ── Icon generation ────────────────────────────────────────────────────────────

def generate_icon() -> Path | None:
    """
    Return assets/icon.png, generating it first if possible.
    Falls back to the pre-existing file if generation fails.
    """
    # If the icon is already there, use it directly
    if ICON_PNG.exists():
        step(f"✓ Icon ready      → {ICON_PNG}")
        return ICON_PNG

    make = HERE / "make_icon.py"
    if not make.exists():
        return None
    try:
        subprocess.check_call(
            [PYTHON, str(make)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass   # Pillow may not be installed; that's OK

    # Return whatever we have after the attempt
    if ICON_PNG.exists():
        step(f"✓ Icon generated  → {ICON_PNG}")
        return ICON_PNG
    return None


def _png_to_icns(png: Path) -> Path | None:
    """
    Convert icon.png → icon.icns on macOS using iconutil.
    Returns path to .icns or None on failure.
    """
    if SYSTEM != "Darwin":
        return None
    try:
        from PIL import Image
        iconset = HERE / "assets" / "FieldLog.iconset"
        iconset.mkdir(parents=True, exist_ok=True)
        img = Image.open(png).convert("RGBA")
        sizes = [16, 32, 64, 128, 256, 512]
        for s in sizes:
            img.resize((s, s), Image.LANCZOS).save(
                iconset / f"icon_{s}x{s}.png"
            )
            img.resize((s * 2, s * 2), Image.LANCZOS).save(
                iconset / f"icon_{s}x{s}@2x.png"
            )
        subprocess.check_call(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(ICON_ICNS)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        shutil.rmtree(iconset, ignore_errors=True)
        if ICON_ICNS.exists():
            step(f"✓ ICNS created    → {ICON_ICNS}")
            return ICON_ICNS
    except Exception:
        pass
    return None


# ── Linux ──────────────────────────────────────────────────────────────────────

def _install_icon_linux(icon: Path) -> str:
    """
    Copy icon.png into the GNOME icon theme so GNOME can find it by name.
    Returns the icon name to use in the desktop file ('fieldlog' or absolute path).
    """
    try:
        theme_dir = (
            Path.home() / ".local" / "share" / "icons"
            / "hicolor" / "256x256" / "apps"
        )
        theme_dir.mkdir(parents=True, exist_ok=True)
        dest = theme_dir / "fieldlog.png"
        shutil.copy2(icon, dest)
        # Refresh the icon cache so GNOME picks up the new icon
        for cache_cmd in (
            ["gtk-update-icon-cache", "-f", "-t",
             str(Path.home() / ".local" / "share" / "icons" / "hicolor")],
            ["update-icon-caches",
             str(Path.home() / ".local" / "share" / "icons" / "hicolor")],
        ):
            try:
                subprocess.run(cache_cmd, capture_output=True)
                break
            except FileNotFoundError:
                continue
        step(f"✓ Icon installed   → {dest}")
        return "fieldlog"        # name-based lookup — most reliable with GNOME
    except Exception:
        return str(icon)         # fall back to absolute path


def create_shortcut_linux(icon: Path | None = None):
    # Write a tiny shell wrapper so the .desktop Exec line is a single
    # unquoted path — far more compatible with all desktop file parsers.
    wrapper = HERE / "fieldlog_run.sh"
    wrapper.write_text(
        "#!/bin/bash\n"
        f'cd "{HERE}"\n'
        f'exec "{PYTHON}" "{LAUNCH}" "$@"\n',
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    step(f"✓ Launcher script  → {wrapper}")

    icon_ref = _install_icon_linux(icon) if icon and icon.exists() else ""
    icon_line = f"Icon={icon_ref}\n" if icon_ref else ""
    entry = (
        "[Desktop Entry]\n"
        "Name=FieldLog\n"
        "Comment=UAM Deployment Entry\n"
        f"Exec={wrapper}\n"
        "Type=Application\n"
        "Categories=Utility;\n"
        "Terminal=false\n"
        "StartupNotify=true\n"
        "StartupWMClass=FieldLog\n"
        + icon_line
    )

    # Application menu
    app_dir = Path.home() / ".local" / "share" / "applications"
    app_dir.mkdir(parents=True, exist_ok=True)
    menu_file = app_dir / "fieldlog.desktop"
    menu_file.write_text(entry)
    menu_file.chmod(0o755)
    step(f"✓ App menu entry  → {menu_file}")

    # Desktop shortcut (if Desktop folder exists)
    desktop = Path.home() / "Desktop"
    if desktop.is_dir():
        shortcut = desktop / "FieldLog.desktop"
        shortcut.write_text(entry)
        shortcut.chmod(0o755)
        # Mark as trusted so GNOME allows launching without the "Allow Launching" prompt.
        # Try with -t string first (required on some distros), fall back without it.
        for _gio_args in (
            ["gio", "set", "-t", "string", str(shortcut), "metadata::trusted", "true"],
            ["gio", "set", str(shortcut), "metadata::trusted", "true"],
        ):
            try:
                r = subprocess.run(_gio_args, capture_output=True)
                if r.returncode == 0:
                    break
            except FileNotFoundError:
                break  # gio not available
        step(f"✓ Desktop shortcut → {shortcut}")


# ── macOS ──────────────────────────────────────────────────────────────────────

def create_shortcut_mac(icon_png: Path | None = None,
                        icon_icns: Path | None = None):
    app_name = "FieldLog.app"
    desktop  = Path.home() / "Desktop"
    app_path = desktop / app_name

    if app_path.exists():
        shutil.rmtree(app_path)

    macos     = app_path / "Contents" / "MacOS"
    resources = app_path / "Contents" / "Resources"
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)

    # Copy icon into bundle
    bundle_icon_name = "AppIcon"
    if icon_icns and icon_icns.exists():
        shutil.copy(icon_icns, resources / "AppIcon.icns")
        bundle_icon_name = "AppIcon"
        step("✓ Icon embedded in .app bundle")
    elif icon_png and icon_png.exists():
        shutil.copy(icon_png, resources / "AppIcon.png")
        bundle_icon_name = "AppIcon"

    (app_path / "Contents" / "Info.plist").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"'
        ' "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0"><dict>\n'
        '  <key>CFBundleName</key>        <string>FieldLog</string>\n'
        '  <key>CFBundleExecutable</key>  <string>launch</string>\n'
        '  <key>CFBundleIdentifier</key>  <string>com.uamtec.fieldlog</string>\n'
        '  <key>CFBundleVersion</key>     <string>1.0</string>\n'
        f' <key>CFBundleIconFile</key>   <string>{bundle_icon_name}</string>\n'
        '  <key>LSUIElement</key>         <false/>\n'
        '</dict></plist>\n'
    )

    script = macos / "launch"
    script.write_text(f'#!/bin/bash\n"{PYTHON}" "{LAUNCH}"\n')
    script.chmod(0o755)

    step(f"✓ App bundle created → {app_path}")
    step(  "  Drag FieldLog.app from Desktop into /Applications to install globally.")
    return app_path


def create_dmg(app_path: Path):
    """Build a distributable DMG from the .app bundle."""
    import tempfile

    dmg_path = Path.home() / "Desktop" / "FieldLog.dmg"
    if dmg_path.exists():
        dmg_path.unlink()

    tmp = Path(tempfile.mkdtemp(prefix="fieldlog_dmg_"))
    try:
        shutil.copytree(app_path, tmp / "FieldLog.app")
        (tmp / "Applications").symlink_to("/Applications")

        subprocess.check_call(
            [
                "hdiutil", "create",
                "-volname", "FieldLog",
                "-srcfolder", str(tmp),
                "-ov",
                "-format", "UDZO",
                str(dmg_path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        step(f"✓ DMG created       → {dmg_path}")
        step(  "  Distribute this DMG — users drag FieldLog.app into Applications.")
    except subprocess.CalledProcessError:
        step("⚠  hdiutil failed — DMG not created.")
    except FileNotFoundError:
        step("⚠  hdiutil not found — run this on macOS to build a DMG.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── Windows ────────────────────────────────────────────────────────────────────

def create_shortcut_windows(icon: Path | None = None):
    desktop = Path.home() / "Desktop"
    icon_arg = f'$s.IconLocation="{icon}";' if icon and icon.exists() else ""

    lnk = desktop / "FieldLog.lnk"
    ps_cmd = (
        f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{lnk}");'
        f'$s.TargetPath="{PYTHON}";'
        f'$s.Arguments=\'"{LAUNCH}"\';'
        f'$s.WorkingDirectory="{HERE}";'
        f'$s.Description="FieldLog — UAM Deployment Entry";'
        + icon_arg +
        f'$s.Save()'
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            check=True, capture_output=True,
        )
        step(f"✓ Desktop shortcut  → {lnk}")
        return
    except Exception:
        pass

    # Fallback: .bat file
    bat = desktop / "FieldLog.bat"
    bat.write_text(
        f'@echo off\n"{PYTHON}" "{LAUNCH}"\n',
        encoding="utf-8",
    )
    step(f"✓ Desktop shortcut  → {bat}  (batch file fallback)")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    build_dmg = "--dmg"       in sys.argv
    skip_qt   = "--skip-qt"   in sys.argv

    banner("FieldLog Installer")
    print(f"  Platform : {SYSTEM}")
    print(f"  Python   : {PYTHON}")
    print(f"  Location : {HERE}")
    if build_dmg and SYSTEM == "Darwin":
        print(f"  Mode     : shortcut + DMG")
    print()

    try:
        install_deps(skip_qt=skip_qt)
    except subprocess.CalledProcessError as e:
        print(f"\n  ✗ Dependency install failed: {e}")
        sys.exit(1)

    print()
    step("Generating icon...")
    icon = generate_icon()

    print()
    step(f"Creating desktop shortcut ({SYSTEM})...")

    try:
        if SYSTEM == "Linux":
            create_shortcut_linux(icon)

        elif SYSTEM == "Darwin":
            icns = _png_to_icns(icon) if icon else None
            app_path = create_shortcut_mac(icon_png=icon, icon_icns=icns)
            if build_dmg:
                print()
                step("Building DMG installer...")
                create_dmg(app_path)

        elif SYSTEM == "Windows":
            create_shortcut_windows(icon)
        else:
            step(f"⚠  Unsupported platform '{SYSTEM}' — skipping shortcut.")
    except Exception as e:
        step(f"⚠  Could not create shortcut: {e}")

    print()
    banner("Installation complete!")
    print()
    print("  To launch FieldLog:")
    print(f"    python {LAUNCH.name}")
    if SYSTEM == "Darwin" and not build_dmg:
        print()
        print("  To also build a distributable DMG:")
        print(f"    python install.py --dmg")
    print()

    if SYSTEM == "Windows":
        input("  Press Enter to close…")


if __name__ == "__main__":
    main()
