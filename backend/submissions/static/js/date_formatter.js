function formatDate(input) {
    let value = input.value.replace(/\D/g, '');
    
    if (value.length > 2) {
        value = value.substring(0, 2) + '-' + value.substring(2);
    }
    if (value.length > 5) {
        value = value.substring(0, 5) + '-' + value.substring(5);
    }
    
    value = value.substring(0, 10);
    
    input.value = value;
}

function handleBackspace(input, event) {
    if (event.key === 'Backspace') {
        let value = input.value;
        let cursorPosition = input.selectionStart;
        
        if (value[cursorPosition - 1] === '-') {
            event.preventDefault();
            input.value = value.substring(0, cursorPosition - 2) + value.substring(cursorPosition);
            input.setSelectionRange(cursorPosition - 2, cursorPosition - 2);
        }
    }
} 