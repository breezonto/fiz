document.addEventListener("DOMContentLoaded", () => {
    const container = document.querySelector(".sidebar-container");
    const sidebar = document.querySelector(".sidebar-container .side");
    const button = document.getElementById("toggle_sidebar");

    if (!container || !sidebar || !button) {
        console.error("Sidebar elements not found.");
        return;
    }

    button.addEventListener("click", () => {
        const collapsed = sidebar.classList.toggle("collapsed");

        button.classList.toggle("collapsed", collapsed);

        button.textContent = collapsed ? "<" : ">";
    });
});

$(document).on("click", ".inset-toggle", function () {
    $(this).closest(".inset").toggleClass("collapsed");
});