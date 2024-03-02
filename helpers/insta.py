from instagrapi import Client as instaClient
import tempfile
from PIL import Image
from instagrapi.mixins.challenge import ChallengeChoice
import email
import imaplib
import re

class instagrammer():

    def get_code_from_email(self,username):
        print('trying to get the conf code from email')
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(self.challenge_email, self.challenge_password)
        mail.select("inbox")
        result, data = mail.search(None, "(UNSEEN)")
        assert result == "OK", "Error1 during get_code_from_email: %s" % result
        ids = data.pop().split()
        for num in reversed(ids):
            mail.store(num, "+FLAGS", "\\Seen")  # mark as read
            result, data = mail.fetch(num, "(RFC822)")
            assert result == "OK", "Error2 during get_code_from_email: %s" % result
            msg = email.message_from_string(data[0][1].decode())
            payloads = msg.get_payload()
            if not isinstance(payloads, list):
                payloads = [msg]
            code = None
            for payload in payloads:
                body = payload.get_payload(decode=True).decode()
                if "<div" not in body:
                    continue
                match = re.search(">([^>]*?({u})[^<]*?)<".format(u=username), body)
                if not match:
                    continue
                print("Match from email:", match.group(1))
                match = re.search(r">(\d{6})<", body)
                if not match:
                    print('Skip this email, "code" not found')
                    continue
                code = match.group(1)
                if code:
                    print('Got code')
                    return code
        return False

    def challenge_code_handler(self, username, choice):
        print('Challenge happened')
        if choice == ChallengeChoice.SMS:
            print('It looking for text code, I dont have this setup')
            return False
        elif choice == ChallengeChoice.EMAIL:
            return self.get_code_from_email(username)
        return False
    
    def __init__(self,un,pw,email,emailpw) -> None:
        self.insta = instaClient()
        self.username = un
        self.challenge_email = email
        self.challenge_password = emailpw

        self.insta.challenge_code_handler = self.challenge_code_handler
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