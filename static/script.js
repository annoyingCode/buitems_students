// These lines are to show the footer section with current year
const date = new Date();
let year = date.getFullYear();

let footer =  document.querySelector('footer');
footer.innerHTML = "<p> © " + year + " Copyright BUITEMS. All Rights Reserved </p>";

// This function will limit the user to select only 5 interests
function check() {
    let interests = document.getElementsByName('interest');
    let error = document.getElementById('error-message');
    let count = 0;

    for (let index = 0; index < interests.length; index++) {
        if (interests[index].checked == true) {
            count += 1;
        }
    }

    if (count > 5) {
        alert("Please select atmost 5 interests!")
        return false;
    }
    else if (count > 0) {
        for (let index = 0; index < interests.length; index++) {
            interests[index].required = false;
        }
        error.innerHTML = "";
        return true;
    }
    else {
        for (let index = 0; index < interests.length; index++) {
            interests[index].required = true;
        }
        error.innerHTML = "** Please select atleast one interest!";
        error.style.color = 'red';
        return true;
    }
}

// JavaScript Bootstrap function for disabling form submissions if there are invalid fields
(function () {
    'use strict'

    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    let forms = document.querySelectorAll('.needs-validation')

    // Loop over them and prevent submission
    Array.prototype.slice.call(forms)
        .forEach(function (form) {
            form.classList.add('was-validated')
            form.addEventListener('submit', function (event) {
                if (!form.checkValidity()) {
                    event.preventDefault()
                    event.stopPropagation()
                }
            }, false)
        })
})()