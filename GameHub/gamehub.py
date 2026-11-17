import hashlib
import json
import base64
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageDraw
import customtkinter as ctk

def resource_path(relative):
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / relative

APP_NAME = 'GameHub'
APP_VERSION = '3.6.0'
DATA_DIR = Path(os.environ.get('APPDATA', str(Path.home()))) / APP_NAME
CONFIG = DATA_DIR / 'launchers.json'

LAUNCHERS = {
    'Steam': ['Steam/steam.exe'],
    'Epic Games': ['Epic Games/Launcher/Portal/Binaries/Win64/EpicGamesLauncher.exe', 'Epic Games/Launcher/Portal/Binaries/Win32/EpicGamesLauncher.exe'],
    'CurseForge': ['Overwolf/CurseForge/CurseForge.exe', 'Programs/CurseForge/CurseForge.exe', 'CurseForge/CurseForge.exe', 'CurseForge Windows/CurseForge.exe'],
    'GOG Galaxy': ['GOG Galaxy/GalaxyClient.exe'],
    'EA app': ['Electronic Arts/EA Desktop/EA Desktop/EADesktop.exe'],
    'Ubisoft Connect': ['Ubisoft/Ubisoft Game Launcher/UbisoftConnect.exe', 'Ubisoft/Ubisoft Game Launcher/upc.exe'],
    'Battle.net': ['Battle.net/Battle.net Launcher.exe', 'Battle.net/Battle.net.exe'],
    'Riot Client': ['Riot Games/Riot Client/RiotClientServices.exe'],
    'Battlestate Games': ['Battlestate Games/BsgLauncher/BsgLauncher.exe', 'Battlestate Games/BsgLauncher.exe', 'BsgLauncher/BsgLauncher.exe', 'Battlestate Games Launcher/BsgLauncher.exe'],
    'Rockstar Games': ['Rockstar Games/Launcher/Launcher.exe'],
    'Amazon Games': ['Amazon Games/App/Amazon Games.exe'],
    'itch.io': ['itch/app-*/itch.exe'],
    'Playnite': ['Playnite/Playnite.DesktopApp.exe'],
    'Heroic': ['Heroic/Heroic.exe'],
    'Xbox': ['WindowsApps/Microsoft.GamingApp*'],
}


def roots():
    values = [os.environ.get('PROGRAMFILES'), os.environ.get('PROGRAMFILES(X86)'), os.environ.get('LOCALAPPDATA'), os.environ.get('APPDATA'), 'C:/Program Files', 'C:/Program Files (x86)', 'C:/Battlestate Games', 'C:/Riot Games', 'C:/Games', 'D:/Games']
    return [Path(p) for p in dict.fromkeys(values) if p]


def detect():
    found = {}
    for name, patterns in LAUNCHERS.items():
        if name == 'Xbox':
            continue
        for root in roots():
            for pattern in patterns:
                try:
                    matches = list(root.glob(pattern))
                except OSError:
                    matches = []
                for match in matches:
                    if match.is_file():
                        found[name] = str(match)
                        break
                if name in found:
                    break
            if name in found:
                break
    # Additional commonly used install locations.
    for name, paths in {
        'Riot Client': ['C:/Riot Games/Riot Client/RiotClientServices.exe'],
        'Battlestate Games': ['C:/Battlestate Games/BsgLauncher/BsgLauncher.exe', 'C:/Battlestate Games/BsgLauncher.exe'],
        'CurseForge': [str(Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/CurseForge/CurseForge.exe'), str(Path(os.environ.get('LOCALAPPDATA', '')) / 'Overwolf/CurseForge/CurseForge.exe')],
    }.items():
        for path in paths:
            if Path(path).is_file():
                found[name] = path
                break
    # Xbox is an MS Store app, opened using its URI instead of an exe path.
    found['Xbox (Microsoft Store)'] = 'ms-windows-store://pdp/?ProductId=9MV0B5HZVK9Z'
    return found


def load_custom():
    try:
        obj = json.loads(CONFIG.read_text(encoding='utf-8'))
        return {str(k): str(v) for k, v in obj.items()} if isinstance(obj, dict) else {}
    except (OSError, ValueError):
        return {}


def save_custom(items):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(items, indent=2), encoding='utf-8')



ASSETS = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'assets'

BG = '#0B0E16'
PANEL = '#141A27'
TILE = '#1B2333'
HOVER = '#26344D'
TEXT = '#F2F5FF'
MUTED = '#94A3BD'
ACCENT = '#758BFF'


class GameHub(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode('dark')
        self.title('GameHub — Your gaming universe')
        try:
            icon_path = resource_path('assets/gamehub.ico')
            self.iconbitmap(str(icon_path))
        except (OSError, tk.TclError):
            pass
        self.geometry('1120x750')
        self.minsize(820, 540)
        self.configure(fg_color=BG)
        self.custom = load_custom()
        self.custom_icons = self.load_custom_icons()
        self.renamed = self.load_renamed()
        self.detected = {}
        self.icon_refs = []
        self.filter = ctk.StringVar(value='')
        self.filter.trace_add('write', lambda *_: self.schedule_render() if hasattr(self, 'scroll') else None)
        self.mode = 'All launchers'
        self.make_ui()
        self.scan()
        self.after(2500, lambda: self.check_updates(silent=True))

    def make_ui(self):
        self.sidebar = ctk.CTkFrame(self, fg_color='#101521', width=225, corner_radius=0)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        ctk.CTkLabel(self.sidebar, text='◈  GAMEHUB', font=('Segoe UI', 23, 'bold'), text_color=TEXT).pack(anchor='w', padx=23, pady=(35, 7))
        ctk.CTkLabel(self.sidebar, text='YOUR GAMING SPACE', font=('Segoe UI', 10, 'bold'), text_color=MUTED).pack(anchor='w', padx=25, pady=(0, 48))
        self.nav_buttons = {}
        for label, symbol in [('All launchers', '▦'), ('Custom apps', '✦')]:
            btn = ctk.CTkButton(self.sidebar, text=f'{symbol}   {label}', anchor='w', height=44,
                fg_color='transparent', hover_color=HOVER, text_color=TEXT, corner_radius=11,
                font=('Segoe UI', 13), command=lambda x=label: self.set_mode(x))
            btn.pack(fill='x', padx=13, pady=4)
            self.nav_buttons[label] = btn
        ctk.CTkFrame(self.sidebar, height=1, fg_color='#283044').pack(fill='x', padx=22, pady=25)
        ctk.CTkButton(self.sidebar, text='+  Add launcher', height=43, corner_radius=12,
            fg_color=ACCENT, hover_color='#6075E7', text_color='#080C17', font=('Segoe UI', 13, 'bold'),
            command=self.add).pack(fill='x', padx=17)
        ctk.CTkButton(self.sidebar, text='↻  Rescan PC', height=40, fg_color='transparent',
            hover_color=HOVER, text_color=MUTED, command=self.scan).pack(fill='x', padx=17, pady=(10, 0))
        ctk.CTkButton(self.sidebar, text='↓  Check for updates', height=40,
            fg_color='transparent', hover_color=HOVER, text_color=MUTED,
            command=lambda: self.check_updates(silent=False)).pack(fill='x', padx=17, pady=(5, 0))
        ctk.CTkLabel(self.sidebar, text='GAMEHUB  •  v3.6.0', text_color='#64728E',
            font=('Segoe UI', 10)).pack(side='bottom', pady=24)

        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        main.pack(side='left', fill='both', expand=True)
        header = ctk.CTkFrame(main, fg_color='transparent')
        header.pack(fill='x', padx=32, pady=(32, 13))
        ctk.CTkLabel(header, text='Your launchers', text_color=TEXT,
            font=('Segoe UI', 29, 'bold')).pack(anchor='w')
        ctk.CTkLabel(header, text='Everything you play, all in one place.',
            text_color=MUTED, font=('Segoe UI', 13)).pack(anchor='w', pady=(4, 0))
        bar = ctk.CTkFrame(main, fg_color='transparent')
        bar.pack(fill='x', padx=32, pady=(20, 17))
        self.search = ctk.CTkEntry(bar, textvariable=self.filter, placeholder_text='Search launchers...',
            height=43, corner_radius=12, fg_color=PANEL, border_color='#29354C',
            text_color=TEXT, font=('Segoe UI', 13))
        self.search.pack(side='left', fill='x', expand=True)
        self.search.configure(placeholder_text='⌕  Search launchers...')
        self.count = ctk.CTkLabel(bar, text='', text_color=MUTED, font=('Segoe UI', 12))
        self.count.pack(side='right', padx=(17, 0))
        self.scroll = ctk.CTkScrollableFrame(main, fg_color='transparent', corner_radius=0, scrollbar_button_color='#273044', scrollbar_button_hover_color='#3B4A66')
        self.scroll.pack(fill='both', expand=True, padx=22, pady=(0, 20))
        # Avoid re-rendering on layout changes: this caused continuous tile flashing.
        self._render_job = None
        self.set_mode('All launchers')

    def schedule_render(self):
        if self._render_job:
            self.after_cancel(self._render_job)
        self._render_job = self.after(180, self.render)

    def set_mode(self, mode):
        self.mode = mode
        for label, btn in self.nav_buttons.items():
            btn.configure(fg_color='#273454' if label == mode else 'transparent',
                          text_color='#FFFFFF' if label == mode else MUTED)
        self.render()

    def scan(self):
        self.detected = detect()
        self.render()

    def check_updates(self, silent=False):
        # Network I/O happens off the Tk UI thread.
        import threading
        from updater import check_for_update, download_and_install
        def worker():
            try:
                info = check_for_update(APP_VERSION)
                if not info:
                    if not silent:
                        self.after(0, lambda: messagebox.showinfo('GameHub Updates', 'You are running the latest version.'))
                    return
                def offer():
                    if messagebox.askyesno('GameHub update available',
                        f"GameHub {info['version']} is available.\n\nDownload and install this verified update now?\nGameHub will close after the installer starts."):
                        threading.Thread(target=install, args=(info,), daemon=True).start()
                self.after(0, offer)
            except Exception as exc:
                if not silent:
                    msg = str(exc)
                    self.after(0, lambda: messagebox.showerror('Update check failed', msg))
        def install(info):
            try:
                installer = download_and_install(info)
                self.after(0, self.destroy)
            except Exception as exc:
                msg = str(exc)
                self.after(0, lambda: messagebox.showerror('Update failed', msg))
        threading.Thread(target=worker, daemon=True).start()

    def get_icon(self, path, name=''):
        # Prefer user-selected or bundled artwork over Windows' often low-resolution EXE icons.
        chosen = self.custom_icons.get(name)
        if chosen and Path(chosen).is_file():
            art = self.load_art(chosen)
            if art: return art
        bundled = ASSETS / (name.lower().replace(' ', '_') + '.png')
        if bundled.is_file():
            art = self.load_art(bundled)
            if art: return art
        if name.startswith('Xbox'):
            return self.xbox_icon()
        if not Path(path).is_file():
            return None
        icon_dir = DATA_DIR / 'icons_v32'
        icon_dir.mkdir(parents=True, exist_ok=True)
        try:
            stamp = f'{path}|{Path(path).stat().st_mtime_ns}|jumbo-v2'
        except OSError:
            return None
        dest = icon_dir / (hashlib.sha256(stamp.encode('utf-8')).hexdigest() + '.png')
        if not dest.exists():
            # SHGetImageList(SHIL_JUMBO) returns the 256px Windows icon when
            # available. The legacy ExtractAssociatedIcon only returns ~32px.
            ps = r"""
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
public class ShellJumbo {
 [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
 public struct SHFILEINFO { public IntPtr hIcon; public int iIcon; public uint dwAttributes;
 [MarshalAs(UnmanagedType.ByValTStr, SizeConst=260)] public string szDisplayName;
 [MarshalAs(UnmanagedType.ByValTStr, SizeConst=80)] public string szTypeName; }
 [DllImport("shell32.dll", CharSet=CharSet.Unicode)]
 static extern IntPtr SHGetFileInfo(string path, uint attrs, ref SHFILEINFO info, uint cb, uint flags);
 [DllImport("shell32.dll", EntryPoint="#727")]
 static extern int SHGetImageList(int type, ref Guid iid, out IntPtr list);
 [DllImport("user32.dll")] static extern bool DestroyIcon(IntPtr icon);
 [UnmanagedFunctionPointer(CallingConvention.StdCall)]
 delegate int GetIconDelegate(IntPtr self, int index, int flags, out IntPtr icon);
 public static void Save(string path, string output) {
  SHFILEINFO info = new SHFILEINFO();
  if (SHGetFileInfo(path, 0, ref info, (uint)Marshal.SizeOf(info), 0x4000) == IntPtr.Zero) return;
  Guid iid = new Guid("46EB5926-582E-4017-9FDF-E8998DAA0950");
  IntPtr list;
  if (SHGetImageList(4, ref iid, out list) != 0 || list == IntPtr.Zero) return;
  IntPtr icon = IntPtr.Zero;
  try {
   IntPtr fn = Marshal.ReadIntPtr(Marshal.ReadIntPtr(list), 10 * IntPtr.Size);
   var get = (GetIconDelegate)Marshal.GetDelegateForFunctionPointer(fn, typeof(GetIconDelegate));
   if (get(list, info.iIcon, 1, out icon) != 0 || icon == IntPtr.Zero) return;
   using (Icon ico = (Icon)Icon.FromHandle(icon).Clone())
   using (Bitmap bitmap = ico.ToBitmap()) bitmap.Save(output, ImageFormat.Png);
  } finally { if (icon != IntPtr.Zero) DestroyIcon(icon); Marshal.Release(list); }
 }
}
'@
[ShellJumbo]::Save($env:GAMEHUB_ICON_SOURCE, $env:GAMEHUB_ICON_DEST)
"""
            try:
                env = dict(os.environ, GAMEHUB_ICON_SOURCE=path, GAMEHUB_ICON_DEST=str(dest))
                subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', ps],
                    env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=14,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            except (OSError, subprocess.TimeoutExpired):
                pass
        try:
            with Image.open(dest) as im:
                if im.width < 64 or im.height < 64:
                    return None  # Don't enlarge a tiny, blurry source.
                im = im.convert('RGBA')
                im.thumbnail((192, 192), Image.Resampling.LANCZOS)
                return ctk.CTkImage(light_image=im.copy(), dark_image=im.copy(), size=(92, 92))
        except (OSError, ValueError):
            return None

    def load_art(self, path):
        try:
            with Image.open(path) as source:
                im = source.convert('RGBA')
                im.thumbnail((220, 220), Image.Resampling.LANCZOS)
                return ctk.CTkImage(light_image=im.copy(), dark_image=im.copy(), size=(92, 92))
        except (OSError, ValueError):
            return None

    def load_custom_icons(self):
        try:
            obj = json.loads((DATA_DIR / 'custom_icons.json').read_text(encoding='utf-8'))
            return obj if isinstance(obj, dict) else {}
        except (OSError, ValueError):
            return {}

    def load_renamed(self):
        try:
            data = json.loads((DATA_DIR / 'renamed.json').read_text(encoding='utf-8'))
            return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_renamed(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / 'renamed.json').write_text(json.dumps(self.renamed, indent=2), encoding='utf-8')

    def edit_name(self, original):
        dialog = ctk.CTkInputDialog(text='Enter a new display name:', title='Rename launcher')
        dialog._entry.insert(0, self.renamed.get(original, original))
        result = dialog.get_input()
        if result is None:
            return
        result = result.strip()
        if not result:
            messagebox.showwarning('Invalid name', 'Launcher name cannot be empty.')
            return
        if result == original:
            self.renamed.pop(original, None)
        else:
            self.renamed[original] = result
        self.save_renamed()
        self.render()

    def edit_logo(self, original):
        path = filedialog.askopenfilename(title='Choose launcher logo',
            filetypes=[('Images', '*.png *.jpg *.jpeg *.webp'), ('All files', '*.*')])
        if not path:
            return
        try:
            with Image.open(path) as im:
                im.verify()
        except (OSError, ValueError):
            messagebox.showerror('Invalid image', 'Choose a valid PNG, JPG, or WebP image.')
            return
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.custom_icons[original] = path
        (DATA_DIR / 'custom_icons.json').write_text(json.dumps(self.custom_icons, indent=2), encoding='utf-8')
        self.render()

    def reset_logo(self, original):
        self.custom_icons.pop(original, None)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / 'custom_icons.json').write_text(json.dumps(self.custom_icons, indent=2), encoding='utf-8')
        self.render()

    def launcher_menu(self, event, original):
        menu = tk.Menu(self, tearoff=0, bg='#1B2333', fg='#F2F5FF',
                       activebackground='#354568', activeforeground='white',
                       bd=0, relief='flat', font=('Segoe UI', 10))
        menu.add_command(label='Rename launcher', command=lambda: self.edit_name(original))
        menu.add_command(label='Change logo...', command=lambda: self.edit_logo(original))
        if original in self.custom_icons:
            menu.add_command(label='Reset logo', command=lambda: self.reset_logo(original))
        if original in self.renamed:
            menu.add_command(label='Reset name', command=lambda: self.reset_name(original))
        if original in self.custom:
            menu.add_separator()
            menu.add_command(label='Remove custom launcher', command=lambda: self.remove_one(original))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def reset_name(self, original):
        self.renamed.pop(original, None)
        self.save_renamed()
        self.render()

    def remove_one(self, original):
        if messagebox.askyesno('Remove launcher', f'Remove {self.renamed.get(original, original)} from GameHub?'):
            self.custom.pop(original, None)
            self.custom_icons.pop(original, None)
            self.renamed.pop(original, None)
            save_custom(self.custom)
            self.save_renamed()
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            (DATA_DIR / 'custom_icons.json').write_text(json.dumps(self.custom_icons, indent=2), encoding='utf-8')
            self.render()

    def xbox_icon(self):
        # Draw a crisp Xbox-inspired X mark without a pixelated text fallback.
        size = 256
        im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((14, 14, 242, 242), fill='#107C10')
        d.arc((49, 43, 207, 210), 202, 338, fill='white', width=16)
        d.line([(67, 64), (127, 122), (189, 64)], fill='white', width=18, joint='curve')
        d.line([(65, 196), (127, 123), (191, 196)], fill='white', width=18, joint='curve')
        return ctk.CTkImage(light_image=im, dark_image=im, size=(92, 92))

    def render(self):
        if not hasattr(self, 'scroll'):
            return
        self._render_job = None
        for child in self.scroll.winfo_children():
            child.destroy()
        self.icon_refs.clear()
        items = self.custom if self.mode == 'Custom apps' else {**self.detected, **self.custom}
        query = self.filter.get().strip().casefold()
        items = [(name, path) for name, path in sorted(items.items(), key=lambda item: self.renamed.get(item[0], item[0]).casefold()) if query in self.renamed.get(name, name).casefold()]
        self.count.configure(text=f'{len(items)} apps')
        cols = 4  # Stable grid prevents resize/reflow redraw loops.
        for col in range(cols):
            self.scroll.grid_columnconfigure(col, weight=1, uniform='apps')
        for idx, (name, path) in enumerate(items):
            row, col = divmod(idx, cols)
            card = ctk.CTkFrame(self.scroll, fg_color=TILE, corner_radius=17,
                                border_width=1, border_color='#303B51', height=184)
            card.grid(row=row, column=col, padx=9, pady=10, sticky='nsew')
            card.grid_propagate(False)
            icon = self.get_icon(path, name)
            if icon:
                self.icon_refs.append(icon)
                logo = ctk.CTkLabel(card, image=icon, text='')
            else:
                logo = ctk.CTkLabel(card, text='◈', text_color='#A9B8FF',
                    font=('Segoe UI', 29, 'bold'))
            logo.pack(expand=True, pady=(17, 0))
            title = ctk.CTkLabel(card, text=self.renamed.get(name, name), text_color=TEXT, font=('Segoe UI', 12, 'bold'),
                                 wraplength=145)
            title.pack(pady=(4, 0))
            title.pack_configure(pady=(5, 17))
            def launch_here(event=None, target=path):
                self.launch(target)
            # Only change hover state when the pointer really enters/leaves the
            # entire card, not when it moves between child labels and the card.
            def update_hover(tile=card):
                if not tile.winfo_exists():
                    return
                x, y = tile.winfo_pointerxy()
                inside = (tile.winfo_rootx() <= x < tile.winfo_rootx() + tile.winfo_width()
                          and tile.winfo_rooty() <= y < tile.winfo_rooty() + tile.winfo_height())
                tile.configure(fg_color=HOVER if inside else TILE,
                               border_color=ACCENT if inside else '#303B51')
            for widget in (card, logo, title):
                widget.bind('<Button-1>', launch_here)
                widget.bind('<Button-3>', lambda e, original=name: self.launcher_menu(e, original))
                widget.bind('<Enter>', lambda e, fn=update_hover: self.after_idle(fn))
                widget.bind('<Leave>', lambda e, fn=update_hover: self.after_idle(fn))
                widget.configure(cursor='hand2')
        if not items:
            ctk.CTkLabel(self.scroll, text='No launchers found\nTry Rescan PC or Add launcher.',
                text_color=MUTED, font=('Segoe UI', 15), justify='center').grid(row=0, column=0,
                columnspan=cols, pady=85)

    def launch(self, target):
        try:
            if target.startswith(('ms-', 'http:', 'https:')):
                os.startfile(target)
            elif Path(target).is_file():
                subprocess.Popen([target], cwd=str(Path(target).parent), close_fds=True)
            else:
                messagebox.showerror('Launcher missing', f'File no longer exists:\n{target}')
        except Exception as exc:
            messagebox.showerror('Could not launch', str(exc))

    def add(self):
        path = filedialog.askopenfilename(title='Choose launcher executable',
            filetypes=[('Windows programs', '*.exe'), ('All files', '*.*')])
        if not path:
            return
        dialog = ctk.CTkInputDialog(text='Name this launcher:', title='Add launcher')
        name = dialog.get_input()
        if name and name.strip():
            self.custom[name.strip()] = path
            save_custom(self.custom)
            self.render()

    def remove(self):
        if not self.custom:
            return
        name = ctk.CTkInputDialog(text='Enter the exact custom launcher name to remove:',
                                  title='Remove launcher').get_input()
        if name in self.custom:
            self.custom.pop(name)
            save_custom(self.custom)
            self.render()


if __name__ == '__main__':
    if sys.platform != 'win32':
        raise SystemExit('GameHub is intended for Windows.')
    GameHub().mainloop()
