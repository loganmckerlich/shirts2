from instagrapi import Client as instaClient
import tempfile
from PIL import Image
from instagrapi.mixins.challenge import ChallengeChoice
import email
import imaplib
import re
import logging

logger = logging.getLogger()

class instagrammer():

    def get_code_from_email(self,username):
        logger.info('trying to get the conf code from email')
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
                # logger.info("Match from email:", match.group(1))
                match = re.search(r">(\d{6})<", body)
                if not match:
                    # logger.info('Skip this email, "code" not found')
                    continue
                code = match.group(1)
                if code:
                    logger.info('Got code')
                    return code
        return False

    def challenge_code_handler(self, username, choice):
        logger.info('Challenge happened')
        if choice == ChallengeChoice.SMS:
            logger.warning('It looking for text code, I dont have this setup')
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

        
    def save_image_to_tempfile(self,image):

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file_path = temp_file.name

            # Save the image to the temporary file as JPEG
            image.save(temp_file_path, format="JPEG")

        return temp_file_path
    
    def carousel_post(self,images, caption):
        logger.info(f'Attempting Carosel post with {len(images)} images')
        paths=[]
        for image in images:
            paths.append(self.save_image_to_tempfile(image))
        try:
            _ = self.insta.album_upload(paths=paths,caption=caption)
        except Exception as e:
            logger.warning('failed to post', exc_info=True)

    def single_post(self,image, caption):
        logger.info(f'Attempting single image post')
        path=self.save_image_to_tempfile(image)
        try:
            _ = self.insta.photo_upload(path=path,caption=caption)
        except Exception as e:
            logger.warning('Failed to post',exc_info=True)
