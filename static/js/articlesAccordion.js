document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".articles__item").forEach((e) => {
        e.addEventListener("click", function () {
            e.classList.toggle("active");
        });
    });
});
