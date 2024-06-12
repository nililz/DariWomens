const callApiButton = document.getElementById("callApiButton");
const responseText = document.getElementById("responseText");
const textToSpeechButton = document.getElementById("textToSpeechButton");

let audioUrl = null; // Variable to store the audio URL

callApiButton.addEventListener("click", async () => {
    try {
        // 1. Make the API call to your Flask backend 
        const response = await fetch('/process_audio', {
            method: 'POST', 
        });

        // 2. Parse the JSON response
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const responseData = await response.json(); 

        // 3. Update the textarea with the text response
        responseText.value = responseData.text;

        // 4. Store the audio URL for playback later 
        audioUrl = responseData.audio; 

    } catch (error) {
        console.error("Error calling API:", error);
        // Implement proper error handling for the user (e.g., an alert)
    }
});

// Event Listener for "Read Response" Button
textToSpeechButton.addEventListener("click", () => {
    if (audioUrl) {
        const audioPlayer = new Audio(audioUrl);
        audioPlayer.play();
    } else {
        alert("Please call the API first to generate an audio response.");
    }
});