const uploadForm = document.querySelector('#upload-form');
const logCardsContainer = document.querySelector('#log-cards-container');

uploadForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const fileInput = document.querySelector('#logfile');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a file to upload.');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/logs/upload/', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Failed to upload file');
        }

        const result = await response.json();
        alert('File uploaded successfully!');
        fetchLogs();
    } catch (error) {
        console.error('Error:', error);
        alert('Error uploading file.');
    }
});

async function fetchLogs() {
    try {
        const response = await fetch('/api/logs/');
        if (!response.ok) {
            throw new Error('Failed to fetch logs');
        }

        const logs = await response.json();
        displayLogs(logs);
    } catch (error) {
        console.error('Error:', error);
    }
}

function displayLogs(logs) {
    logCardsContainer.innerHTML = '';

    logs.forEach((log) => {
        const card = document.createElement('div');
        card.className = 'form_area';
        card.innerHTML = `
            <h4 class="title">${log.name}</h4>
            <p class="sub_title">Description: ${log.description}</p>
            <p class="sub_title">Uploaded At: ${new Date(log.created_at).toLocaleString()}</p>
            <button class="btn" onclick="visualizeLog(${log.id})">Visualize</button>
        `;
        logCardsContainer.appendChild(card);
    });
}

function visualizeLog(logId) {
    alert(`Visualizing log with ID: ${logId}`);
    // Add logic to visualize the log (e.g., redirect to a visualization page)
}

fetchLogs();