from instagrapi import Client as instaClient
import tempfile

class instagrammer():
    def __init__(self,un,pw) -> None:
        self.insta = instaClient(username=un,password=pw)
        
    def save_rgba_image_to_tempfile(self,image):
        # Convert RGBA image to RGB
        rgb_image = image.convert("RGB")

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file_path = temp_file.name

            # Save the RGB image to the temporary file as JPEG
            rgb_image.save(temp_file_path, format="JPEG")

        return temp_file_path
    
    def carousel_post(self,images, caption):
        paths=[]
        for image in images:
            paths.append(self.save_rgba_image_to_tempfile(image))

        try:
            self.insta.album_upload(paths=paths,caption=caption)
        except:
            print('failed to post')
            
    def single_post(self,image, caption):
        path=self.save_rgba_image_to_tempfile(image)
        try:
            self.insta.photo_upload(path=path,caption=caption)
        except:
            print('Failed to post')