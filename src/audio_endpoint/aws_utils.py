import tempfile
import time
import os
import logging
import boto3
from src.ai_integration.speech_to_text_api import nova_speech_api
import uuid


def get_transcription(
        s3: boto3.client, bucket_name: str, file_path: str
) -> str:
    """
    @rtype: str
    @param s3: s3 client
    @param bucket_name: name of the s3 bucket
    @param file_path: path to save the audio file from s3 bucket
    @return: audio file from s3 bucket
    """
    # pylint: disable=R1732
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    try:
        start_time = time.time()
        s3.download_file(bucket_name, file_path, temp_file.name)
        logging.debug("download_file time: %s", time.time() - start_time)

        temp_file.close()

        transcription = nova_speech_api(temp_file.name)
    finally:
        os.remove(temp_file.name)

    return transcription


def upload_file(
        s3, bucket_name, unique_id: uuid.UUID, response_audio: bytes
) -> None:
    """
    @rtype: None
    @param s3: s3 client
    @param bucket_name: name of the s3 bucket
    @param unique_id: identifier to upload file under
    @param response_audio: audio file to upload
    @return: Nothing
    """
    res_audio_path = f"/tmp/res_audio_{unique_id}.wav"
    audio_write_time = time.time()
    with open(res_audio_path, 'wb') as f:
        f.write(response_audio)
    logging.debug("audio_write time: %s", time.time() - audio_write_time)

    upload_time = time.time()
    s3.upload_file(res_audio_path, bucket_name, f"result_{unique_id}.wav")
    logging.debug("upload_file time: %s", time.time() - upload_time)
