const generateScriptButton = document.getElementById('generate-script');
const generateAudioButton = document.getElementById('generate-audio');
const apiKeyInput = document.getElementById('gemini-api-key');
const showApiKeyButton = document.getElementById('show-api-key');
const fileInput = document.getElementById('file-upload');
const urlInput = document.getElementById('url-input');
const podcastScriptTextarea = document.getElementById('podcast-script');
const addUrlButton = document.getElementById('add-url');
const uploadedFilesList = document.getElementById('uploaded-files-list');
const enteredUrlsList = document.getElementById('entered-urls-list');
const languageSelect = document.getElementById('language-select');
const progressIndicator = document.getElementById('progress-indicator');

let uploadedFiles = []; // Array to store uploaded files
let enteredUrls = [];

// Event listener for file uploads
fileInput.addEventListener('change', () => {
    // Add newly selected files to the uploadedFiles array
    for (let i = 0; i < fileInput.files.length; i++) {
        const file = fileInput.files[i];
        uploadedFiles.push(file);
    }

    // Clear the list and re-populate it with all uploaded files
    uploadedFilesList.innerHTML = '';
    uploadedFiles.forEach((file, index) => {
        const listItem = document.createElement('li');
        listItem.textContent = file.name;

        // Add a "Remove" button for each file
        const removeButton = document.createElement('button');
        removeButton.textContent = 'Remove';
        removeButton.style.marginLeft = '10px'; // Add space to the left
        removeButton.addEventListener('click', () => {
            // Remove the file from the array
            uploadedFiles.splice(index, 1);
            // Remove the list item
            uploadedFilesList.removeChild(listItem);
        });

        listItem.appendChild(removeButton);
        uploadedFilesList.appendChild(listItem);
    });
});

// Event listener for adding URLs
addUrlButton.addEventListener('click', () => {
    const url = urlInput.value.trim();
    if (url) {
        enteredUrls.push(url);
        const listItem = document.createElement('li');
        listItem.textContent = url;

        // Add a "Remove" button for each URL
        const removeButton = document.createElement('button');
        removeButton.textContent = 'Remove';
        removeButton.style.marginLeft = '10px'; // Add space to the left
        removeButton.addEventListener('click', () => {
            // Remove the URL from the array
            enteredUrls.splice(enteredUrls.indexOf(url), 1);
            // Remove the list item
            enteredUrlsList.removeChild(listItem);
        });

        listItem.appendChild(removeButton);
        enteredUrlsList.appendChild(listItem);
        urlInput.value = '';
    }
});

// Event listener for generating the script
generateScriptButton.addEventListener('click', () => {
    const apiKey = apiKeyInput.value;

    const formData = new FormData();
    formData.append('gemini-api-key', apiKey);

    // Append all uploaded files to the FormData object
    for (let i = 0; i < uploadedFiles.length; i++) {
        formData.append('file-upload', uploadedFiles[i]);
    }

    // Append entered URLs to the FormData object
    if (enteredUrls.length > 0) {
        formData.append('url-input', JSON.stringify(enteredUrls));
    }

    // Check if at least one file or URL has been provided
    if (uploadedFiles.length === 0 && enteredUrls.length === 0) {
        alert('Please upload files or enter URLs.');
        return;
    }

    // Show a loading popup while the script is being generated
    const popup = document.createElement('div');
    popup.id = 'loading-popup';
    popup.innerHTML = '<p>Generating Script. Please wait...</p>';
    document.body.appendChild(popup);

    // Send a POST request to the server to generate the script
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            // If the response is not ok, throw an error
            return response.json().then(data => {
                throw new Error(data.error || 'Error generating script');
            });
        }
        // Otherwise, return the response as JSON
        return response.json();
    })
    .then(data => {
        // Set the value of the script textarea to the generated script
        podcastScriptTextarea.value = data.script;
    })
    .catch(error => {
        // If there's an error, show an alert
        alert(error.message);
    })
    .finally(() => {
        // Remove the loading popup
        document.body.removeChild(popup);
    });
});

// Event listener for generating audio
generateAudioButton.addEventListener('click', () => {
    const script = podcastScriptTextarea.value;
    const language = languageSelect.value;

    // Show progress indicator
    progressIndicator.textContent = "Generating audio, this may take a while...";

    // Send a POST request to the server to generate the audio
    fetch('/generate-audio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'script': script,
            'language': language
        })
    })
    .then(response => {
        if (!response.ok) {
            // If the response is not ok, throw an error
            throw new Error('Error generating audio');
        }

        // Load and play audio
        const audioPlayback = document.getElementById('audio-playback');
        audioPlayback.src = '/download-audio';
        audioPlayback.load();
        audioPlayback.play();

        // Show download link
        const audioDownload = document.getElementById('audio-download');
        audioDownload.style.display = 'block';

        // Update progress indicator
        progressIndicator.textContent = "Audio generation complete!";
    })
    .catch(error => {
        // If there's an error, show an alert
        alert(error.message);
        progressIndicator.textContent = "";
    });
});

// Event listener for showing/hiding the API key
showApiKeyButton.addEventListener('click', () => {
    if (apiKeyInput.type === "password") {
        apiKeyInput.type = "text";
        showApiKeyButton.textContent = "Hide API Key";
    } else {
        apiKeyInput.type = "password";
        showApiKeyButton.textContent = "Show API Key";
    }
});