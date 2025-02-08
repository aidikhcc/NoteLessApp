document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add question form handling
    const addQuestionForm = document.getElementById('addQuestionForm');
    if (addQuestionForm) {
        addQuestionForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const questionInput = document.getElementById('questionText');
            const sessionId = this.dataset.sessionId;
            const submitButton = this.querySelector('button[type="submit"]');
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            
            if (!questionInput.value.trim()) {
                alert('Please enter a question');
                return;
            }
            
            try {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Adding...';
                
                const response = await fetch(`/session/${sessionId}/questions`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ text: questionInput.value.trim() })
                });

                const data = await response.json();

                if (response.ok) {
                    location.reload();
                } else {
                    throw new Error(data.error || 'Failed to add question');
                }
            } catch (error) {
                console.error('Error:', error);
                alert(error.message || 'Failed to add question. Please try again.');
            } finally {
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fas fa-plus me-2"></i>Add Question';
            }
        });
    }

    // Handle response form submissions
    document.querySelectorAll('.response-form').forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const questionId = this.dataset.questionId;
            const submitButton = this.querySelector('button[type="submit"]');
            const textarea = this.querySelector('.response-input');
            
            // Disable form while submitting
            submitButton.disabled = true;
            textarea.disabled = true;
            
            try {
                const response = await fetch(`/question/${questionId}/respond`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                    },
                    body: JSON.stringify({
                        text: textarea.value
                    })
                });

                if (response.ok) {
                    // Show success message
                    const originalText = submitButton.innerHTML;
                    submitButton.innerHTML = '<i class="fas fa-check"></i> Submitted!';
                    submitButton.classList.add('bg-green-500');
                    
                    // Clear and disable the form
                    textarea.value = '';
                    
                    setTimeout(() => {
                        // Reset button
                        submitButton.innerHTML = originalText;
                        submitButton.classList.remove('bg-green-500');
                        // Re-enable form
                        submitButton.disabled = false;
                        textarea.disabled = false;
                    }, 2000);
                } else {
                    throw new Error('Failed to submit response');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to submit response. Please try again.');
                // Re-enable form
                submitButton.disabled = false;
                textarea.disabled = false;
            }
        });
    });

    // Delete question handling
    document.querySelectorAll('.delete-question').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            if (!confirm('Are you sure you want to delete this question?')) return;

            const questionId = this.dataset.questionId;
            try {
                const response = await fetch(`/question/${questionId}/delete`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                    }
                });

                if (response.ok) {
                    const questionElement = this.closest('.question-item');
                    questionElement.style.animation = 'fadeOut 0.3s ease-out forwards';
                    setTimeout(() => questionElement.remove(), 300);
                } else {
                    throw new Error('Failed to delete question');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to delete question. Please try again.');
            }
        });
    });

    // Delete session handling
    document.querySelectorAll('.delete-session').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            if (!confirm('Are you sure you want to delete this session and all its questions?')) return;

            const sessionId = this.dataset.sessionId;
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            
            try {
                const response = await fetch(`/session/${sessionId}/delete`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    credentials: 'same-origin'
                });

                if (response.ok) {
                    const sessionCard = this.closest('.session-card');
                    if (sessionCard) {
                        // If on dashboard page
                        sessionCard.style.animation = 'fadeOut 0.3s ease-out forwards';
                        setTimeout(() => {
                            sessionCard.remove();
                            if (document.querySelectorAll('.session-card').length === 0) {
                                location.reload();
                            }
                        }, 300);
                    } else {
                        // If on session detail page
                        window.location.href = '/dashboard';
                    }
                } else {
                    const data = await response.json();
                    throw new Error(data.error || 'Failed to delete session');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to delete session. Please try again.');
            }
        });
    });

    // Copy access code to clipboard
    document.querySelectorAll('button[onclick*="copyAccessCode"]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent default onclick behavior
            const accessCode = this.getAttribute('onclick').match(/'([^']+)'/)[1];
            copyAccessCode(accessCode);
        });
    });

    // Add this function to handle copying the access code
    function copyAccessCode(accessCode) {
        // Get the full URL for joining the session
        const joinUrl = `${window.location.origin}/join/${accessCode}`;
        
        navigator.clipboard.writeText(joinUrl).then(() => {
            // Show a temporary success message
            const buttons = document.querySelectorAll('button[onclick*="copyAccessCode"]');
            const button = buttons[0]; // Get the first (and should be only) button
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> Link Copied!';
            button.classList.add('bg-green-500');
            
            setTimeout(() => {
                button.innerHTML = originalText;
                button.classList.remove('bg-green-500');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            alert('Failed to copy link. Please try again.');
        });
    }

    // Handle copy link button clicks
    document.querySelectorAll('.copy-link-btn').forEach(button => {
        button.addEventListener('click', function() {
            const accessCode = this.dataset.accessCode;
            const joinUrl = `${window.location.origin}/join/${accessCode}`;
            
            navigator.clipboard.writeText(joinUrl).then(() => {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i> Link Copied!';
                this.classList.add('bg-green-500');
                
                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.classList.remove('bg-green-500');
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
                alert('Failed to copy link. Please try again.');
            });
        });
    });

    // Handle modal reset when closed
    const createSessionModal = document.getElementById('createSessionModal');
    if (createSessionModal) {
        createSessionModal.addEventListener('hidden.bs.modal', function () {
            const form = this.querySelector('#createSessionForm');
            if (form) {
                form.reset();
            }
        });
    }
}); 