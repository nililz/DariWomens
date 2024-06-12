const recordButton = document.getElementById('recordButton');
const stopButton = document.getElementById('stopButton');
const audioPlayback = document.getElementById('audioPlayback');
const callApiButton = document.getElementById('callApiButton');
const responseText = document.getElementById('responseText');
const textToSpeechButton = document.getElementById('textToSpeechButton');

let mediaRecorder;
let audioChunks = [];

navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' }); 
            const audioUrl = URL.createObjectURL(audioBlob);
            audioPlayback.src = audioUrl; 
            audioPlayback.controls = true;

            // Enable API call button
            callApiButton.disabled = false;
        };

        recordButton.addEventListener('click', () => {
            audioChunks = []; // Reset audio chunks
            mediaRecorder.start();
            recordButton.disabled = true;
            stopButton.disabled = false;
        });

        stopButton.addEventListener('click', () => {
            mediaRecorder.stop();
            recordButton.disabled = false;
            stopButton.disabled = true;
        });
    })
    .catch(err => {
        console.error('Error accessing microphone:', err);
    });

callApiButton.addEventListener('click', async () => {
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    try {
        const response = await fetch('/process_audio', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const responseData = await response.json();
        responseText.value = responseData.text;
        
        // Enable Text-to-Speech button
        audioPlayback.src = responseData.audio;
        textToSpeechButton.disabled = false; 
        audioPlayback.load(); 

    } catch (error) {
        console.error('Error calling API:', error);
    }
});

textToSpeechButton.addEventListener('click', () => {
    audioPlayback.play(); 
});