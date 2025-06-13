function formatDate(input) {
    // Remove any non-digit characters
    let value = input.value.replace(/\D/g, '');
    
    // Add dashes automatically
    if (value.length > 2) {
        value = value.substring(0, 2) + '-' + value.substring(2);
    }
    if (value.length > 5) {
        value = value.substring(0, 5) + '-' + value.substring(5);
    }
    
    // Limit to 10 characters (dd-mm-yyyy)
    value = value.substring(0, 10);
    
    input.value = value;
}

function handleBackspace(input, event) {
    if (event.key === 'Backspace') {
        let value = input.value;
        let cursorPosition = input.selectionStart;
        
        // If cursor is right after a dash, delete the dash and the previous digit
        if (value[cursorPosition - 1] === '-') {
            event.preventDefault();
            input.value = value.substring(0, cursorPosition - 2) + value.substring(cursorPosition);
            input.setSelectionRange(cursorPosition - 2, cursorPosition - 2);
        }
    }
} 