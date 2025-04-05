from coldtype import *
from coldtype.fx.skia import *

import numpy as np

from palette_manager import PaletteManager

midi = MidiTimeline(ººsiblingºº("media/quarters.mid"))

font_name = "ObviouslyVariable.ttf"
font_size = 751

font_axes = {
  "wght": 0.35,
  "ital": 0.29,
  "wdth": 0.38,
  "tu": 24,
  "leading": 64
}

pm = PaletteManager()
pm.apply_config_transforms() # Apply settings from config

# Optional: Apply manual overrides
(
    pm
    .load_palette_by_index(
        628).shuffle(seed=
        155).rotate(
        6)
)

# pm.save_config()

aspect = 16/9
width = 1920
height = width / aspect
dims = (width,height)

@animation(dims, tl=midi)
def scratch(f:Frame):
  all_four = midi.ki(24)
  downbeats = midi.ki(25)
  upbeats = midi.ki(26)

  composition = P()

  # Draw background first
  composition += P().rect(f.a.r).f(pm.get_color('bg')) # Use named color for background

  # Add ornaments
  composition += (
    P(
      [StSt(
        "m",
        font_name,
        font_size,
        **font_axes
      )
      .scale(2.80)
      for x in range(4)]
    )
    .mapv(lambda e,p: p
      .rotate(e*132*upbeats.adsr((10,10),rng=(0.84,0.82)))
      .scale(3.23,2.09)
      .align(f.a.r,
        "NE" if e==0 else
        "NW" if e==1 else
        "SW" if e==2 else
        "SE" if e==3 else
        None
      )
    )
    .scale(0.31*all_four.adsr((10,10),rng=(0.8,0.73)))
    .align(f.a.r, "C")
    .ch(phototype(f.a.r, 2.57, 83, 26, pm[1])) # Example using indexed color
  )

  composition += (
    P(
      [StSt(
        "=",
        font_name,
        font_size*1.5,
        **font_axes
      )
      for x in range(3)]
    )
    .mapv(lambda e,p: p
      .rotate(e*115*downbeats.adsr((10,10),rng=(0.90,0.95)))
      .scale(1.40,1.37)
      .align(f.a.r,
        "NE" if e==0 else
        "NW" if e==1 else
        "SW" if e==2 else
        "SE" if e==3 else
        None
      )
    )
    .rotate(-86)
    .scale(1.30,0.41)
    .align(f.a.r, "C")
    .ch(phototype(f.a.r, 1.06, 64, 23, pm.get_color('fg'))) # Example using named color
  )

  composition += (
    P(
      [StSt(
        "*",
        font_name,
        font_size,
        **font_axes
      )
      for x in range(4)]
    )
    .mapv(lambda e,p: p
      .rotate(23*all_four.adsr((10,10),rng=(0.58,0.95)))
      .scale(1.32,1.84)
      .offset(1.0*np.pow(10,3)*np.sin(2*e), 3.3*np.pow(10,3)*np.sin(3*e))
    )
    .rotate(-9)
    .scale(0.70,0.21)
    .align(f.a.r,"C")
    .ch(phototype(f.a.r, 1.47, 64, 23, pm.get_color('accent'))) # Example using named color
  )

  # Add palette preview
  preview_rect = f.a.r.take(1.00, "N").take(0.05, "E").inset(12) 
  composition += pm.preview(preview_rect, font_size=0)

  return composition
