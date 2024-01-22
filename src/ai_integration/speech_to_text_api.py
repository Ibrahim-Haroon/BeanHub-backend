import time
import logging
import whisper
from os import path
from deepgram import Deepgram
from pydub import AudioSegment
import speech_recognition as speech

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s')


def google_cloud_speech_api(
        source: str = None
) -> str:
    """

    @rtype: str
    @param source: str = file path of an audio file
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
        audio = recognizer.record(audio_source)

        try:
            transcribed_audio = recognizer.recognize_google(audio)
        except speech.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return "None"
        except speech.RequestError as e:
            print(
                "Could not request results from Google Speech Recognition service; {0}".format(e))

    logging.info(f"google_cloud_speech time: {time.time() - start_time}")

    return transcribed_audio


def nova_speech_api(
        source: str
) -> str:
    """

    @rtype: str
    @param source: audio file path
    @return: transcription
    """
    key_path = path.join(
        path.dirname(
            path.realpath(__file__)),
        "../..",
        "other",
        "deepgram_api_key.txt")
    with open(key_path) as api_key:
        key = api_key.readline().strip()

    start_time = time.time()
    dg = Deepgram(key)

    MIMETYPE = 'audio/wav'

    options = {
        'punctuate': False,
        'model': 'general',
        'tier': 'enhanced'
    }

    with open(source, 'rb') as f:
        audio = {"buffer": f, "mimetype": MIMETYPE}
        response = dg.transcription.sync_prerecorded(audio, options)

    logging.info(f"nova_speech time: {time.time() - start_time}")
    return response['results']['channels'][0]['alternatives'][0]['transcript']


def whisper_speech_api(
        source: str
) -> str:
    """
    @possible models:
        size,params,english,VRAM,relative speed
        tiny,39 M,tiny.en,1 GB,32x
        base,74 M,base.en,1 GB,16x
        small,244 M,small.en,2 GB,6x
        medium,569 M,medium.en,5 GB,2x
        large,1550 M,N/A,10 GB,1x
    @rtype: str
    @param source: audio file path
    @return: transcription
    """
    start_time = time.time()
    model = whisper.load_model("small.en")

    transcription = model.transcribe(source)

    logging.info(f"whisper_speech time: {time.time() - start_time}")
    return transcription['text']


def whisper_multi_speech_api(
        source: str
) -> str:
    """

    @possible models:
        size,params,,multilingual,VRAM,relative speed
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

    audio = whisper.load_audio(source)
    audio = whisper.pad_or_trim(audio)

    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    _, probs = model.detect_language(mel)
    logging.info(f"Detected language: {max(probs, key=probs.get)}")

    options = whisper.DecodingOptions()
    result = whisper.decode(model, mel, options)

    logging.info(f"whisper_multi_speech time: {time.time() - start_time}")
    return result.text


def record_until_silence(

) -> bytes and str:
    """

    @rtype: bytes and str
    @return: audio file containing recording of microphone and transcription
    """
    recognizer = speech.Recognizer()
    audio_data = []
    transcribed_audio = None

    # Disable dynamic energy threshold adjustment
    recognizer.dynamic_energy_threshold = False
    # Set the pause threshold to optimize for short utterances
    recognizer.pause_threshold = 0.8
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
            except speech.RequestError as e:
                print(f"Google Speech Recognition request failed: {e}")

    audio_data = b"".join(audio_data)

    return audio_data, transcribed_audio


def save_as_mp3(
        audio_data: bytes, output_filename: str = "recorded_audio.wav",
        print_completion: bool = False
) -> None:
    """

    @param print_completion: boolean for whether you want notification of completion
    @param audio_data: audio to save in .mp3 format
    @param output_filename: file name to save audio object under
    @return None
    """
    audio_segment = AudioSegment(
        audio_data,
        sample_width=2,
        frame_rate=44100,
        channels=1)
    audio_segment.export(output_filename, format="wav")
    if print_completion:
        print(f"Audio saved as {output_filename}")


if __name__ == "__main__":
    _ = nova_speech_api(
        '/Users/ibrahimharoon/Downloads/customer_order_1705338629783.wav')
    print(_)
