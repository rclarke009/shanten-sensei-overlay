""" GUI common/utility functions"""
import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageDraw, ImageFont, ImageTk

from common.mj_helper import MJAI_TILE_2_UNICODE, ActionUnicode


# Review-page aligned dark palette
_DARK_BG = "#1a1f24"
_DARK_PANEL = "#242b33"
_DARK_TEXT = "#e8eef4"
_DARK_MUTED = "#9aabba"
_DARK_LINE = "#3a4550"
_DARK_HOVER = "#314052"
_DARK_HOVER_TIP = "#2c343d"
_BTN_GREEN = "#4CAF50"
_BTN_GREEN_ACTIVE = "#66BB6A"


class GuiStyle:
    """ GUI Style Class"""
    def __init__(self, std_font_size:int=12):
        self.std_font_size = std_font_size
        self.font_size = std_font_size
        self.dpi_scale:float = 1.0
        self.dark: bool = False

    @property
    def bg(self) -> str:
        return _DARK_BG if self.dark else "SystemButtonFace"

    @property
    def panel(self) -> str:
        return _DARK_PANEL if self.dark else "SystemButtonFace"

    @property
    def text(self) -> str:
        return _DARK_TEXT if self.dark else "SystemButtonText"

    @property
    def muted(self) -> str:
        return _DARK_MUTED if self.dark else "SystemButtonText"

    @property
    def line(self) -> str:
        return _DARK_LINE if self.dark else "gray"

    @property
    def hover_bg(self) -> str:
        return _DARK_HOVER if self.dark else "light blue"

    @property
    def hover_tip_bg(self) -> str:
        return _DARK_HOVER_TIP if self.dark else "lightyellow"

    def set_style_normal(self, style:ttk.Style, dark: bool = False):
        """ Set style for ttk widgets; dark uses clam so colors stick on macOS."""
        self.dark = dark
        if dark:
            style.theme_use("clam")
            style.configure(
                ".",
                background=_DARK_BG,
                foreground=_DARK_TEXT,
                fieldbackground=_DARK_PANEL,
                troughcolor=_DARK_PANEL,
                bordercolor=_DARK_LINE,
                lightcolor=_DARK_LINE,
                darkcolor=_DARK_BG,
            )
            style.configure(
                "TLabel",
                background=_DARK_BG,
                foreground=_DARK_TEXT,
                font=("Microsoft YaHei", self.font_size),
            )
            style.configure("TFrame", background=_DARK_BG)
            style.configure(
                "TCheckbutton",
                background=_DARK_BG,
                foreground=_DARK_TEXT,
                font=("Microsoft YaHei", self.font_size),
            )
            style.map(
                "TCheckbutton",
                background=[("active", _DARK_BG), ("selected", _DARK_BG)],
                foreground=[("active", _DARK_TEXT)],
            )
            style.configure(
                "TCombobox",
                fieldbackground=_DARK_PANEL,
                background=_DARK_PANEL,
                foreground=_DARK_TEXT,
                arrowcolor=_DARK_TEXT,
            )
            style.map(
                "TCombobox",
                fieldbackground=[("readonly", _DARK_PANEL)],
                selectbackground=[("readonly", _DARK_HOVER)],
                selectforeground=[("readonly", _DARK_TEXT)],
            )
            style.configure(
                "TEntry",
                fieldbackground=_DARK_PANEL,
                foreground=_DARK_TEXT,
                insertcolor=_DARK_TEXT,
            )
            style.configure(
                "TButton",
                background=_BTN_GREEN,
                foreground="white",
                font=("Microsoft YaHei", self.font_size),
                relief="raised",
                borderwidth=2,
            )
            style.map(
                "TButton",
                background=[("active", _BTN_GREEN_ACTIVE), ("disabled", _DARK_LINE)],
                foreground=[("disabled", _DARK_MUTED)],
            )
            style.configure("TSeparator", background=_DARK_LINE)
        else:
            for name in ("aqua", "vista", "xpnative", "winnative", "default", "clam"):
                if name in style.theme_names():
                    try:
                        style.theme_use(name)
                        break
                    except tk.TclError:
                        continue
            style.configure("TLabel", font=("Microsoft YaHei", self.font_size))
            style.configure(
                "TButton",
                background=_BTN_GREEN, foreground="black",
                font=("Microsoft YaHei", self.font_size),
                relief="raised",
                borderwidth=2,
            )

    def paint_root(self, root: tk.Misc):
        """Paint a toplevel/root and common chrome when dark."""
        if not self.dark:
            return
        try:
            root.configure(bg=_DARK_BG)
        except tk.TclError:
            pass

    def paint_frame(self, frame: tk.Misc):
        """Paint a bare tk.Frame (and similar) when dark."""
        if not self.dark:
            return
        try:
            frame.configure(bg=_DARK_BG, highlightbackground=_DARK_LINE)
        except tk.TclError:
            try:
                frame.configure(bg=_DARK_BG)
            except tk.TclError:
                pass

    def sunken_kwargs(self) -> dict:
        """Kwargs for sunken tk.Label panels."""
        if not self.dark:
            return {}
        return {
            "bg": _DARK_PANEL,
            "fg": _DARK_TEXT,
            "highlightbackground": _DARK_LINE,
        }

    def text_kwargs(self) -> dict:
        """Kwargs for ScrolledText / Text widgets."""
        if not self.dark:
            return {}
        return {
            "bg": _DARK_PANEL,
            "fg": _DARK_TEXT,
            "insertbackground": _DARK_TEXT,
            "highlightbackground": _DARK_LINE,
            "selectbackground": _DARK_HOVER,
            "selectforeground": _DARK_TEXT,
        }

    def font_normal(self, family:str=None, size:int=None):
        """ return normal font for gui/widgets"""
        if not family:
            family = "Microsoft YaHei"
        if not size:
            size = self.font_size
        else:
            size = int(size / self.dpi_scale)        
        return (family, size)
    

    def set_dpi_scaling(self, scale:float=1.0):
        """ set dpi scaling, change font size accordingly"""
        self.dpi_scale = scale
        self.font_size = int(self.std_font_size / scale)


def add_hover_text(widget:tk.Widget, text:str):
    """ Add a hover string label when mouse is over the widget"""
    widget.bind("<Enter>", lambda event: _on_hover(widget, text))
    widget.bind("<Leave>", lambda event: _on_leave_hover(widget))
    
    
def _on_hover(wdg:tk.Widget, text:str):
    # display a hover label with text
    toplvl = wdg.winfo_toplevel()
    try:
        wdg.original_bg = wdg.cget("background")
        wdg.configure(background=GUI_STYLE.hover_bg)
    except tk.TclError:
        wdg.original_bg = None
    tip_kwargs = {
        "text": text,
        "bg": GUI_STYLE.hover_tip_bg,
        "highlightbackground": GUI_STYLE.line if GUI_STYLE.dark else "black",
        "highlightthickness": 1,
    }
    if GUI_STYLE.dark:
        tip_kwargs["fg"] = _DARK_TEXT
    wdg.hover_text = tk.Label(toplvl, **tip_kwargs)
    x = wdg.winfo_rootx() - toplvl.winfo_rootx() + wdg.winfo_width()
    y = wdg.winfo_rooty() - toplvl.winfo_rooty() + wdg.winfo_height() //2
    wdg.hover_text.place(x=x, y=y, anchor=tk.W)
    

def _on_leave_hover(wdg:tk.Widget):
    # destroy the hover label
    if hasattr(wdg, "hover_text"):
        wdg.hover_text.destroy()
    if hasattr(wdg, "original_bg") and wdg.original_bg is not None:
        try:
            wdg.configure(background=wdg.original_bg)
        except tk.TclError:
            pass
        

def crop_image_from_top_left(image:Image, width, height):
    # Get the size of the original image
    original_width, original_height = image.size
    
    # Calculate the coordinates of the cropping box
    left = 0
    top = 0
    right = min(original_width, width)
    bottom = min(original_height, height)
    
    # Crop the image
    cropped_image = image.crop((left, top, right, bottom))    
    return cropped_image

def text_to_image(size:int, text:str, width:int=800, height:int=600):
    """ create image based on the text content"""
    
    # draw emojis and regular text in different fonts
    ft_emj = ImageFont.truetype(font="seguiemj.ttf", size=size)
    ft_txt = ImageFont.truetype(font="msyh.ttf", size=size)
    line_spacing = int(size/2)
    pad_x = int(size/2)
    pad_y = int(size/2)
    dummy_img = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)   

    cur_x = pad_x
    cur_y = pad_y + line_spacing
    
    # Create the image with calculated dimensions
    im = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(im)
    
    # draw text each line and each character, record line width and total height
    max_width = 1
    lines = text.split("\n")
    for l in lines:
        for c in l:
            if c in MJAI_TILE_2_UNICODE.values():
                ft = ft_emj
            else:
                ft = ft_txt
            bbox = dummy_draw.textbbox((0, 0), c, font=ft, embedded_color=True, spacing=line_spacing)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            draw.text((cur_x,cur_y), c, font=ft, embedded_color=True, anchor="lm", fill="black", spacing=line_spacing)
            cur_x += text_w
        max_width = max(cur_x,max_width)
        cur_x = pad_x
        cur_y += size + line_spacing
        
    # crop image to fit the text
    max_width += pad_x
    max_height = cur_y - line_spacing   # mid > top    
    im = crop_image_from_top_left(im, max_width, max_height)

    return ImageTk.PhotoImage(im)


# Approximate height of both toolbar rows (icon row + toggles) for geometry shrink
TOOLBAR_COLLAPSE_DELTA = 156


def window_size(hide_ai_options: bool, hide_toolbars: bool = False) -> tuple[int, int]:
    """Base coaching window size; shrink when setup toolbars are collapsed."""
    width, height = (480, 620) if hide_ai_options else (620, 620)
    if hide_toolbars:
        height = max(height - TOOLBAR_COLLAPSE_DELTA, 300)
    return width, height


GUI_STYLE = GuiStyle()
