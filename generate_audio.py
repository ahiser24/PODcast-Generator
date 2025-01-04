import tempfile
import asyncio
import os
from audio_processor import AudioGenerator
from dotenv import load_dotenv
from pydub import AudioSegment
import logging

# Configure logging
logging.basicConfig(filename='audio_generation.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
#Voice choices: Puck, Charon, Kore, Fenrir, Aoede
VOICE_A = os.getenv('VOICE_A', 'Puck')  # Use Puck for Voice A
VOICE_B = os.getenv('VOICE_B', 'Aoede')  # Use Aoede for Voice B

def parse_conversation(script):  # Changed to accept script directly
    """Parses the conversation script into lines for each speaker."""
    lines = script.strip().split('\n')
    speaker_a_lines = []
    speaker_b_lines = []

    for line in lines:
        if line.strip():
            if line.startswith("Speaker A:"):
                speaker_a_lines.append(line.replace("Speaker A:", "").strip())
            elif line.startswith("Speaker B:"):
                speaker_b_lines.append(line.replace("Speaker B:", "").strip())

    return speaker_a_lines, speaker_b_lines

async def setup_environment():
    """Sets up the environment and returns the script directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return script_dir

def read_and_parse_inputs(script):  # Changed to accept script as input
    """Reads the system instructions and parses the conversation from the script."""
    system_instructions = ""
    try:
        with open('system_instructions_audio.txt', 'r', encoding='utf-8') as file:
            system_instructions = file.read()
    except FileNotFoundError:
        print("system_instructions_audio.txt not found. Skipping.")
    
    speaker_a_lines, speaker_b_lines = parse_conversation(script)
    return system_instructions, speaker_a_lines, speaker_b_lines

def prepare_speaker_dialogues(system_instructions, full_script, speaker_lines, voice, temp_dir):
    """Prepares the dialogues and output file paths for a speaker."""
    dialogues = [system_instructions + "\n\n" + full_script]
    output_files = [os.path.join(temp_dir, f"speaker_{voice}_initial.wav")]

    for i, line in enumerate(speaker_lines):
        dialogues.append(line)
        output_files.append(os.path.join(temp_dir, f"speaker_{voice}_{i}.wav"))

    return dialogues, output_files

async def process_speaker(voice, dialogues, output_files):
    """Processes the dialogues for a speaker using the AudioGenerator."""
    try:
        # Create a single generator for all dialogues
        generator = AudioGenerator(voice)

        # Process the entire batch of dialogues at once
        await generator.process_batch(dialogues, output_files)

        # Ensure the websocket connection is closed
        if generator.ws:
            await generator.ws.close()
    except Exception as e:
        logging.exception(f"Error in process_speaker: {e}")
        raise

def interleave_output_files(speaker_a_files, speaker_b_files):
    """Interleaves the audio files from both speakers to maintain conversation order."""
    all_output_files = []
    min_length = min(len(speaker_a_files), len(speaker_b_files))

    # Interleave files from both speakers
    for i in range(min_length):
        all_output_files.extend([speaker_a_files[i], speaker_b_files[i]])

    # Add any remaining files from either speaker
    all_output_files.extend(speaker_a_files[min_length:])
    all_output_files.extend(speaker_b_files[min_length:])

    return all_output_files

def combine_audio_files(file_list, output_file, silence_duration_ms=50):
    """Combines the audio files into a single output file."""
    combined = AudioSegment.empty()
    silence = AudioSegment.silent(duration=silence_duration_ms)

    for file in file_list:
        audio = AudioSegment.from_wav(file)
        if audio.channels == 1:
            audio = audio.set_channels(2)
        combined += audio + silence

    combined.export(output_file, format="wav")

async def generate_podcast(language):  # Changed function signature
    """Generates the podcast audio from the provided script."""
    try:
        logging.info('Setting up environment')
        script_dir = await setup_environment()

        with tempfile.TemporaryDirectory(dir=script_dir) as temp_dir:
            logging.info(f'Created temporary directory: {temp_dir}')
            
            # Get the script from the frontend
            script = ""
            try:
                with open('podcast_script.txt', 'r', encoding='utf-8') as f:
                    script = f.read()
            except FileNotFoundError:
                print("podcast_script.txt not found, using an empty script.")

            logging.info('Reading and parsing inputs')
            system_instructions, speaker_a_lines, speaker_b_lines = read_and_parse_inputs(script)

            # Prepare dialogues for both speakers, using the full script for the initial prompt
            dialogues_a, output_files_a = prepare_speaker_dialogues(system_instructions, script, speaker_a_lines, VOICE_A, temp_dir)  # Use script here
            dialogues_b, output_files_b = prepare_speaker_dialogues(system_instructions, script, speaker_b_lines, VOICE_B, temp_dir)  # Use script here

            logging.info('Processing Speaker A...')
            await process_speaker(VOICE_A, dialogues_a, output_files_a)

            logging.info('Processing Speaker B...')
            await process_speaker(VOICE_B, dialogues_b, output_files_b)

            logging.info('Interleaving and combining audio')
            all_output_files = interleave_output_files(output_files_a[1:], output_files_b[1:])
            final_output = "final_podcast.wav"
            combine_audio_files(all_output_files, final_output, silence_duration_ms=50)
            logging.info(f'Final podcast audio created: {final_output}')

        logging.info('Temporary files cleaned up')

    except Exception as e:
        logging.exception(f'An error occurred during audio generation: {e}')
        raise

if __name__ == "__main__":
    # Get the language argument from the command line
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', default='en-US', help='Language for audio narration')
    args = parser.parse_args()

    asyncio.run(generate_podcast(args.language))  # Pass only the language argument