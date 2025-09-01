document.addEventListener("DOMContentLoaded", () => {
    const t = document.querySelectorAll(".tabs__btn"),
        e = document.querySelectorAll(".tab-content");
    t.forEach((c) => {
        c.addEventListener("click", () => {
            const a = c.getAttribute("data-tab");
            t.forEach((t) => t.classList.remove("active")), e.forEach((t) => t.classList.remove("active")), c.classList.add("active"), document.querySelector(`.tab-content[data-tab="${a}"]`).classList.add("active");
        });
    }),
        t.length > 0 && t[0].click();
});
