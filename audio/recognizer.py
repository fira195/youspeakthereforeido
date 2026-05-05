import json
from vosk import KaldiRecognizer
from config import SAMPLE_RATE
from core.processor import handle_partial, handle_final


recognizer = None


def init_recognizer(model):
    global recognizer
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    return recognizer


def process_audio(data, ui_update):
    global recognizer

    if recognizer.AcceptWaveform(data):
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip()
        if text:
            handle_final(text, ui_update)
    else:
        partial = json.loads(recognizer.PartialResult()).get("partial", "")
        handle_partial(partial, ui_update)