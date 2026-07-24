import sys
import os
import argparse
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow library is not installed. Please install it using 'pip install Pillow'")
    sys.exit(1)

def crop_to_square(image_path):
    path = Path(image_path)
    if not path.is_file():
        return
        
    # Check if it's an image
    if path.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.webp', '.bmp']:
        return
        
    # Skip already cropped images
    if path.stem.endswith('_cropped'):
        return

    out_suffix = '.jpeg' if path.suffix.lower() == '.png' else path.suffix
    out_path = path.with_name(f"{path.stem}_cropped{out_suffix}")
    if out_path.exists():
        print(f"Skipping {path.name}: {out_path.name} already exists.")
        return

    try:
        with Image.open(path) as img:
            width, height = img.size
            if width == height:
                print(f"Skipping {path.name}: Image is already a square.")
                return
                
            # Calculate the crop box for center crop
            new_size = min(width, height)
            left = (width - new_size) / 2
            top = (height - new_size) / 2
            right = (width + new_size) / 2
            bottom = (height + new_size) / 2
            
            # Crop and save
            img_cropped = img.crop((left, top, right, bottom))
            
            # Convert PNG to JPEG
            if path.suffix.lower() == '.png':
                img_cropped = img_cropped.convert('RGB')
                
            img_cropped.save(out_path)
            print(f"Successfully cropped {path.name} -> {out_path.name}")
    except Exception as e:
        print(f"Error processing {path.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Center crop images to 1:1 square ratio.")
    parser.add_argument("target", help="File or directory path to process")
    args = parser.parse_args()

    target = Path(args.target)
    
    if not target.exists():
        print(f"Error: Target path '{target}' does not exist.")
        sys.exit(1)
        
    if target.is_file():
        crop_to_square(target)
    elif target.is_dir():
        count = 0
        for item in target.iterdir():
            if item.is_file():
                crop_to_square(item)
                count += 1
        if count == 0:
            print(f"No files found in directory '{target}'")
    else:
        print(f"Error: Target path '{target}' is not a valid file or directory.")

if __name__ == "__main__":
    main()
