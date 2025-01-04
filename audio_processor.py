import asyncio
import base64
import json
import os
import wave
from websockets.asyncio.client import connect
import websockets
import pyaudio
from dotenv import load_dotenv
import logging

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Configure logging
logging.basicConfig(filename='audio_generation.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class AudioGenerator:
    def __init__(self, voice):
        self.voice = voice
        self.audio_in_queue = asyncio.Queue()
        self.ws = None
        self.ws_semaphore = asyncio.Semaphore(1)

        # Audio configuration
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.SAMPLE_RATE = 24000
        self.CHUNK_SIZE = 512

        # WebSocket configuration
        self.ws_options = {
            'ping_interval': 20,
            'ping_timeout': 10,
            'close_timeout': 5
        }

        # API configuration
        self.host = 'generativelanguage.googleapis.com'
        self.model = "gemini-2.0-flash-exp"  # Updated model name
        self.uri = f"wss://{self.host}/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={GOOGLE_API_KEY}"

        self.complete_audio = bytearray()

    async def cleanup(self):
        if self.ws:
            await self.ws.close()
        self.complete_audio.clear()
        while not self.audio_in_queue.empty():
            self.audio_in_queue.get_nowait()

    async def process_batch(self, dialogues, output_files):
        """Processes a batch of dialogues and saves the generated audio to output files."""
        try:
            async with connect(self.uri, **self.ws_options) as ws:
                self.ws = ws
                await self.startup(ws, self.voice)
                for dialogue, output_file in zip(dialogues, output_files):
                    await self.send_text(ws, dialogue)
                    await self.receive_audio(output_file)
        except Exception as e:
            logging.exception(f"Error in process_batch: {e}")
            raise

    async def startup(self, ws, voice):
        """Sends the initial setup message to the websocket."""
        try:
            async with self.ws_semaphore:
                setup_msg = {
                    "setup": {
                        "model": f"models/{self.model}",
                        "generation_config": {
                            "speech_config": {
                                "voice_config": {
                                    "prebuilt_voice_config": {
                                        "voice_name": voice
                                    }
                                }
                            }
                        }
                    }
                }
                await ws.send(json.dumps(setup_msg))
                response = await ws.recv()  # You might want to handle this response
        except Exception as e:
            logging.exception(f"Error in startup: {e}")
            raise

    async def send_text(self, ws, text):
        """Sends the text to the websocket for audio generation."""
        try:
            async with self.ws_semaphore:
                msg = {
                    "client_content": {
                        "turn_complete": True,
                        "turns": [
                            {"role": "user", "parts": [{"text": text}]}
                        ]
                    }
                }
                await ws.send(json.dumps(msg))
        except Exception as e:
            logging.exception(f"Error in send_text: {e}")
            raise

    async def receive_audio(self, output_file):
        """Receives the audio data from the websocket and saves it to a file."""
        try:
            async with self.ws_semaphore:
                self.complete_audio.clear()
                await asyncio.sleep(0.1)  # Brief pause to allow for initial response

                try:
                    async for raw_response in self.ws:
                        response = json.loads(raw_response)

                        try:
                            parts = response["serverContent"]["modelTurn"]["parts"]
                            for part in parts:
                                if "inlineData" in part:
                                    b64data = part["inlineData"]["data"]
                                    pcm_data = base64.b64decode(b64data)
                                    self.complete_audio.extend(pcm_data)
                                    self.audio_in_queue.put_nowait(pcm_data)
                        except KeyError:
                            pass  # Handle missing keys appropriately

                        try:
                            if response["serverContent"].get("turnComplete", False):
                                self.save_wav_file(output_file)
                                while not self.audio_in_queue.empty():
                                    self.audio_in_queue.get_nowait()
                                break
                        except KeyError:
                            pass  # Handle missing keys appropriately

                except websockets.exceptions.ConnectionClosedError as e:
                    logging.exception(f"Connection closed: {e}")
                    raise
        except Exception as e:
            logging.exception(f"Error in receive_audio: {e}")
            raise

    def save_wav_file(self, filename):
        """Saves the accumulated audio data to a WAV file."""
        try:
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(self.CHANNELS)
                wav_file.setsampwidth(2)  # 2 bytes per sample for 16-bit audio
                wav_file.setframerate(self.SAMPLE_RATE)
                stereo_data = bytearray()
                for i in range(0, len(self.complete_audio), 2):
                    sample = self.complete_audio[i:i+2]
                    # Convert mono to stereo by duplicating the sample
                    stereo_data.extend(sample)
                    stereo_data.extend(sample)
                wav_file.writeframes(stereo_data)
        except Exception as e:
            logging.exception(f"Error in save_wav_file: {e}")
            raise

    async def run(self, dialogues, output_files, max_retries=3):
        """Runs the audio generation process with retries in case of connection errors."""
        last_exception = None
        for attempt in range(max_retries):
            try:
                async with connect(self.uri, **self.ws_options) as ws:
                    self.ws = ws
                    await self.startup(self.ws, self.voice)
                    for dialogue, output_file in zip(dialogues, output_files):
                        await self.send_text(self.ws, dialogue)
                        await self.receive_audio(output_file)
                return  # Success, exit the loop
            except websockets.exceptions.ConnectionClosedError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logging.warning(f"Connection lost. Retrying in 5 seconds... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(5)
                else:
                    logging.error("Max retries reached. Unable to reconnect.")
                    raise last_exception