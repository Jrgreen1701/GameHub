import hashlib
import re
import colorsys
import math
import threading
import psutil
import pystray
import json
import io
import urllib.request
import urllib.parse
import webbrowser
import uuid
import base64
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageDraw, ImageTk, ImageGrab
import customtkinter as ctk

def resource_path(relative):
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / relative

APP_NAME = 'GameHub'
APP_VERSION = '3.9.6'
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
TEXT = '#DDE5F2'
MUTED = '#9AA8C0'
ACCENT = '#758BFF'
ACCENTS = {'Blue': '#758BFF', 'Purple': '#A78BFA', 'Green': '#43CFA8', 'Orange': '#F6A65C', 'Pink': '#F08AB8'}


def theme_palette(accent):
    """Tint dark surfaces with the chosen accent, without reducing readability."""
    from colorsys import rgb_to_hsv
    raw = accent.lstrip('#')
    if len(raw) != 6:
        raise ValueError('Expected a six-digit RGB color')
    r, g, b = (int(raw[i:i+2], 16) for i in (0, 2, 4))
    def blend(base, amount):
        original = tuple(int(base[i:i+2], 16) for i in (1, 3, 5))
        return '#' + ''.join(f'{round(a * (1 - amount) + c * amount):02X}' for a, c in zip(original, (r,g,b)))
    return dict(bg=blend('#0B0E16', .10), sidebar=blend('#101521', .16),
                panel=blend('#141A27', .18), tile=blend('#1B2333', .22),
                hover=blend('#26344D', .33), border=blend('#303B51', .36),
                input_border=blend('#29354C', .38))


def fetch_bytes(url, limit=8_000_000):
    if not url.startswith('https://'):
        raise ValueError('Only HTTPS images are supported')
    request = urllib.request.Request(url, headers={'User-Agent': 'GameHub/3.8 (desktop launcher)'})
    with urllib.request.urlopen(request, timeout=12) as response:
        if response.headers.get('Content-Length') and int(response.headers['Content-Length']) > limit:
            raise ValueError('File exceeds download limit')
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('File exceeds download limit')
    return data


def fetch_json(url):
    return json.loads(fetch_bytes(url, limit=2_000_000).decode('utf-8'))


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
        self.logo_only = tk.BooleanVar(value=False)
        self.logo_size = tk.IntVar(value=84)
        self.view_settings_path = DATA_DIR / 'view_settings.json'
        try:
            saved = json.loads(self.view_settings_path.read_text(encoding='utf-8'))
            self.logo_only.set(bool(saved.get('logo_only', False)))
            self.logo_size.set(max(48, min(132, int(saved.get('logo_size', 84)))))
        except (OSError, ValueError, TypeError):
            pass
        self.preferences_path = DATA_DIR / 'preferences_v37.json'
        try:
            prefs = json.loads(self.preferences_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            prefs = {}
        self.favorites = set(prefs.get('favorites', []))
        self.launcher_order = list(prefs.get('order', []))
        self.accent_name = prefs.get('accent', 'Blue')
        if self.accent_name not in (*ACCENTS, 'Custom'):
            self.accent_name = 'Blue'
        self.custom_accent = prefs.get('custom_accent', '#758BFF')
        try:
            theme_palette(self.custom_accent)
        except (ValueError, TypeError):
            self.custom_accent = '#758BFF'
        self.accent = self.custom_accent if self.accent_name == 'Custom' else ACCENTS[self.accent_name]
        self.theme_colors = theme_palette(self.accent)
        self.configure(fg_color=self.theme_colors['bg'])
        self._drag_start = None
        self._dragged = False
        self._suppress_click = False
        self._tiles = {}
        self._running_dots = {}
        self._tray = None
        self._really_exit = False
        self.protocol('WM_DELETE_WINDOW', self.hide_to_tray)
        self.make_ui()
        self.scan()
        self.after(2500, lambda: self.check_updates(silent=True))
        self.after(1800, self.poll_running)

    def make_ui(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=self.theme_colors['sidebar'], width=225, corner_radius=0)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        brand = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        brand.pack(anchor='w', padx=20, pady=(32, 7))
        brand_icon = ctk.CTkImage(light_image=Image.open(ASSETS / 'gamehub_icon.png'),
                                  dark_image=Image.open(ASSETS / 'gamehub_icon.png'), size=(34, 34))
        self.brand_icon = brand_icon
        ctk.CTkLabel(brand, image=brand_icon, text='').pack(side='left', padx=(0, 9))
        ctk.CTkLabel(brand, text='GAMEHUB', font=('Segoe UI', 21, 'bold'), text_color=TEXT).pack(side='left')
        ctk.CTkLabel(self.sidebar, text='YOUR GAMING SPACE', font=('Segoe UI', 10, 'bold'), text_color=MUTED).pack(anchor='w', padx=25, pady=(0, 48))
        self.nav_buttons = {}
        for label, symbol in [('All launchers', '▦'), ('Custom apps', '✦')]:
            btn = ctk.CTkButton(self.sidebar, text=f'{symbol}   {label}', anchor='w', height=44,
                fg_color='transparent', hover_color=self.theme_colors['hover'], text_color=TEXT, corner_radius=11,
                font=('Segoe UI', 13), command=lambda x=label: self.set_mode(x))
            btn.pack(fill='x', padx=13, pady=4)
            self.nav_buttons[label] = btn
        ctk.CTkFrame(self.sidebar, height=1, fg_color='#283044').pack(fill='x', padx=22, pady=25)
        self.add_button = ctk.CTkButton(self.sidebar, text='+  Add launcher', height=43, corner_radius=12,
            fg_color=self.accent, hover_color=self.theme_colors['hover'], text_color='#080C17', font=('Segoe UI', 13, 'bold'),
            command=self.add)
        self.add_button.pack(fill='x', padx=17)
        ctk.CTkButton(self.sidebar, text='↻  Rescan PC', height=40, fg_color='transparent',
            hover_color=HOVER, text_color=MUTED, command=self.scan).pack(fill='x', padx=17, pady=(10, 0))
        ctk.CTkButton(self.sidebar, text='↓  Check for updates', height=40,
            fg_color='transparent', hover_color=HOVER, text_color=MUTED,
            command=lambda: self.check_updates(silent=False)).pack(fill='x', padx=17, pady=(5, 0))
        ctk.CTkLabel(self.sidebar, text='APPEARANCE', text_color=MUTED,
                     font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=23, pady=(22, 6))
        self.color_button = ctk.CTkButton(
            self.sidebar, text='  Theme colors     ◉', anchor='w', height=39,
            corner_radius=11, fg_color=self.theme_colors['panel'],
            border_width=1, border_color=self.theme_colors['border'],
            text_color=TEXT, hover_color=self.theme_colors['hover'],
            command=self.open_theme_dialog)
        self.color_button.pack(padx=17, fill='x')
        ctk.CTkLabel(self.sidebar, text='GAMEHUB  •  v3.9.0', text_color='#64728E',
            font=('Segoe UI', 10)).pack(side='bottom', pady=24)

        main = ctk.CTkFrame(self, fg_color=self.theme_colors['bg'], corner_radius=0)
        main.pack(side='left', fill='both', expand=True)
        header = ctk.CTkFrame(main, fg_color='transparent')
        header.pack(fill='x', padx=32, pady=(32, 13))
        ctk.CTkLabel(header, text='Your launchers', text_color=TEXT,
            font=('Segoe UI Semibold', 28)).pack(anchor='w')
        ctk.CTkLabel(header, text='Everything you play, all in one place.',
            text_color=MUTED, font=('Segoe UI', 13)).pack(anchor='w', pady=(4, 0))
        # Compact display controls sit ABOVE the search bar, right-aligned.
        controls = ctk.CTkFrame(main, fg_color='transparent', height=24)
        controls.pack(fill='x', padx=32, pady=(2, 0))
        self.logo_switch = ctk.CTkSwitch(
            controls, text='Logos only', variable=self.logo_only,
            command=self.change_view, font=('Segoe UI', 11),
            text_color=MUTED, width=91, switch_width=29, switch_height=16,
            progress_color=self.accent)
        self.logo_switch.pack(side='right', padx=(10, 0))
        ctk.CTkLabel(controls, text='▣', font=('Segoe UI', 13),
                     text_color=MUTED).pack(side='right', padx=(5, 0))
        self.logo_slider = ctk.CTkSlider(
            controls, from_=48, to=132, number_of_steps=21,
            width=83, height=12, progress_color=self.accent,
            button_color='#B4C2FF', button_hover_color='#E0E6FF',
            command=self.resize_logos)
        self.logo_slider.pack(side='right')
        self.logo_slider.set(self.logo_size.get())
        ctk.CTkLabel(controls, text='▫', font=('Segoe UI', 13),
                     text_color=MUTED).pack(side='right', padx=(0, 4))
        bar = ctk.CTkFrame(main, fg_color='transparent')
        bar.pack(fill='x', padx=32, pady=(7, 17))
        self.search = ctk.CTkEntry(bar, textvariable=self.filter,
            placeholder_text='⌕  Search launchers...',
            height=43, corner_radius=12, fg_color=self.theme_colors['panel'],
            border_color=self.theme_colors['input_border'], text_color=TEXT,
            font=('Segoe UI', 13))
        self.search.pack(side='left', fill='x', expand=True)
        self.count = ctk.CTkLabel(bar, text='', text_color=MUTED,
                                  font=('Segoe UI', 12))
        self.count.pack(side='right', padx=(17, 0))
        self.scroll = ctk.CTkScrollableFrame(main, fg_color='transparent', corner_radius=0, scrollbar_button_color=self.theme_colors['border'], scrollbar_button_hover_color='#3B4A66')
        self.scroll.pack(fill='both', expand=True, padx=22, pady=(0, 20))
        # Avoid re-rendering on layout changes: this caused continuous tile flashing.
        self._render_job = None
        self.set_mode('All launchers')

    def save_preferences(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.preferences_path.write_text(json.dumps({
            'favorites': sorted(self.favorites),
            'order': self.launcher_order,
            'accent': self.accent_name,
            'custom_accent': self.custom_accent
        }, indent=2), encoding='utf-8')

    def open_theme_dialog(self):
        """CustomTkinter themed HSV wheel with live preview and hex input."""
        if getattr(self, '_theme_dialog', None) and self._theme_dialog.winfo_exists():
            self._theme_dialog.lift()
            return
        dialog = ctk.CTkToplevel(self)
        self._theme_dialog = dialog
        dialog.title('GameHub • Appearance')
        dialog.geometry('450x570')
        dialog.resizable(False, False)
        dialog.configure(fg_color=self.theme_colors['bg'])
        dialog.transient(self)
        dialog.lift()
        dialog.focus_force()
        ctk.CTkLabel(dialog, text='Customize GameHub', text_color=TEXT,
                     font=('Segoe UI Semibold', 22)).pack(anchor='w', padx=24, pady=(22, 2))
        ctk.CTkLabel(dialog, text='Choose an accent color for your dashboard',
                     text_color=MUTED, font=('Segoe UI', 12)).pack(anchor='w', padx=24)
        swatches = ctk.CTkFrame(dialog, fg_color='transparent')
        swatches.pack(fill='x', padx=23, pady=(18, 10))
        selected = tk.StringVar(value=self.accent)
        preview = ctk.CTkFrame(dialog, fg_color=self.theme_colors['panel'], corner_radius=12)
        preview.pack(fill='x', padx=24, pady=(0, 12))
        preview_label = ctk.CTkLabel(preview, text='●  Live color preview',
                                     text_color=self.accent, font=('Segoe UI Semibold', 13))
        preview_label.pack(pady=9)
        wheel_frame = ctk.CTkFrame(dialog, fg_color='transparent')
        wheel_frame.pack(pady=2)
        dim = 220
        wheel = tk.Canvas(wheel_frame, width=dim, height=dim, bd=0,
                          highlightthickness=0, bg=self.theme_colors['bg'])
        wheel.pack()
        # Hue is the angle; saturation is the distance from the center.
        image = Image.new('RGBA', (dim, dim), (0, 0, 0, 0))
        pix = image.load()
        center = (dim-1)/2
        radius = center-4
        for y in range(dim):
            for x in range(dim):
                dx, dy = x-center, center-y
                r = math.hypot(dx, dy)
                if r <= radius:
                    h = (math.atan2(dy, dx)/(2*math.pi)) % 1
                    sat = min(1.0, r/radius)
                    rgb = colorsys.hsv_to_rgb(h, sat, 1.0)
                    pix[x,y] = tuple(round(v*255) for v in rgb)+(255,)
        photo = ImageTk.PhotoImage(image)
        wheel._photo = photo
        wheel.create_image(0, 0, image=photo, anchor='nw')
        indicator = wheel.create_oval(0,0,0,0,outline='#101522',width=3)
        def set_color(hex_color):
            try:
                raw=hex_color.strip().lstrip('#')
                if len(raw)!=6: return
                rgb=tuple(int(raw[i:i+2],16)/255 for i in (0,2,4))
                hue, sat, val=colorsys.rgb_to_hsv(*rgb)
                selected.set('#'+raw.upper())
                preview_label.configure(text_color=selected.get())
                preview.configure(border_width=1, border_color=selected.get())
                wheel.coords(indicator,
                             center+radius*sat*math.cos(hue*2*math.pi)-6,
                             center-radius*sat*math.sin(hue*2*math.pi)-6,
                             center+radius*sat*math.cos(hue*2*math.pi)+6,
                             center-radius*sat*math.sin(hue*2*math.pi)+6)
                if hex_entry.get().upper()!=selected.get().upper():
                    hex_entry.delete(0,'end')
                    hex_entry.insert(0,selected.get())
            except (ValueError, tk.TclError):
                pass
        for name, color in ACCENTS.items():
            ctk.CTkButton(swatches, text='', width=43, height=31,
                          corner_radius=9, fg_color=color, hover_color=color,
                          border_width=1, border_color='#72809B',
                          command=lambda c=color: set_color(c)).pack(side='left', padx=4)
        def pick(event):
            dx,dy=event.x-center,center-event.y
            hue=(math.atan2(dy,dx)/(2*math.pi))%1
            sat=min(1,math.hypot(dx,dy)/radius)
            rgb=colorsys.hsv_to_rgb(hue,sat,1)
            set_color('#'+''.join(f'{round(v*255):02X}' for v in rgb))
        wheel.bind('<Button-1>',pick)
        wheel.bind('<B1-Motion>',pick)
        line = ctk.CTkFrame(dialog, fg_color='transparent')
        line.pack(fill='x',padx=26,pady=(14,10))
        ctk.CTkLabel(line,text='HEX',text_color=MUTED,font=('Segoe UI',12)).pack(side='left')
        hex_entry=ctk.CTkEntry(line,width=115,height=34,fg_color=self.theme_colors['panel'],
                               border_color=self.theme_colors['border'],text_color=TEXT)
        hex_entry.pack(side='left',padx=12)
        hex_entry.bind('<Return>',lambda e:set_color(hex_entry.get()))
        def apply():
            set_color(hex_entry.get())
            self.custom_accent=selected.get()
            self.change_accent('Custom')
            dialog.destroy()
        buttons=ctk.CTkFrame(dialog,fg_color='transparent')
        buttons.pack(fill='x',padx=24,pady=(7,0))
        ctk.CTkButton(buttons,text='Cancel',fg_color=self.theme_colors['panel'],
                      hover_color=self.theme_colors['hover'],width=135,
                      command=dialog.destroy).pack(side='left')
        ctk.CTkButton(buttons,text='Apply theme',fg_color=self.accent,
                      hover_color=self.theme_colors['hover'],width=170,
                      command=apply).pack(side='right')
        set_color(self.accent)

    def pick_custom_color(self):
        self.open_theme_dialog()

    def change_accent(self, name):
        self.accent_name = name
        self.accent = self.custom_accent if name == 'Custom' else ACCENTS[name]
        self.theme_colors = theme_palette(self.accent)
        self.save_preferences()
        # Rebuild the dashboard so the background, sidebar, search field and tiles
        # all receive the new color rather than changing only hover highlights.
        if self._render_job is not None:
            self.after_cancel(self._render_job)
            self._render_job = None
        for child in self.winfo_children():
            child.destroy()
        self.configure(fg_color=self.theme_colors['bg'])
        self.make_ui()

    def toggle_favorite(self, original):
        if original in self.favorites:
            self.favorites.remove(original)
        else:
            self.favorites.add(original)
        self.save_preferences()
        self.render()

    def poll_running(self):
        try:
            processes = {p.info['name'].lower() for p in psutil.process_iter(['name'])
                         if p.info.get('name')}
            for name, (path, dot) in list(self._running_dots.items()):
                if not dot.winfo_exists():
                    continue
                running = (Path(path).name.lower() in processes if not path.startswith('ms-')
                           else 'xboxpcapp.exe' in processes)
                dot.configure(text='●' if running else ' ')
        except (psutil.Error, OSError, tk.TclError):
            pass
        if not self._really_exit:
            self.after(4000, self.poll_running)

    def hide_to_tray(self):
        if self._really_exit:
            self.destroy()
            return
        self.withdraw()
        if self._tray is not None:
            return
        try:
            with Image.open(ASSETS / 'gamehub_icon.png') as image:
                tray_image = image.convert('RGBA').resize((64, 64))
            def show(icon=None, item=None):
                self.after(0, self.restore_from_tray)
            def quit_app(icon=None, item=None):
                self.after(0, self.quit_app)
            self._tray = pystray.Icon(
                'GameHub', tray_image, 'GameHub',
                pystray.Menu(pystray.MenuItem('Open GameHub', show, default=True),
                             pystray.MenuItem('Exit GameHub', quit_app)))
            threading.Thread(target=self._tray.run, daemon=True).start()
        except Exception:
            self.deiconify()
            self._tray = None

    def restore_from_tray(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def quit_app(self):
        self._really_exit = True
        if self._tray:
            self._tray.stop()
            self._tray = None
        self.destroy()

    def drag_start(self, event, name):
        self._drag_start = (name, event.x_root, event.y_root)
        self._dragged = False

    def drag_motion(self, event):
        if not self._drag_start:
            return
        _, x, y = self._drag_start
        if abs(event.x_root - x) + abs(event.y_root - y) > 12:
            self._dragged = True

    def drag_end(self, event, name):
        if not self._drag_start:
            return
        start_name = self._drag_start[0]
        self._drag_start = None
        if not self._dragged:
            return
        self._suppress_click = True
        self.after(200, lambda: setattr(self, '_suppress_click', False))
        target = None
        for other, tile in self._tiles.items():
            if tile.winfo_exists() and (
                tile.winfo_rootx() <= event.x_root < tile.winfo_rootx() + tile.winfo_width()
                and tile.winfo_rooty() <= event.y_root < tile.winfo_rooty() + tile.winfo_height()
            ):
                target = other
                break
        if not target or target == start_name:
            return
        all_names = list(dict.fromkeys(self.launcher_order + list(self.detected) + list(self.custom)))
        if start_name in all_names and target in all_names:
            all_names.remove(start_name)
            all_names.insert(all_names.index(target), start_name)
            self.launcher_order = all_names
            self.save_preferences()
            self.render()

    def save_view_settings(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.view_settings_path.write_text(json.dumps({
            'logo_only': self.logo_only.get(),
            'logo_size': self.logo_size.get()
        }, indent=2), encoding='utf-8')

    def change_view(self):
        self.save_view_settings()
        self.render()

    def resize_logos(self, value):
        size = int(round(value))
        if abs(size - self.logo_size.get()) < 3:
            return
        self.logo_size.set(size)
        self.save_view_settings()
        self.schedule_render()

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
        """Custom dark context popup instead of the classic native Tk menu."""
        if getattr(self, '_context_popup', None):
            try:
                self._context_popup.destroy()
            except tk.TclError:
                pass
        popup = ctk.CTkToplevel(self)
        self._context_popup = popup
        popup.withdraw()
        popup.overrideredirect(True)
        popup.attributes('-topmost', True)
        popup.configure(fg_color='#202A3B')
        outer = ctk.CTkFrame(popup, fg_color='#202A3B',
                             corner_radius=12, border_width=1,
                             border_color='#3A4B68')
        outer.pack(fill='both', expand=True, padx=1, pady=1)
        label = ctk.CTkLabel(outer, text=self.renamed.get(original, original),
                             text_color='#9FB0CD', font=('Segoe UI Semibold', 11),
                             anchor='w')
        label.pack(fill='x', padx=14, pady=(11, 5))
        def action(callback):
            popup.destroy()
            self._context_popup = None
            self.after(20, callback)
        def item(symbol, title, callback, danger=False):
            button = ctk.CTkButton(
                outer, text=f'  {symbol}    {title}', anchor='w', height=37,
                corner_radius=7, fg_color='transparent',
                hover_color='#33445E' if not danger else '#54313C',
                text_color='#F29AA7' if danger else '#E0E8F6',
                font=('Segoe UI', 12), border_width=0,
                command=lambda: action(callback))
            button.pack(fill='x', padx=7, pady=2)
        item('★' if original in self.favorites else '☆',
             'Unpin favorite' if original in self.favorites else 'Pin to favorites',
             lambda: self.toggle_favorite(original))
        item('✎', 'Rename launcher', lambda: self.edit_name(original))
        item('▧', 'Choose logo from computer', lambda: self.edit_logo(original))
        if original in self.custom_icons:
            item('↺', 'Reset logo', lambda: self.reset_logo(original))
        if original in self.renamed:
            item('↺', 'Reset name', lambda: self.reset_name(original))
        if original in self.custom:
            ctk.CTkFrame(outer, height=1, fg_color='#3A4B68').pack(
                fill='x', padx=13, pady=6)
            item('×', 'Remove launcher', lambda: self.remove_one(original), danger=True)
        ctk.CTkFrame(outer, height=7, fg_color='transparent').pack()
        popup.update_idletasks()
        w, h = 246, popup.winfo_reqheight()
        screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        x = max(0, min(event.x_root, screen_w - w - 8))
        y = max(0, min(event.y_root, screen_h - h - 8))
        popup.geometry(f'{w}x{h}+{x}+{y}')
        popup.deiconify()
        popup.lift()
        popup.focus_force()
        def dismiss(event=None):
            if popup.winfo_exists():
                popup.destroy()
            if self._context_popup is popup:
                self._context_popup = None
        popup.bind('<Escape>', dismiss)
        popup.bind('<FocusOut>', lambda e: popup.after(
            120, lambda: dismiss() if popup.winfo_exists() and
            self.focus_get() is None else None))
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
        self._tiles = {}
        self._running_dots = {}
        items = self.custom if self.mode == 'Custom apps' else {**self.detected, **self.custom}
        query = self.filter.get().strip().casefold()
        order_index = {name: i for i, name in enumerate(self.launcher_order)}
        items = [(name, path) for name, path in sorted(
            items.items(), key=lambda item: (
                0 if item[0] in self.favorites else 1,
                order_index.get(item[0], 100000),
                self.renamed.get(item[0], item[0]).casefold()
            )) if query in self.renamed.get(name, name).casefold()]
        self.count.configure(text=f'{len(items)} apps')
        compact = self.logo_only.get()
        size = self.logo_size.get()
        cols = 4 if not compact else max(4, min(8, 760 // (size + 26)))
        for col in range(8):
            self.scroll.grid_columnconfigure(col, weight=1 if col < cols else 0,
                                              uniform='apps' if col < cols else '')
        for idx, (name, path) in enumerate(items):
            row, col = divmod(idx, cols)
            tile_size = size + 24
            card = ctk.CTkFrame(
                self.scroll, fg_color='transparent' if compact else self.theme_colors['tile'],
                corner_radius=15 if compact else 17,
                border_width=0 if compact else 1,
                border_color=self.theme_colors['border'],
                width=tile_size if compact else 180,
                height=tile_size if compact else max(150, size + 88))
            card.grid(row=row, column=col, padx=7 if compact else 9,
                      pady=7 if compact else 10,
                      sticky='' if compact else 'nsew')
            card.grid_propagate(False)
            self._tiles[name] = card
            icon = self.get_icon(path, name)
            if icon:
                # CTkImage supports resizing the display without enlarging the source file.
                try:
                    icon.configure(size=(size, size))
                except (AttributeError, ValueError):
                    pass
                self.icon_refs.append(icon)
                logo = ctk.CTkLabel(card, image=icon, text='')
            else:
                logo = ctk.CTkLabel(card, text='◈', text_color='#A9B8FF',
                    font=('Segoe UI Semibold', max(24, size // 2)))
            logo.pack(expand=True, pady=(0, 0) if compact else (12, 0))
            title = None
            if not compact:
                title = ctk.CTkLabel(
                    card, text=self.renamed.get(name, name), text_color=TEXT,
                    font=('Segoe UI Semibold', 12), wraplength=150)
                title.pack(pady=(4, 14))
            dot = ctk.CTkLabel(card, text=' ', height=13,
                               font=('Segoe UI', 10), text_color=self.accent)
            dot.pack(side='bottom', pady=(0, 2))
            self._running_dots[name] = (path, dot)
            def launch_here(event=None, target=path):
                if not self._dragged and not self._suppress_click:
                    self.launch(target)
            def update_hover(tile=card, compact=compact):
                if not tile.winfo_exists():
                    return
                x, y = tile.winfo_pointerxy()
                inside = (tile.winfo_rootx() <= x < tile.winfo_rootx() + tile.winfo_width()
                          and tile.winfo_rooty() <= y < tile.winfo_rooty() + tile.winfo_height())
                base = self.theme_colors['bg'] if compact else self.theme_colors['tile']
                target = self.theme_colors['hover'] if inside else base
                previous_job = getattr(tile, '_hover_job', None)
                if previous_job is not None:
                    try: tile.after_cancel(previous_job)
                    except tk.TclError: pass
                def rgb(c):
                    return tuple(int(c[i:i+2],16) for i in (1,3,5))
                try:
                    current = tile.cget('fg_color')
                    if not isinstance(current,str) or not current.startswith('#'):
                        current = base
                    a,b=rgb(current),rgb(target)
                except (ValueError,tk.TclError):
                    return
                def frame(step):
                    if not tile.winfo_exists(): return
                    t=1-(1-step/6)**2
                    color='#'+''.join(f'{round(v+(w-v)*t):02X}' for v,w in zip(a,b))
                    try:
                        tile.configure(fg_color=color,
                                       border_color=self.accent if inside else self.theme_colors['border'])
                        if step<6:
                            tile._hover_job=tile.after(17,lambda:frame(step+1))
                        else: tile._hover_job=None
                    except tk.TclError: pass
                frame(1)
            widgets = (card, logo) + ((title,) if title else ())
            for widget in widgets:
                widget.bind('<ButtonPress-1>', lambda e, n=name: self.drag_start(e, n))
                widget.bind('<B1-Motion>', self.drag_motion)
                widget.bind('<ButtonRelease-1>', lambda e, n=name, target=path: (
                    self.drag_end(e, n), self.launch(target) if not self._dragged and not self._suppress_click else None))

                widget.bind('<Button-3>', lambda e, original=name: self.launcher_menu(e, original))
                widget.bind('<Enter>', lambda e, fn=update_hover: self.after_idle(fn))
                widget.bind('<Leave>', lambda e, fn=update_hover: self.after_idle(fn))
                widget.configure(cursor='hand2')
            if compact:
                # Names are still available as tooltips via native Tk hover timing.
                tip = self.renamed.get(name, name)
                logo.bind('<Button-3>', lambda e, original=name: self.launcher_menu(e, original))
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
