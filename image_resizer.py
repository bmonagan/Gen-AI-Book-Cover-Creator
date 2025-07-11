from PIL import Image

def resize_image(input_path, output_path, size=(512, 512)):
    """
    Resize an image to the specified size and save it to the output path.
    
    :param input_path: Path to the input image file.
    :param output_path: Path where the resized image will be saved.
    :param size: Tuple specifying the desired size (width, height).
    """
    try:
        with Image.open(input_path) as img:
            img = img.resize(size, Image.ANTIALIAS)
            img.save(output_path)
            print(f"Image resized and saved to {output_path}")
    except Exception as e:
        print(f"Error resizing image: {e}")

