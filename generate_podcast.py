import subprocess
import os
import logging
import sys

# Custom formatter that only shows the message
class CustomFormatter(logging.Formatter):
    def format(self, record):
        return record.getMessage()

# Configure logging with custom formatter
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
# Remove default handlers
logging.getLogger().handlers = []

def update_language_in_template(language):
    """Updates the language placeholder in the audio template."""
    template_file = 'system_instructions_audio_template.txt'
    output_file = 'system_instructions_audio.txt'
    
    with open(template_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    updated_content = content.replace('[LANGUAGE]', language)
    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(updated_content)

def generate_podcast(language, script):  # Add script argument
    """Generates the podcast, including script and audio."""
    try:
        # Update language in template file
        update_language_in_template(language)
        logger.info(f"Updated template for language: {language}")

        # Save the script to podcast_script.txt
        with open('podcast_script.txt', 'w', encoding='utf-8') as f:
            f.write(script)

        # Step 2: Generate audio with updated language file
        logger.info("Converting script to audio...")
        subprocess.run([sys.executable, "generate_audio.py", "--language", language], check=True)  # Pass language to generate_audio.py

        if os.path.exists("final_podcast.wav"):
            logger.info("Podcast generation complete! Output: final_podcast.wav")
        else:
            logger.error("Failed to generate final podcast audio")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Process failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    # This block will not be executed when imported as a module
    pass