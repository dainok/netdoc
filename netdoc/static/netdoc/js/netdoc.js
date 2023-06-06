/*
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"
 */

function getCookie(name) {
    // Return cookie
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function addMessage(severity, text) {
    var container = document.createElement("div");
    container.setAttribute("class", "django-message toast align-items-center border-0 bg-" + severity + " fade show");
    container.setAttribute("data-django-type", "message");
    container.setAttribute("role", "alert");
    container.setAttribute("aria-live", "assertive");
    container.setAttribute("aria-atomic", "true");
    container.setAttribute("data-bs-delay", "10000");
    container.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="mdi mdi-check-circle me-1"></i> ` + text + `
            </div>
            <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `
    document.getElementById("django-messages").appendChild(container);

    function fadeOut() {
        container.classList.remove("show");
        container.classList.add("hide");
    }
    setTimeout(fadeOut, 10000);
}
