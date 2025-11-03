#!/usr/bin/env python3
"""
Script to generate logo files in various formats from SVG source
"""
import os
from PIL import Image, ImageDraw
import cairosvg
import io

def svg_to_png(svg_path, png_path, size):
    """Convert SVG to PNG with specified size"""
    try:
        # Convert SVG to PNG using cairosvg
        png_data = cairosvg.svg2png(url=svg_path, output_width=size, output_height=size)
        
        # Save PNG
        with open(png_path, 'wb') as f:
            f.write(png_data)
        
        print(f"Created: {png_path} ({size}x{size})")
        return True
    except Exception as e:
        print(f"Error creating {png_path}: {e}")
        return False

def create_ico_file(png_paths, ico_path):
    """Create ICO file from multiple PNG files"""
    try:
        images = []
        for png_path in png_paths:
            if os.path.exists(png_path):
                img = Image.open(png_path)
                images.append(img)
        
        if images:
            images[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in images])
            print(f"Created: {ico_path}")
            return True
    except Exception as e:
        print(f"Error creating ICO: {e}")
        return False

def main():
    logo_dir = "/home/kjell/git_prosjekt/imalink/fase1/logo"
    svg_file = os.path.join(logo_dir, "imalink_logo.svg")
    
    if not os.path.exists(svg_file):
        print(f"SVG file not found: {svg_file}")
        return
    
    # Standard icon sizes
    sizes = [16, 24, 32, 48, 64, 128, 256, 512]
    png_files = []
    
    print("Generating PNG files...")
    for size in sizes:
        png_file = os.path.join(logo_dir, f"imalink_icon_{size}.png")
        if svg_to_png(svg_file, png_file, size):
            png_files.append(png_file)
    
    # Create ICO file for Windows
    print("\nCreating ICO file...")
    ico_file = os.path.join(logo_dir, "imalink_icon.ico")
    create_ico_file(png_files[:6], ico_file)  # Use first 6 sizes for ICO
    
    # Create Apple Touch Icon
    print("\nCreating Apple Touch Icon...")
    apple_icon = os.path.join(logo_dir, "apple-touch-icon.png")
    svg_to_png(svg_file, apple_icon, 180)
    
    # Create favicon
    print("\nCreating favicon...")
    favicon = os.path.join(logo_dir, "favicon.ico")
    small_pngs = [png for png in png_files if "16" in png or "32" in png or "48" in png]
    create_ico_file(small_pngs, favicon)
    
    print("\nLogo generation complete!")
    print(f"Files created in: {logo_dir}")

if __name__ == "__main__":
    main()