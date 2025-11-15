// Set current date
document.getElementById('currentDate').textContent = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
});

// Success Rate Chart - Bar Chart showing This Month vs Last Month
const successCtx = document.getElementById('successChart');
if (successCtx) {
    const chart = new Chart(successCtx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['This Month', 'Last Month'],
            datasets: [{
                label: 'Success Rate (%)',
                data: [68, 72], // This would ideally come from backend data
                backgroundColor: ['#198754', '#0d6efd'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// View patient details
function viewPatientDetails(patientId) {
    // In a real application, this would fetch patient data via API
    document.getElementById('patientDetailsContent').innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading patient details...</p>
        </div>
    `;

    const modal = new bootstrap.Modal(document.getElementById('patientDetailsModal'));
    modal.show();

    // Simulate API call
    setTimeout(() => {
        document.getElementById('patientDetailsContent').innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Medical Information</h6>
                    <ul class="list-unstyled">
                        <li><strong>Age:</strong> 32</li>
                        <li><strong>BMI:</strong> 24.5</li>
                        <li><strong>AMH Level:</strong> 2.1 ng/mL</li>
                        <li><strong>FSH Level:</strong> 7.2 mIU/mL</li>
                    </ul>
                </div>
                <div class="col-md-6">
                    <h6>Treatment History</h6>
                    <ul class="list-unstyled">
                        <li><strong>Previous Cycles:</strong> 1</li>
                        <li><strong>Current Protocol:</strong> Long Protocol</li>
                        <li><strong>Success Prediction:</strong> 65.2%</li>
                        <li><strong>Embryo Quality Score:</strong> B+ (Good)</li>
                    </ul>
                </div>
            </div>
            <hr>
            <div class="row">
                <div class="col-12">
                    <h6>Wellness Trends</h6>
                    <div class="row">
                        <div class="col-md-3 text-center">
                            <div class="wellness-metric">
                                <div class="metric-value text-primary">4.2/5</div>
                                <div class="metric-label">Avg Mood</div>
                            </div>
                        </div>
                        <div class="col-md-3 text-center">
                            <div class="wellness-metric">
                                <div class="metric-value text-warning">2.8/5</div>
                                <div class="metric-label">Avg Stress</div>
                            </div>
                        </div>
                        <div class="col-md-3 text-center">
                            <div class="wellness-metric">
                                <div class="metric-value text-success">7.5h</div>
                                <div class="metric-label">Avg Sleep</div>
                            </div>
                        </div>
                        <div class="col-md-3 text-center">
                            <div class="wellness-metric">
                                <div class="metric-value text-info">4.1/5</div>
                                <div class="metric-label">Energy</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }, 1000);
}

// Add notes
function openNotesModal(cycleId) {
    if (!cycleId || cycleId === 'null') {
        alert('This patient does not have an active cycle to add a note to.');
        return;
    }

    const notesForm = document.getElementById('notesForm');
    if (notesForm) {
        notesForm.action = `/add_cycle_note/${cycleId}`;
    }

    const modal = new bootstrap.Modal(document.getElementById('notesModal'));
    modal.show();
}

// Generate AI recommendations
function generateAIRecommendations(patientId) {
    // Show loading state
    const button = event.target.closest('button');
    const originalContent = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    button.disabled = true;

    // Simulate AI analysis
    setTimeout(() => {
        alert(`AI Analysis Complete for Patient #${patientId}:\n\n` +
              `• Protocol Optimization: Consider adjusting FSH dose\n` +
              `• Success Prediction: 68.5% based on current parameters\n` +
              `• Wellness Correlation: Stress levels may impact cycle outcome\n` +
              `• Recommendation: Schedule additional monitoring`);

        // Reset button
        button.innerHTML = originalContent;
        button.disabled = false;
    }, 2000);
}

// Filter functionality
document.querySelectorAll('[data-filter]').forEach(button => {
    button.addEventListener('click', function() {
        // Update active button
        document.querySelectorAll('[data-filter]').forEach(btn => btn.classList.remove('active'));
        this.classList.add('active');

        // Filter logic would go here
        const filter = this.dataset.filter;
        console.log('Filtering by:', filter);
    });
});

// Search functionality
document.getElementById('patientSearch')?.addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase();
    const rows = document.querySelectorAll('#patientTable tbody tr');

    rows.forEach(row => {
        const patientName = row.cells[0].textContent.toLowerCase();
        const email = row.cells[0].querySelector('small')?.textContent.toLowerCase() || '';
        const isVisible = patientName.includes(searchTerm) || email.includes(searchTerm);
        row.style.display = isVisible ? '' : 'none';
    });
});

// Quick Actions
function createNewCycle() {
    const modal = new bootstrap.Modal(document.getElementById('newCycleModal'));
    modal.show();
}

function scheduleAppointment() {
    const modal = new bootstrap.Modal(document.getElementById('appointmentModal'));
    modal.show();
}

function generateReport() {
    // Show loading
    const button = event.target.closest('button');
    const originalContent = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    button.disabled = true;

    // Simulate report generation
    setTimeout(() => {
        alert('Report generated successfully! Check your downloads folder.');
        button.innerHTML = originalContent;
        button.disabled = false;
    }, 2000);
}

function sendMessage() {
    const patientId = prompt('Enter patient ID to send message to:');
    if (patientId) {
        const message = prompt('Enter your message:');
        if (message) {
            alert(`Message sent to patient ${patientId}: "${message}"`);
        }
    }
}

function viewFullCalendar() {
    alert('Full calendar view would open here. This would show all appointments, procedures, and important dates.');
}

// Mini calendar initialization
function initMiniCalendar() {
    const today = new Date();
    const calendarEl = document.getElementById('miniCalendar');

    if (calendarEl) {
        calendarEl.innerHTML = `
            <div class="text-center">
                <div class="calendar-header mb-2">
                    <strong>${today.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</strong>
                </div>
                <div class="calendar-grid">
                    <div class="calendar-day current-day">${today.getDate()}</div>
                </div>
            </div>
        `;
    }
}

// Play video function for educational resources
function playVideo(videoType) {
    const videoUrls = {
        'embryo-assessment': 'https://www.youtube.com/results?search_query=embryo+assessment+tutorial+IVF',
        'icsi-procedure': 'https://www.youtube.com/results?search_query=ICSI+procedure+guide+IVF',
        'ovarian-stimulation': 'https://www.youtube.com/results?search_query=controlled+ovarian+stimulation+IVF'
    };

    const url = videoUrls[videoType];
    if (url) {
        window.open(url, '_blank');
    } else {
        alert('Video tutorial coming soon!');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initMiniCalendar();
});
