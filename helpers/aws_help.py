import boto3
import pandas as pd
from io import StringIO, BytesIO


class s3_mover:
    def __init__(self):
        self.s3 = boto3.client("s3")
        self.data_base = "CFB_shirt/data/"
        self.image_base = "CFB_shirt/images/"

    def pd_to_s3(self, file, s3_name):
        key = self.data_base + s3_name + ".csv"
        csv_buffer = StringIO()
        file.to_csv(csv_buffer)
        csv_buffer.seek(0)
        response = self.s3.put_object(
            Bucket="lm-myfreebucket", Body=csv_buffer.getvalue(), Key=key
        )

    def image_to_s3(self, pil_image, s3_name):
        key = self.image_base + s3_name + ".png"
        png_buffer = BytesIO()
        pil_image.save(png_buffer, format="png")
        # pil_image.save(png_buffer, format=pil_image.format)
        png_buffer.seek(0)
        response = self.s3.put_object(
            Bucket="lm-myfreebucket", Body=png_buffer, Key=key
        )

    def s3_to_pd(self, s3_name):
        key = self.data_base + s3_name + ".csv"
        response = self.s3.get_object(Bucket="lm-myfreebucket", Key=key)
        return pd.read_csv(response.get("Body"), index_col=0)
