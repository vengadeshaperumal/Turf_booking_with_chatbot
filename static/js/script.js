
function toggleMenu() {
    const menu = document.getElementById("navMenu");
    if (menu) {
        menu.classList.toggle("open");
    }
}

document.addEventListener("DOMContentLoaded", function () {
    // Automatically hide notification messages after a short delay.
    const messages = document.querySelectorAll(".message");

    messages.forEach(function (message) {
        setTimeout(function () {
            message.style.transition = "opacity 0.4s ease";
            message.style.opacity = "0";

            setTimeout(function () {
                message.remove();
            }, 450);
        }, 5000);
    });
});

