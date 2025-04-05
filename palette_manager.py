import json
import numpy as np
import colorsys
from collections import deque
from coldtype import *
from pypalettes import load_cmap, get_colors


# Helper function for sorting keys with error handling
def _get_hls_hue_safe(hex_color):
    try:
        r = int(hex_color[1:3], 16) / 255.0
        g = int(hex_color[3:5], 16) / 255.0
        b = int(hex_color[5:7], 16) / 255.0
        hls = colorsys.rgb_to_hls(r, g, b)
        return hls[0] # Return hue
    except (ValueError, IndexError, TypeError) as e:
        print(f"Warning: Error getting HLS hue for sorting color '{hex_color}': {e}. Using hue 0.0.")
        return 0.0 # Return default hue on error

class PaletteManager:
    def __init__(self, config_path="palette_config.json"):
        self.config_path = config_path
        self.palette_names = list(get_colors._load_palettes().keys())
        self.palette = []
        self.palette_hex = []
        self.colors = {}
        self.current_palette_name = ""
        self.config = self._load_config() # Load config first
        self._load_base_palette()      # Load base palette based on config index
        # Note: Transforms are NOT automatically applied on init
        print(f"Initialized PaletteManager: Loaded base palette '{self.current_palette_name}' ({self.config.get('palette_idx')}) with {len(self.palette)} colors.")

    def _load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
                # Ensure essential keys have defaults if missing
                config_data.setdefault("palette_idx", 836)
                config_data.setdefault("seed", 42)
                config_data.setdefault("rotate_amount", 0)
                config_data.setdefault("max_colors", 16)
                config_data.setdefault("color_indices", {"bg": 0.06, "fg": 0.62})
                return config_data
        except FileNotFoundError:
            print(f"Config file '{self.config_path}' not found. Using default configuration.")
            # Return a copy of the default config
            return {
                "palette_idx": 836,
                "seed": 42,
                "rotate_amount": 0,
                "max_colors": 16,
                "color_indices": {
                    "bg": 0.06,
                    "fg": 0.62,
                }
            }

    def save_config(self):
        """Saves the current in-memory configuration to the JSON file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to '{self.config_path}'.")
        except Exception as e:
            print(f"Error saving configuration to '{self.config_path}': {e}")
        return self # Allow chaining

    def update_config(self, key, value):
        """Updates a configuration value in memory. Does not save automatically."""
        if key in self.config:
            self.config[key] = value
            print(f"Config updated: {key} = {value}")
            # Consider if certain updates should trigger a reload or partial update?
            # For now, requires manual reload() or specific method calls.
        else:
            print(f"Warning: Config key '{key}' not found.")
        return self # Allow chaining

    def reload(self):
        """Reloads config from file, reloads base palette, applies config transforms."""
        print(f"Reloading configuration from '{self.config_path}'...")
        self.config = self._load_config()
        self._load_base_palette()
        self.apply_config_transforms()
        # Status printed by apply_config_transforms
        return self

    def _load_base_palette(self):
        """(Internal) Loads the raw palette from source based on config, before transforms."""
        palette_idx = self.config.get("palette_idx", 836)
        max_colors = self.config.get("max_colors", 16)

        if not (0 <= palette_idx < len(self.palette_names)):
            print(f"Warning: palette_idx {palette_idx} out of bounds. Correcting to 0.")
            palette_idx = 0
            self.config["palette_idx"] = 0

        self.current_palette_name = self.palette_names[palette_idx]
        try:
            cmap = load_cmap(self.current_palette_name)
        except Exception as e:
            print(f"Error loading cmap '{self.current_palette_name}': {e}. Using empty palette.")
            self.palette_hex = []
            self.palette = []
            return

        # Sample and sort colors
        if len(cmap.colors) > max_colors:
            try:
                sorted_colors = sorted(cmap.colors, key=_get_hls_hue_safe)
                step = len(sorted_colors) // (max_colors - 1) if max_colors > 1 else 1
                base_hex = [sorted_colors[i * step] for i in range(max_colors)]
                if max_colors > 0 and sorted_colors[-1] not in base_hex:
                    base_hex[-1] = sorted_colors[-1]
            except Exception as e:
                 print(f"Error during color sorting/sampling for '{self.current_palette_name}': {e}. Using unsorted colors.")
                 base_hex = list(cmap.colors)[:max_colors]
        else:
            base_hex = list(cmap.colors)

        self.palette_hex = base_hex
        # Convert hex to HSL objects
        new_palette = []
        for c in self.palette_hex:
            try:
                r = int(c[1:3], 16) / 255.0
                g = int(c[3:5], 16) / 255.0
                b = int(c[5:7], 16) / 255.0
                hls_tuple = colorsys.rgb_to_hls(r, g, b)
                h, l, s = hls_tuple
                new_palette.append(hsl(h, s, l))
            except (ValueError, IndexError, TypeError) as e:
                print(f"Warning: Error converting hex '{c}' to HSL: {e}. Appending black.")
                new_palette.append(hsl(0, 0, 0))
        self.palette = new_palette
        # Do not assign named colors here, happens after transforms

    def apply_config_transforms(self):
        """Applies shuffle and rotate based on current config values."""
        seed = self.config.get("seed")
        rotate_amount = self.config.get("rotate_amount")
        print(f"Applying config transforms: Seed={seed}, Rotation={rotate_amount}")
        self._shuffle(seed) # Use internal shuffle
        self._rotate(rotate_amount) # Use internal rotate
        self._assign_named_colors()
        self._print_status("Applied config transforms")
        return self

    # public chainable methods
    def shuffle(self, seed=None):
        """Shuffles the palette with a specific seed (or config seed if None)."""
        current_seed = seed if seed is not None else self.config.get("seed")
        self._shuffle(current_seed)
        self._assign_named_colors()
        self._print_status(f"Shuffled with seed {current_seed}")
        return self

    def rotate(self, amount=None):
        """Rotates the palette by a specific amount (or config amount if None)."""
        rotate_amount = amount if amount is not None else self.config.get("rotate_amount")
        self._rotate(rotate_amount)
        self._assign_named_colors()
        self._print_status(f"Rotated by {rotate_amount}")
        return self

    # Internal, non-chainable versions for use by apply_config_transforms
    def _shuffle(self, seed):
        if not self.palette: return
        if seed is None: seed = 42 # Default if absolutely no seed found

        rng = np.random.default_rng(seed=int(seed))
        indices = np.arange(len(self.palette))
        rng.shuffle(indices)
        self.palette = [self.palette[i] for i in indices]
        self.palette_hex = [self.palette_hex[i] for i in indices]

    def _rotate(self, amount):
        if not self.palette: return
        if amount is None: amount = 0 # Default if no amount found

        num_colors = len(self.palette)
        if num_colors == 0: return
        rotate_amount = int(amount) % num_colors

        if rotate_amount != 0:
            palette_deque = deque(self.palette)
            palette_deque.rotate(rotate_amount)
            self.palette = list(palette_deque)
            hex_deque = deque(self.palette_hex)
            hex_deque.rotate(rotate_amount)
            self.palette_hex = list(hex_deque)

    def _assign_named_colors(self):
        """(Internal) Assigns named colors based on current palette order and config."""
        self.colors = {}
        num_palette_colors = len(self.palette)
        if num_palette_colors == 0: return

        color_indices = self.config.get("color_indices", {})
        for name, index_ratio in color_indices.items():
            idx = int(float(index_ratio) * num_palette_colors) % num_palette_colors
            self.colors[name] = self.palette[idx]

    def _print_status(self, action="Status"):
        """(Internal) Helper to print current status."""
        palette_idx = self.config.get("palette_idx", "N/A")
        # Note: These reflect config values, not necessarily the state after manual calls
        seed = self.config.get("seed", "N/A")
        rotate_amount = self.config.get("rotate_amount", "N/A")
        print(f"{action}: Palette '{self.current_palette_name}' ({palette_idx}), {len(self.palette)} colors (Config Seed: {seed}, Config Rotation: {rotate_amount}) Named: {list(self.colors.keys())}")

    def load_palette_by_index(self, index):
        """Loads a new base palette by index and applies config transforms."""
        self.update_config("palette_idx", index) # Update config
        self._load_base_palette() # Load new base
        self.apply_config_transforms() # Apply transforms from (potentially updated) config
        return self

    def get_color(self, name):
        """Gets a named color (e.g., 'bg', 'fg'). Returns black if not found."""
        return self.colors.get(name, hsl(0,0,0))

    def __len__(self):
        return len(self.palette)

    def __getitem__(self, index):
        """Gets a color by index (e.g., pm[0]), wraps around. Returns black if palette empty."""
        if not self.palette:
             return hsl(0,0,0)
        return self.palette[index % len(self.palette)]

    def preview(self, rect: Rect, font_name="Azeret", font_size=12, label_offset=3):
        """Creates a visual preview of the current palette within the given rect."""
        box = P()
        if len(self.palette) == 0:
            return box # Return empty P if no palette

        preview_rect = rect.inset(10) # Add some padding
        s = Scaffold(preview_rect).grid(1, len(self.palette)) # Grid for colors

        # Add palette name label
        try:
            name_style = Style(font_name, font_size * 1.2, load_font=True, wght=0.4)
            box += (
                StSt(self.current_palette_name, name_style)
                .f(self[len(self)//2]) # Use middle color for name
                .align(preview_rect, "NW")
            )
        except Exception as e:
            print(f"Warning: Could not render palette name preview: {e}")

        # Add color boxes and hex labels
        label_style = Style(font_name, font_size, load_font=True, wght=0.60)
        for i, cell in enumerate(s):
            # Color box
            box.append(
                P().rect(cell).fssw(self[i], bw(0), 3)
            )
            # Hex label
            try:
                 box.append(
                    StSt(self.palette_hex[i], label_style)
                    .f(self[(i + label_offset) % len(self)]) # Offset label color
                    .align(cell)
                )
            except Exception as e:
                 print(f"Warning: Could not render hex label preview for {self.palette_hex[i]}: {e}")

        return box
