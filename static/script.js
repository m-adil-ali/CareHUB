form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const userMessage = input.value;
    appendMessage('user', userMessage);
    input.value = '';

    const response = await fetch('/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `message=${encodeURIComponent(userMessage)}`
    });
    const data = await response.json();
    appendMessage('bot', data.bot_response);

    // Play the audio response
    if (data.audio_url) {
        const audio = new Audio(data.audio_url);
        audio.play();
    }

    if (data.show_popup) {
        modal.style.display = 'flex';
    }
});
