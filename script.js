// Ask permission for notifications
if ("Notification" in window && Notification.permission !== "granted") {
    Notification.requestPermission();
}

// Show notifications
function showNotification(message) {
    if (Notification.permission === "granted") {
        new Notification("Study Reminder", { body: message });
    }
}

// Example usage: showNotification("You did not study Math for 3 days");
