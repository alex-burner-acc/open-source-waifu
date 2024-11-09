import json
import logging
import os
import tempfile
from base64 import b64decode
from io import BytesIO

import boto3
from moviepy.editor import *
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

logging.basicConfig(level=logging.INFO)

class S3():
    def __init__(self, s3: boto3.client):
        self.temp_files = []
        self.aws_s3: boto3.client = s3
        
    def upload_mp4(self, 
                   file_name: str,
                   file: FileStorage,
                   bucket_name: str,
                   prefix: str = '') -> str:
        """
        Uploads a video file directly to an S3 bucket without saving it as a temporary file,
        ensuring it is stored as an .mp4 file.

        :param file_name: The name of the file to upload
        :param file: FileStorage object from Flask request
        :param bucket_name: Name of the S3 bucket
        :param prefix: Optional prefix path within the bucket
        :return: URL of the uploaded video file
        """
        # Secure the filename and ensure it ends with .mp4
        file_name = secure_filename(file_name)
        if not file_name.endswith('.mp4'):
            file_name += '.mp4'

        object_key = prefix + file_name  # Combine prefix and file name to form the full object key

        self.aws_s3.upload_fileobj(file, Bucket=bucket_name, Key=object_key)

        # Construct the URL for the uploaded video file
        # Note: Consider using the AWS SDK to generate the URL if your bucket name or object key contains characters that require URL encoding
        file_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"

        return file_url
    
    def download_file(self, 
                      bucket_name,
                      font_key, 
                      local_font_path):
        self.aws_s3.download_file(bucket_name, font_key, local_font_path)
        logging.info(f"Downloaded font file from S3: {font_key}")
        return True
        
    def upload_mp3(self, file_name: str, file: FileStorage, bucket_name: str, prefix: str = '') -> bool:
        """
        Uploads an audio file directly to an S3 bucket without saving it as a temporary file,
        ensuring it is stored as an .mp3 file.
        """
        # Secure the filename and ensure it ends with .mp3
        file_name = secure_filename(file_name)
        if not file_name.endswith('.mp3'):
            file_name += '.mp3'  # Append .mp3 if it's not already part of the filename
        
        full_key_path = prefix + file_name if prefix else f"{file_name}"
        logging.info(f"Uploading audio to S3 bucket {bucket_name} at {full_key_path}")

        # Specify the content type for the .mp3 file
        content_type = 'audio/mpeg'

        # Upload the file-like object directly to S3, with content type set
        self.aws_s3.upload_fileobj(Fileobj=file, 
                                   Bucket=bucket_name,
                                   Key=full_key_path,
                                   ExtraArgs={'ContentType': content_type})

        logging.info(f"Successfully uploaded audio as .mp3 to S3 bucket {bucket_name} at {full_key_path}")
        
        return True
        
    def get_dict_from_video_data(self,
                                 prefix,
                                 file_name,
                                 bucket_name):
        # Construct the file name or key in the bucket
        file_key = prefix + file_name
        
        try:
            # Use the S3 client to get the object
            obj = self.aws_s3.get_object(Bucket=bucket_name, Key=file_key)
            # Read the file's content and decode it
            json_content = obj['Body'].read().decode('utf-8')
            # Convert JSON content to a dictionary
            dict_from_s3 = json.loads(json_content)
            logging.info(f"Successfully retrieved transcription for file key: {file_key}")
            return dict_from_s3
        except self.aws_s3.exceptions.NoSuchKey:
            logging.error(f"Transcription file does not exist for file key: {file_key}")
            return None
        except Exception as e:
            logging.error(f"Failed to get transcription for file key: {file_key}. Error: {str(e)}")
            return None
    
    def delete_item(self,
                    bucket_name,
                    object_key):
        try:
            self.aws_s3.delete_object(Bucket=bucket_name, Key=object_key)
            logging.info(f"Deleted item from S3: {object_key}")
            return True
        except Exception as e:
            logging.error(f"Failed to delete item from S3: {object_key}. Error: {str(e)}")
            return False

    def write_dict_to_video_data(self, 
                                 prefix,
                                 dictionary,
                                 file_name,
                                 bucket_name):
        # Construct the file name or key in the bucket, including the "folder" path
        file_key = prefix + file_name
        
        try:
            # Serialize the transcription dictionary to a JSON string
            json_data = json.dumps(dictionary)
            # Convert the JSON string to bytes
            transcription_bytes = json_data.encode('utf-8')
            # Use the S3 client to put the object. This automatically "creates" the folder if it doesn't exist.
            self.aws_s3.put_object(Bucket=bucket_name, Key=file_key, Body=transcription_bytes)
            logging.info(f"Successfully wrote transcription for project_id: {prefix}")
            return True
        except Exception as e:
            logging.error(f"Failed to write transcription for project_id: {prefix}. Error: {str(e)}")
            return False
    
    def write_videofileclip(self,
                            clip: VideoFileClip,
                            video_id,
                            bucket_name,
                            prefix=''):
        # Combine the prefix with the video_id to form the full key path
        full_key_path = f"{prefix}{video_id}" if prefix else video_id
        logging.info(f"Uploading video {video_id} to S3 bucket {bucket_name} under prefix '{prefix}'")

        # Use tempfile to create a temporary video file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            
            logging.info(f"Writing video {video_id} to temporary file {tmp_file.name}")
            # Export the clip to the temporary file
            clip.write_videofile(tmp_file.name, codec="libx264", audio_codec="aac")
            
            # Once the file is saved, upload it to S3 with the full key path including the prefix
            self.aws_s3.upload_file(Filename=tmp_file.name, Bucket=bucket_name, Key=full_key_path)
    
        logging.info(f"Successfully uploaded {video_id} to S3 bucket {bucket_name} under prefix '{prefix}'")
        
        self.temp_files.append(tmp_file.name)
        
        return True
    
    def write_imageclip_as_videofile(self, 
                                     image_clip: ImageClip,
                                     video_id: str,
                                     bucket_name: str,
                                     prefix: str = ''):
        """
        Saves an ImageClip as an .mp4 file and uploads it to an S3 bucket.

        :param image_clip: The ImageClip to be saved and uploaded.
        :param video_id: A unique identifier for the video file.
        :param bucket_name: The name of the S3 bucket to upload the file to.
        :param prefix: An optional prefix to prepend to the video_id for the S3 key path.
        """
        # Ensure the ImageClip has a duration set
        if not hasattr(image_clip, 'duration') or image_clip.duration is None:
            logging.error("ImageClip must have a duration set.")
            return False

        if not video_id.endswith('.mp4'):
            video_id += '.mp4'
        
        # Combine the prefix with the video_id to form the full key path
        full_key_path = prefix + video_id if prefix else video_id
        logging.info(f"Uploading video {video_id} to S3 bucket {bucket_name} under prefix '{prefix}'")

        # Use tempfile to create a temporary video file
        with tempfile.NamedTemporaryFile(suffix='.mp4') as tmp_file:
            # Export the ImageClip to the temporary file as a video, specifying fps
            image_clip.write_videofile(tmp_file.name, fps=24, codec="libx264", audio_codec="aac", temp_audiofile=tmp_file.name + ".mp3", remove_temp=True)

            # Rewind the file to ensure it's read from the beginning
            tmp_file.seek(0)
            
            # Upload the file to S3
            self.aws_s3.upload_file(Filename=tmp_file.name, Bucket=bucket_name, Key=full_key_path)
        
        logging.info(f"Successfully uploaded {video_id} as .mp4 to S3 bucket {bucket_name} under prefix '{prefix}'")
        
        return True
    
    def get_videofileclip(self,
                          video_id,
                          bucket_name,
                          prefix=''):
        full_key_path = f"{prefix}{video_id}" if prefix else video_id
        logging.info(f"Getting Video {full_key_path} from S3 bucket {bucket_name}")

        file_buffer = BytesIO()
        self.aws_s3.download_fileobj(Bucket=bucket_name,
                                        Key=full_key_path,
                                        Fileobj=file_buffer)
        
        # Use tempfile to create a temp file on disk for the video
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            # Write the contents of the BytesIO buffer to the temp file
            file_buffer.seek(0)  # Go to the start of the BytesIO buffer
            tmp_file.write(file_buffer.read())
            
            # Now that the file is saved to disk, we can load it with VideoFileClip
            video_clip = VideoFileClip(tmp_file.name)
            
            logging.info(f"Successfully retrieved video {video_id} from S3 bucket {bucket_name}")
        
        self.temp_files.append(tmp_file.name)
        return video_clip
    
    def get_imageclip(self,
                        image_id,
                        bucket_name,
                        duration,
                        prefix='') -> ImageClip:
        full_key_path = f"{prefix}{image_id}" if prefix else image_id
        logging.info(f"Getting image {full_key_path} from S3 bucket {bucket_name}")

        file_buffer = BytesIO()
        self.aws_s3.download_fileobj(Bucket=bucket_name,
                                        Key=full_key_path,
                                        Fileobj=file_buffer)
        
        # Use tempfile to create a temp file on disk for the video
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            # Write the contents of the BytesIO buffer to the temp file
            file_buffer.seek(0)  # Go to the start of the BytesIO buffer
            tmp_file.write(file_buffer.read())
            
            # Now that the file is saved to disk, we can load it with VideoFileClip
            video_clip = ImageClip(tmp_file.name, duration=duration)
            
            logging.info(f"Successfully retrieved video {image_id} from {full_key_path}")
        
        self.temp_files.append(tmp_file.name)
        return video_clip
    
    def get_audiofileclip(self, 
                          audio_id,
                          bucket_name,
                          prefix=''):
        # Combine the prefix with the audio_id to form the full key path
        full_key_path = f"{prefix}{audio_id}" if prefix else audio_id
        logging.info(f"Getting audio {full_key_path} from S3 bucket {bucket_name}")

        file_buffer = BytesIO()
        self.aws_s3.download_fileobj(Bucket=bucket_name,
                                    Key=full_key_path,
                                    Fileobj=file_buffer)

        # Use tempfile to create a temp file on disk
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            # Write the contents of the BytesIO buffer to the temp file
            file_buffer.seek(0)  # Go to the start of the BytesIO buffer
            tmp_file.write(file_buffer.read())

            # Now that the file is saved to disk, we can load it with AudioFileClip
            audio_clip = AudioFileClip(tmp_file.name)

        # Optionally keep track of temp files for cleanup, assumed self.temp_files is initialized elsewhere
        self.temp_files.append(tmp_file.name)
        
        logging.info(f"Successfully retrieved audio {audio_id} from S3 bucket {bucket_name}")
        return audio_clip

    def get_item_url(self,
                     bucket_name,
                     object_key,
                     expiry_time=3600,
                     prefix=''):
        full_key_path = f"{prefix}{object_key}" if prefix else object_key
        logging.info(f"Getting URL for item {object_key} from {full_key_path}'")

        # Ensure the video exists
        try:
            self.aws_s3.head_object(Bucket=bucket_name, Key=full_key_path)
        except:
            logging.info(f"Video {object_key} not found in {full_key_path}'")
            return None

        # Generate presigned URL
        return self.aws_s3.generate_presigned_url('get_object',
                                                Params={'Bucket': bucket_name,
                                                        'Key': full_key_path},
                                                ExpiresIn=expiry_time)
    
    def get_all_items(self, bucket_name, prefix=''):
        # Initialize a list to hold the item keys
        item_keys = []

        # Initialize the pagination marker
        continuation_token = None

        # Loop to handle pagination
        while True:
            # Prepare the arguments for the list_objects_v2 call
            list_objects_v2_args = {
                'Bucket': bucket_name,
                'Prefix': prefix  # Specify the prefix here
            }

            # If this is not the first page, add the continuation token to the arguments
            if continuation_token:
                list_objects_v2_args['ContinuationToken'] = continuation_token

            # Make the list_objects_v2 call with the prepared arguments
            response = self.aws_s3.list_objects_v2(**list_objects_v2_args)

            # Check if 'Contents' is in the response
            if 'Contents' in response:
                # Extend the item keys list with keys from the current page, excluding the prefix itself
                item_keys.extend(item['Key'] for item in response['Contents'] if item['Key'] != prefix)

            # Check if there are more pages
            if response.get('IsTruncated'):
                continuation_token = response.get('NextContinuationToken')
            else:
                break  # Exit the loop if no more pages

        return item_keys
    
    def create_folder(self, 
                      folder_name,
                      bucket_name,
                      prefix=''):
        # Ensure the full key path ends with a slash to represent a folder
        full_key_path = f"{prefix}{folder_name}/" if prefix else f"{folder_name}/"
        logging.info(f"Creating folder '{full_key_path}' in S3 bucket '{bucket_name}'")

        try:
            # Use the put_object call to create a pseudo-folder in S3
            self.aws_s3.put_object(Bucket=bucket_name, Key=full_key_path)
            logging.info(f"Successfully created folder '{full_key_path}' in S3 bucket '{bucket_name}'")
        except Exception as e:
            logging.error(f"Failed to create folder '{full_key_path}' in S3 bucket '{bucket_name}'. Error: {e}")
            return False

        return True
    
    def save_image_to_s3(self, 
                         json_image_data,
                         file_name,
                         bucket_name,
                         prefix=''):
        response = json_image_data
        full_key_path = prefix + file_name if prefix else file_name

        for index, image_dict in enumerate(response.data):
            image_data = b64decode(image_dict.b64_json)
            
            try:
                self.aws_s3.put_object(Bucket=bucket_name,
                                       Key=full_key_path,
                                       Body=image_data,
                                       ContentType='image/png')
            except Exception as e:
                logging.error(f"Error uploading file to S3: {e}")
                raise
            
        logging.info(f"Saved image to S3: {file_name}")
        return True
    
    def get_list_of_projects(self, key, bucket_name):
        # Initialize a list to hold the names of the projects
        project_folders = []

        # Use the S3 client to list objects with the specified prefix and delimiter
        response = self.aws_s3.list_objects_v2(Bucket=bucket_name, Prefix=key, Delimiter='/')

        # Check if the 'CommonPrefixes' key is in the response, which contains the folder names
        if 'CommonPrefixes' in response:
            for item in response['CommonPrefixes']:
                # Extract the folder name, remove the user_id prefix and the trailing slash
                folder_name = item['Prefix'][len(key):-1]
                project_folders.append(folder_name)

        return project_folders
    
    def get_list_of_objects(self, key, bucket_name):
        # Initialize a list to hold the names of the files
        file_names = []

        # Use the S3 client to list objects with the specified prefix
        response = self.aws_s3.list_objects_v2(Bucket=bucket_name, Prefix=key)

        # Check if the 'Contents' key is in the response, which contains the file names
        if 'Contents' in response:
            for obj in response['Contents']:
                # Check if the key is not just the folder name
                if obj['Key'] != key:
                    # Extract the file name from the key by removing the folder prefix
                    file_name = obj['Key'][len(key):]
                    file_names.append(file_name)

        return file_names

    # ALWAYS CALL THIS AFTER YOU ARE DONE USING THIS CLASS
    def dispose_temp_files(self):
        for file in self.temp_files:
            os.remove(file)