import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
from elevenlabs.client import ElevenLabs
from elevenlabs import play, save, Voice, VoiceSettings
import numpy as np
import time
import os

from utils.config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    RECORDING_SAMPLE_RATE,
    RECORDING_CHANNELS,
    TEMP_AUDIO_FILENAME,
)

# Initialize ElevenLabs client
try:
    el_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
except Exception as e:
    print(f"Error initializing ElevenLabs client: {e}")
    el_client = None

# Initialize recognizer
r = sr.Recognizer()

def speak_text(text: str):
    """Uses ElevenLabs to convert text to speech and play it."""
    if not el_client:
        print("ElevenLabs client not initialized. Cannot speak text.")
        print("Fallback: Printing text instead.")
        print(f"Interviewer: {text}")
        # Add a delay to simulate speech time
        time.sleep(len(text.split()) / 3) # Approximate delay
        return

    try:
        print("Generating audio...")
        # Ensure ELEVENLABS_VOICE_ID exists or use a default known good one if needed
        voice_obj = Voice(
            voice_id=ELEVENLABS_VOICE_ID,
            settings=VoiceSettings(stability=0.6, similarity_boost=0.85, style=0.1, use_speaker_boost=True)
        )

        audio = el_client.generate(
            text=text,
            voice=voice_obj,
            model="eleven_multilingual_v2" # Or other suitable model
        )
        print("Speaking...")
        play(audio)
        print("Finished speaking.")
    except Exception as e:
        print(f"Error during ElevenLabs TTS: {e}")
        print("Fallback: Printing text instead.")
        print(f"Interviewer: {text}")
        time.sleep(len(text.split()) / 3) # Approximate delay


def record_audio(duration: int = 15, filename: str = TEMP_AUDIO_FILENAME) -> str | None:
    """Records audio from the microphone for a specified duration."""
    print(f"\n🎙️ Recording for {duration} seconds... Speak clearly into the microphone.")
    try:
        # Make sure the directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        recording = sd.rec(int(duration * RECORDING_SAMPLE_RATE),
                           samplerate=RECORDING_SAMPLE_RATE,
                           channels=RECORDING_CHANNELS,
                           dtype='float32') # Use float32 which soundfile handles well
        sd.wait()  # Wait until recording is finished

        # Normalize if needed (optional, but can help)
        # recording /= np.max(np.abs(recording)) if np.max(np.abs(recording)) > 0 else 1

        # Save as WAV file using soundfile
        sf.write(filename, recording, RECORDING_SAMPLE_RATE)

        print(f"✅ Recording saved to {filename}")
        return filename
    except Exception as e:
        print(f"Error during audio recording: {e}")
        return None

def transcribe_audio(filename: str = TEMP_AUDIO_FILENAME) -> str | None:
    """Transcribes audio file to text using SpeechRecognition (Google Web Speech API)."""
    print("Transcribing your response...")
    if not os.path.exists(filename):
        print(f"Error: Audio file not found for transcription: {filename}")
        return None

    with sr.AudioFile(filename) as source:
        try:
            audio_data = r.record(source) # Read the entire audio file
            # Use Google Web Speech API for transcription
            text = r.recognize_google(audio_data)
            print(f"🎤 You said: {text}")
            return text
        except sr.UnknownValueError:
            print("❓ Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during transcription: {e}")
            return None
        finally:
            # Clean up the temporary file
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception as e:
                print(f"Warning: Could not delete temp audio file {filename}: {e}")