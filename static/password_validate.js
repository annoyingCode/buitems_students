// Get the form element and the password input field
const form = document.querySelector('form');
const passwordInput = document.querySelector('#password');
const message = document.querySelector('#message');
const requirements = document.querySelector('#requirements');

// Define the password requirements
const passwordRequirements = {
    length: 8,
    lowercase: true,
    uppercase: true,
    digits: true,
    specialCharacters: true,
};

// Define a function to check if the password meets the requirements
function validatePassword(password) {
    let valid = true;

    if (password.length < passwordRequirements.length) {
        valid = false;
    }
    if (passwordRequirements.lowercase && !password.match(/[a-z]/)) {
        valid = false;
    }
    if (passwordRequirements.uppercase && !password.match(/[A-Z]/)) {
        valid = false;
    }
    if (passwordRequirements.digits && !password.match(/\d/)) {
        valid = false;
    }
    if (passwordRequirements.specialCharacters && !password.match(/[!#\$%&]/)) {
        valid = false;
    }

    return valid;
}

// Add an event listener to the password input field to validate the password on input
passwordInput.addEventListener('input', () => {
    const password = passwordInput.value;
    if (validatePassword(password)) {
        message.innerHTML = 'Password is valid';
        message.style.color = 'green';
    } else {
        message.innerHTML = 'Password is invalid';
        message.style.color = 'red';
    }

    // Update the requirements list to show whether each requirement is met
    requirements.children[0].style.color = password.length >= passwordRequirements.length ? 'green' : 'red';
    requirements.children[1].style.color = password.match(/[a-z]/) ? 'green' : 'red';
    requirements.children[2].style.color = password.match(/[A-Z]/) ? 'green' : 'red';
    requirements.children[3].style.color = password.match(/\d/) ? 'green' : 'red';
    requirements.children[4].style.color = password.match(/[!#\$%&]/) ? 'green' : 'red';
});

// Add an event listener to the form to prevent it from being submitted if the password is invalid
form.addEventListener('submit', (event) => {
    const password = passwordInput.value;
    if (!validatePassword(password)) {
        event.preventDefault();
    }
});