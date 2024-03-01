from instagrapi import Client as instaClient
import tempfile
from PIL import Image

class instagrammer():
    def __init__(self,un,pw) -> None:
        self.insta = instaClient()
        self.insta.login(username=un,password=pw)
        
    def save_rgba_image_to_tempfile(self,image):
        # Convert RGBA image to RGB
        rgb_image = Image.new("RGB", image.size, (255, 255, 255))
        rgb_image.paste(image, (0, 0), image)

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file_path = temp_file.name

            # Save the RGB image to the temporary file as JPEG
            rgb_image.save(temp_file_path, format="JPEG")

        return temp_file_path
    
    def carousel_post(self,images, caption):
        print(f'Attempting Carosel post with {len(images)} images')
        paths=[]
        for image in images:
            paths.append(self.save_rgba_image_to_tempfile(image))
        try:
            _ = self.insta.album_upload(paths=paths,caption=caption)
        except Exception as e:
            print('failed to post')
            print(e)

    def single_post(self,image, caption):
        print(f'Attempting single image post')
        path=self.save_rgba_image_to_tempfile(image)
        try:
            _ = self.insta.photo_upload(path=path,caption=caption)
        except Exception as e:
            print('Failed to post')
            print(e)