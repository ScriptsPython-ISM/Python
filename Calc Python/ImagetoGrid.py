from PIL import Image
import math

def image_to_start_txt(image_path, output_path="start.txt", size=(50, 50)):
    img = Image.open(image_path).convert("RGB")
    img = img.resize(size)
    key = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/|()1{}[]?-_+~<>i!lI;:,\"^`'."
    multiplication = len(key)/255

    with open(output_path, "w") as f:
        for y in range(img.height):
            line = ""
            for x in range(img.width):
                R,G,B = img.getpixel((x, y))
                index = round(R*multiplication)-1
                line += list(key)[index]
            f.write(line + "\n")

    print(f"Saved {output_path} ({size[0]}x{size[1]}) from {image_path}")

image_to_start_txt("lorenzo.jpg",size=(226,403))
