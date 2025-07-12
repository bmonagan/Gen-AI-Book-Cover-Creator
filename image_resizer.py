
from PIL import Image
import os

input_folder = 'goodreads data/goodreads_book_covers'
output_folder = 'goodreads data/goodreads_covers_resized'
size = (512, 512)


print(f"Resizing images from {input_folder} to {output_folder}...")
for filename in os.listdir(input_folder):
    if filename.endswith('.jpg') and filename not in os.listdir(output_folder):
        img = Image.open(os.path.join(input_folder, filename))
        img.thumbnail(size)
        img.save(os.path.join(output_folder, filename))
        print(f"Resized and saved: {filename}")
print("Resizing complete.")