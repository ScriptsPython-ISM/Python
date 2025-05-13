from PIL import Image

def image_to_start_txt(image_path, output_path="start.txt", size=(50, 50), threshold=128):
    img = Image.open(image_path).convert("L")
    img = img.resize(size)

    with open(output_path, "w") as f:
        for y in range(img.height):
            line = ""
            for x in range(img.width):
                pixel = img.getpixel((x, y))
                line += '1' if pixel < threshold else '0'
            f.write(line + "\n")

    print(f"Saved {output_path} ({size[0]}x{size[1]}) from {image_path}")

image_to_start_txt("me.jpg",size=(500,500), threshold = 100)
