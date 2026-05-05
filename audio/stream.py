import sounddevice as sd
from config import SAMPLE_RATE, BLOCKSIZE
from audio.recognizer import process_audio

is_listening = False


def start_stream(device, ui_update):
    def callback(indata, frames, time, status):
        global is_listening

        if not is_listening:
            return

        process_audio(bytes(indata), ui_update)

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        callback=callback,
        device=device,
        blocksize=BLOCKSIZE,
    )

    stream.start()
    return stream