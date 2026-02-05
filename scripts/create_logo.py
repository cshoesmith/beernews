#!/usr/bin/env python3
"""Create a horizontal logo for The Sydney Beer Herald that fits the masthead."""

from PIL import Image, ImageDraw, ImageFont
import os

# Logo dimensions - wide and short for horizontal header
WIDTH = 450
HEIGHT = 70

# Colors - matching newspaper aesthetic
BLACK = '#1a1a1a'
DARK_GRAY = '#444444'
GOLD = '#b8860b'  # Dark goldenrod for beer

def create_logo():
    # Create image with transparent background
    img = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Use default font since custom fonts aren't available
    try:
        # Try different font paths
        font_paths = [
            "C:/Windows/Fonts/Georgia.ttf",
            "C:/Windows/Fonts/times.ttf", 
            "C:/Windows/Fonts/arial.ttf",
        ]
        
        title_font = None
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    title_font = ImageFont.truetype(fp, 28)
                    small_font = ImageFont.truetype(fp, 12)
                    break
                except:
                    continue
        
        if not title_font:
            title_font = ImageFont.load_default()
            small_font = title_font
            
    except Exception as e:
        title_font = ImageFont.load_default()
        small_font = title_font
    
    # Draw hop icon on the left
    hop_center_x = 25
    hop_center_y = HEIGHT // 2
    
    # Draw a simple stylized hop cone
    # Main body - teardrop shape using ellipse
    draw.ellipse([hop_center_x - 12, hop_center_y - 15, hop_center_x + 12, hop_center_y + 15], 
                 fill=GOLD, outline=BLACK, width=2)
    
    # Inner details (lines)
    draw.line([(hop_center_x, hop_center_y - 15), (hop_center_x, hop_center_y + 10)], 
              fill=BLACK, width=1)
    draw.line([(hop_center_x - 6, hop_center_y - 10), (hop_center_x - 6, hop_center_y + 5)], 
              fill=BLACK, width=1)
    draw.line([(hop_center_x + 6, hop_center_y - 10), (hop_center_x + 6, hop_center_y + 5)], 
              fill=BLACK, width=1)
    
    # Stem
    draw.line([(hop_center_x, hop_center_y - 15), (hop_center_x, hop_center_y - 25)], 
              fill=BLACK, width=2)
    
    # Draw text
    text_x = 50
    text_y = 15
    
    # "THE SYDNEY" - smaller, on top
    draw.text((text_x, text_y), "THE SYDNEY", font=small_font, fill=DARK_GRAY)
    
    # "BEER HERALD" - larger, main title
    draw.text((text_x, text_y + 14), "BEER HERALD", font=title_font, fill=BLACK)
    
    # Decorative underline
    line_y = HEIGHT - 12
    draw.line([(text_x, line_y), (WIDTH - 30, line_y)], fill=BLACK, width=2)
    
    # Small beer mug on the right
    mug_x = WIDTH - 25
    mug_y = HEIGHT // 2 - 8
    
    # Mug body
    draw.rectangle([mug_x, mug_y + 5, mug_x + 12, mug_y + 20], 
                   fill=GOLD, outline=BLACK, width=1)
    # Handle
    draw.arc([mug_x + 10, mug_y + 8, mug_x + 18, mug_y + 17], 
             start=270, end=90, fill=BLACK, width=2)
    # Foam
    for i, fx in enumerate([mug_x - 2, mug_x + 3, mug_x + 8]):
        draw.ellipse([fx, mug_y, fx + 6, mug_y + 8], fill='white', outline=BLACK, width=1)
    
    return img

def create_simple_text_logo():
    """Create a simple text-only logo."""
    WIDTH = 400
    HEIGHT = 60
    
    img = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font_paths = [
            "C:/Windows/Fonts/Georgia.ttf",
            "C:/Windows/Fonts/times.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        
        font = None
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    font = ImageFont.truetype(fp, 32)
                    break
                except:
                    continue
        
        if not font:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    text = "THE SYDNEY BEER HERALD"
    
    # Get text size for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (WIDTH - text_width) // 2
    y = (HEIGHT - text_height) // 2 - 5
    
    # Draw text
    draw.text((x, y), text, font=font, fill=BLACK)
    
    # Draw underline
    line_y = y + text_height + 2
    draw.line([(x, line_y), (x + text_width, line_y)], fill=BLACK, width=2)
    
    return img

# Create both versions
logo1 = create_logo()
logo2 = create_simple_text_logo()

# Save logos
output_dir = os.path.join(os.path.dirname(__file__), '..', 'public')

logo1_path = os.path.join(output_dir, 'SBH_logo.png')
logo1.save(logo1_path, 'PNG')
print(f"Created: {logo1_path}")

logo2_path = os.path.join(output_dir, 'SBH_logo_simple.png')
logo2.save(logo2_path, 'PNG')
print(f"Created: {logo2_path}")
