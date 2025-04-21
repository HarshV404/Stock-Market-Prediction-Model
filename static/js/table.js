function filterTable() {
    const searchValue = document.getElementById('date-search').value.trim();
    const tableWrapper = document.querySelector('.table-wrapper');
    const rows = tableWrapper.querySelectorAll('tr');
    let found = false;

    // Remove any existing no-results message
    const existingMessage = document.getElementById('no-results');
    if (existingMessage) existingMessage.remove();

    rows.forEach((row, index) => {
        if (index === 0) return; // Skip header row

        // Find date cell - more robust selector
        const dateCell = row.querySelector('td[data-date]') || row.cells[0]; // Try data-date attribute first
        if (dateCell) {
            const cellText = dateCell.textContent.trim();
            // Better date comparison (adjust format as needed)
            if (cellText === searchValue || cellText.includes(searchValue)) {
                row.style.display = '';
                found = true;
            } else {
                row.style.display = 'none';
            }
        }
    });

    if (!found) {
        const message = document.createElement('div');
        message.id = 'no-results';
        message.textContent = 'No results found for the specified date.';
        message.style.textAlign = 'center';
        message.style.padding = '20px';
        // Insert after the table
        tableWrapper.parentNode.insertBefore(message, tableWrapper.nextSibling);
    }
}