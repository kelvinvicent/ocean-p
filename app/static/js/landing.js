/* landing.js — reveal staggered + hover magnético */

(function () {
  // 1) Reveal letter-by-letter del headline (la palabra "útil" mantiene la cursiva)
  const headline = document.getElementById("headline");
  if (headline) {
    const text = headline.textContent.trim();
    headline.innerHTML = text
      .split("")
      .map((ch) =>
        ch === " " ? " " : `<span class="reveal-letter">${ch}</span>`
      )
      .join("");
    anime({
      targets: "#headline .reveal-letter",
      opacity: [0, 1],
      translateY: [16, 0],
      delay: anime.stagger(12, { start: 100 }),
      duration: 500,
      easing: "easeOutExpo",
    });
  }

  // 2) Stagger reveal de los bloques
  anime({
    targets: ".reveal-up",
    opacity: [0, 1],
    translateY: [20, 0],
    delay: anime.stagger(80, { start: 400 }),
    duration: 600,
    easing: "easeOutExpo",
  });

  // 3) Hover magnético en CTA — sutil
  const cta = document.getElementById("cta-button");
  if (cta) {
    cta.addEventListener("mousemove", (e) => {
      const rect = cta.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      anime({
        targets: cta,
        translateX: x * 0.08,
        translateY: y * 0.08,
        duration: 200,
        easing: "easeOutQuad",
      });
    });
    cta.addEventListener("mouseleave", () => {
      anime({
        targets: cta,
        translateX: 0,
        translateY: 0,
        duration: 300,
        easing: "easeOutElastic(1, .6)",
      });
    });
  }
})();
