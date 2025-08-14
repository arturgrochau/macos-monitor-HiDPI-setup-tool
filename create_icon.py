#!/usr/bin/env python3
"""
Create an icon for Monitor Layout Manager
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

import os

def create_app_icon():
    """Create a simple app icon using PIL or system tools."""
    
    if not PIL_AVAILABLE:
        print("📝 PIL not available, creating placeholder icon...")
        # Create a simple text file as placeholder
        with open("icon.txt", "w") as f:
            f.write("Monitor Layout Manager Icon Placeholder")
        return
    
    # Create a 1024x1024 icon (macOS standard)
    size = 1024
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background with gradient-like effect
    for i in range(size // 10):
        alpha = int(200 * (i / (size // 10)))
        color = (60, 120, 216, 50 + alpha)  # Blue gradient
        margin = i * 10
        if size - margin * 2 > 0:
            draw.rectangle([margin, margin, size - margin, size - margin], fill=color)
    
    # Draw monitor representations
    monitor_width = size // 4
    monitor_height = monitor_width * 3 // 4
    
    # Main monitor (larger)
    main_x = size // 2 - monitor_width // 2
    main_y = size // 2 - monitor_height // 2
    draw.rectangle([main_x, main_y, main_x + monitor_width, main_y + monitor_height], 
                   fill=(255, 255, 255, 255), outline=(50, 50, 50, 255), width=4)
    
    # Secondary monitor (smaller, to the right)
    sec_width = monitor_width * 3 // 4
    sec_height = monitor_height * 3 // 4
    sec_x = main_x + monitor_width + 20
    sec_y = main_y + 10
    draw.rectangle([sec_x, sec_y, sec_x + sec_width, sec_y + sec_height],
                   fill=(240, 240, 240, 255), outline=(50, 50, 50, 255), width=3)
    
    # Add some decorative elements
    center_x, center_y = size // 2, size // 2
    
    # Connection line between monitors
    draw.line([main_x + monitor_width, center_y, sec_x, sec_y + sec_height // 2],
              fill=(100, 100, 100, 200), width=3)
    
    # Save as PNG first
    img.save('app_icon.png')
    print(f"✅ Created app_icon.png ({size}x{size})")
    
    # Try to create ICNS file using system tools
    try:
        os.system('mkdir -p app_icon.iconset')
        # Create different sizes for iconset
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        for s in sizes:
            resized = img.resize((s, s), Image.Resampling.LANCZOS)
            resized.save(f'app_icon.iconset/icon_{s}x{s}.png')
            if s <= 512:  # Also create @2x versions
                resized.save(f'app_icon.iconset/icon_{s//2}x{s//2}@2x.png')
        
        # Convert to ICNS using iconutil
        result = os.system('iconutil -c icns app_icon.iconset -o app_icon.icns')
        if result == 0:
            print("✅ Created app_icon.icns")
            os.system('rm -rf app_icon.iconset')
        else:
            print("⚠️  Could not create ICNS, using PNG")
            
    except Exception as e:
        print(f"⚠️  Icon conversion failed: {e}")

if __name__ == "__main__":
    create_app_icon()
