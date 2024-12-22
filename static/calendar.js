document.addEventListener('DOMContentLoaded', () => {
    const calendar = document.getElementById('calendar');
    const crossOffButton = document.getElementById('cross-off');
    const dates = Array.from({ length: 31 }, (_, i) => `2024-11-${i + 1}`);
    const selectedDates = new Set();

    dates.forEach(date => {
        const dateElement = document.createElement('div');
        dateElement.classList.add('date');
        dateElement.textContent = date;

        dateElement.addEventListener('click', () => {
            const day = parseInt(date.split('-')[2], 10);

            if (selectedDates.has(date)) {
                selectedDates.delete(date);
                dateElement.classList.remove('selected');
            } else {
                selectedDates.add(date);
                dateElement.classList.add('selected');
            }

            const totalCost = Array.from(selectedDates)
                .map(d => parseInt(d.split('-')[2], 10))
                .reduce((sum, d) => sum + d, 0);

            crossOffButton.textContent = `Cross Off! ($${totalCost})`;
            crossOffButton.style.display = selectedDates.size > 0 ? 'block' : 'none';
        });

        calendar.appendChild(dateElement);
    });

    crossOffButton.addEventListener('click', () => {
        window.location.href = `/checkout?dates=${Array.from(selectedDates).join(',')}`;
    });
});
