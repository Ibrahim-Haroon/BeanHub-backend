"""
This file contains various speech to text APIs and a function to record audio from the microphone.
"""
import io
import time
import wave
import logging
from os import path
from os import getenv as env
import whisper
from deepgram import Deepgram
from dotenv import load_dotenv
from pydub import AudioSegment
import speech_recognition as speech
from src.django_beanhub.settings import DEBUG

load_dotenv()

LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=LOGGING_LEVEL, format='%(asctime)s:%(levelname)s:%(message)s')


def google_cloud_speech_api(
        source: str = None
) -> str:
    """
    This function transcribes audio file using Google Cloud Speech API
    @param source: str = file path of an audio file
    @rtype: str
    @return: transcription
    """

    if not source:
        return "None"

    start_time = time.time()
    recognizer = speech.Recognizer()

    recognizer.dynamic_energy_threshold = False
    recognizer.pause_threshold = 0.8
    recognizer.single_utterance = True
    recognizer.interim_results = True

    transcribed_audio = ""

    with speech.AudioFile(source) as audio_source:
        _audio_ = recognizer.record(audio_source)

        try:
            transcribed_audio = recognizer.recognize_google(_audio_)
        except speech.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return "None"
        except speech.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

    logging.debug("google_cloud_speech time: %s", time.time() - start_time)

    return transcribed_audio


def nova_speech_api(
        source: str
) -> str:
    """
    This function transcribes audio file using Deepgram API
    @param source: audio file path
    @rtype: str
    @return: transcription
    """
    key = env("DEEPGRAM_API_KEY")
    if not key:
        key_path = path.join(path.dirname(path.realpath(__file__)),
                             "../..", "other", "deepgram_api_key.txt")
        with open(key_path, encoding='utf-8') as api_key:
            key = api_key.readline().strip()

    start_time = time.time()
    dg = Deepgram(key)

    mime_type = 'audio/wav'

    options = {
        'punctuate': False,
        'model': 'general',
        'tier': 'enhanced'
    }

    with open(source, 'rb') as f:
        _audio_ = {"buffer": f, "mimetype": mime_type}
        response = dg.transcription.sync_prerecorded(_audio_, options)

    logging.debug("nova_speech time: %s", time.time() - start_time)
    return response['results']['channels'][0]['alternatives'][0]['transcript']


def whisper_speech_api(
        source: str
) -> str:
    """
    This function transcribes audio file using Whisper API
    @possible models:
        size,params,english,VRAM,relative speed
        tiny,39 M,tiny.en,1 GB,32x
        base,74 M,base.en,1 GB,16x
        small,244 M,small.en,2 GB,6x
        medium,569 M,medium.en,5 GB,2x
        large,1550 M,N/A,10 GB,1x
    @param source: audio file path
    @rtype: str
    @return: transcription
    """
    start_time = time.time()
    model = whisper.load_model("small.en")

    transcription = model.transcribe(source)

    logging.debug("whisper_speech time: %s", time.time() - start_time)
    return transcription['text']


def whisper_multi_speech_api(
        source: str
) -> str:
    """
    This function transcribes multilingual audio files using Whisper API
    @possible models:
        size,params,multilingual,VRAM,relative speed
        tiny,39 M,tiny,1 GB,32x
        base,74 M,base,1 GB,16x
        small,244 M,small,2 GB,6x
        medium,569 M,medium,5 GB,2x
        large,1550 M,N/A,large,10 GB,1x
    @rtype: str
    @param source: audio file path
    @return: transcription in english
    """
    start_time = time.time()
    model = whisper.load_model("small")

    _audio_ = whisper.load_audio(source)
    _audio_ = whisper.pad_or_trim(_audio_)

    mel = whisper.log_mel_spectrogram(_audio_).to(model.device)

    _, probs = model.detect_language(mel)
    logging.debug(f"Detected language: {max(probs, key=probs.get)}")

    options = whisper.DecodingOptions(
        fp16=False,
        language="en"
    )
    result = whisper.decode(model, mel, options)

    logging.debug(f"whisper_multi_speech time: {time.time() - start_time}")
    return result.text


def record_until_silence(

) -> bytes and str:
    """
    This function records audio from the microphone until silence is detected.
    @rtype: bytes and str
    @return: audio file containing recording of microphone and transcription
    """
    recognizer = speech.Recognizer()
    audio_data = []
    transcribed_audio = None

    recognizer.dynamic_energy_threshold = False  # Disable dynamic energy threshold adjustment
    recognizer.pause_threshold = 0.8  # Set the pause threshold to optimize for short utterances
    recognizer.single_utterance = True  # Treat each call as a single short utterance
    recognizer.interim_results = True  # Get interim results for streaming

    with speech.Microphone() as audio_source:
        print("Recording... Speak until you want to stop.")

        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(audio_source, duration=1)

        while True:
            try:
                audio_chunk = recognizer.listen(audio_source, timeout=1)
                audio_data.append(audio_chunk.frame_data)

                # Try to convert speech to text
                transcribed_audio = recognizer.recognize_google(audio_chunk)
                print(f"Recognized: {transcribed_audio}")

            except speech.WaitTimeoutError:
                print("Timeout. No speech detected.")
                break
            except speech.UnknownValueError:
                print("Could not understand audio.")
                break
            except speech.RequestError as e:
                print(f"Google Speech Recognition request failed: {e}")
                break

    audio_data = b"".join(audio_data)

    return audio_data, transcribed_audio


def return_as_wav(
        audio_data: bytes
) -> bytes:
    """
    This function converts audio data to wav format
    @param audio_data: audio data to convert
    @rtype: bytes
    @return: bytes of wav audio data
    """
    buffer = io.BytesIO()

    # pylint: disable=E1101
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(audio_data)

    wav_data = buffer.getvalue()

    buffer.close()

    return wav_data


def save_as_mp3(
        audio_data: bytes, output_filename: str = "recorded_audio.wav",
        print_completion: bool = False
) -> None:
    """
    This function saves audio data as an mp3 file
    @param print_completion: boolean for whether you want notification of completion
    @param audio_data: audio to save in .mp3 format
    @param output_filename: file name to save audio object under
    @rtype: None
    @return None
    """
    audio_segment = AudioSegment(audio_data, sample_width=2, frame_rate=44100, channels=1)
    audio_segment.export(output_filename, format="wav")
    if print_completion:
        print(f"Audio saved as {output_filename}")


if __name__ == "__main__":  # pragma: no cover
    transcript = whisper_multi_speech_api('/Users/ibrahimharoon/BeanHubCo/BeanHub-backend/urdu_sample.wav')
    print(f"Transcript: {transcript}")
