import speech_recognition as speech
from pydub import AudioSegment


def get_transcription(source: str = None) -> str:
    """

    @rtype: str
    @param source: str = file path of an audio file
    @return: transcription
    """

    if not source:
        return "None"

    recognizer = speech.Recognizer()

    transcribed_audio = None

    with speech.AudioFile(source) as audio_source:
        audio = recognizer.record(audio_source)

        try:
            transcribed_audio = recognizer.recognize_google(audio)
        except speech.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return "None"
        except speech.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))

    return transcribed_audio



def record_until_silence() -> bytes and str:
    """

    @rtype: bytes and str
    @return: audio file containing recording of microphone and transcription
    """
    recognizer = speech.Recognizer()
    audio_data = []
    transcribed_audio = None

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


def save_as_mp3(audio_data: bytes, output_filename: str = "recorded_audio.mp3", print_completion: bool = False) -> None:
    """

    @param print_completion: boolean for whether you want notification of completion
    @param audio_data: audio to save in .mp3 format
    @param output_filename: file name to save audio object under
    @return None
    """
    audio_segment = AudioSegment(audio_data, sample_width=2, frame_rate=44100, channels=1)
    audio_segment.export(output_filename, format="mp3")
    if print_completion:
        print(f"Audio saved as {output_filename}")


if __name__ == "__main__":
    recorded_audio, transcription = record_until_silence()
    if recorded_audio is not None:
        save_as_mp3(recorded_audio)