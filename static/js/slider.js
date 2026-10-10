document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-slider]").forEach((slider) => {
        const track = slider.querySelector("[data-slider-track]");
        const previous = slider.querySelector("[data-slider-prev]");
        const next = slider.querySelector("[data-slider-next]");
        const progress = slider.querySelector("[data-slider-progress]");

        if (!track || !previous || !next || !progress) {
            return;
        }

        const scrollByPage = (direction) => {
            const amount = Math.max(track.clientWidth * 0.82, 220);
            track.scrollBy({ left: amount * direction, behavior: "smooth" });
        };

        const updateControls = () => {
            const maxScroll = Math.max(track.scrollWidth - track.clientWidth, 0);
            const ratio = maxScroll ? track.scrollLeft / maxScroll : 0;
            const width = maxScroll ? Math.max((track.clientWidth / track.scrollWidth) * 100, 18) : 100;
            const left = ratio * (100 - width);

            previous.disabled = track.scrollLeft <= 2;
            next.disabled = track.scrollLeft >= maxScroll - 2;
            progress.style.width = `${width}%`;
            progress.style.marginLeft = `${left}%`;
        };

        previous.addEventListener("click", () => scrollByPage(-1));
        next.addEventListener("click", () => scrollByPage(1));
        track.addEventListener("scroll", updateControls, { passive: true });
        window.addEventListener("resize", updateControls);
        updateControls();
    });
});
