/* report.js — animaciones del informe */

(function () {
  // Visibilidad por defecto desde CSS: el contenido SE VE siempre.
  // JS solo añade movimiento, nunca esconde.
  document.documentElement.classList.add("js");

  // 1) Reveal letter-by-letter del arquetipo
  const headline = document.getElementById("archetype-headline");
  if (headline && headline.textContent.trim().length > 0) {
    const text = headline.textContent.trim();
    headline.innerHTML = text
      .split("")
      .map((ch) =>
        ch === " " ? " " : `<span class="reveal-letter">${ch}</span>`
      )
      .join("");
    if (typeof anime !== "undefined") {
      anime({
        targets: "#archetype-headline .reveal-letter",
        opacity: [0, 1],
        translateY: [16, 0],
        delay: anime.stagger(15, { start: 100 }),
        duration: 500,
        easing: "easeOutExpo",
      });
    }
  }

  // 2) Stagger reveal de las secciones al cargar
  if (typeof anime !== "undefined") {
    anime({
      targets: ".reveal-up",
      opacity: [0, 1],
      translateY: [20, 0],
      delay: anime.stagger(80, { start: 500 }),
      duration: 600,
      easing: "easeOutExpo",
    });
  }

  // 3) Animación del gráfico de dimensiones al entrar en viewport
  const chart = document.getElementById("dimensions-chart");
  if (chart) {
    const fillBars = chart.querySelectorAll(".dimension-bar-fill");
    const runBars = () => {
      fillBars.forEach((bar) => {
        bar.style.transition = "width 1.2s cubic-bezier(0.16, 1, 0.3, 1)";
        bar.style.width = (bar.dataset.percentile || 0) + "%";
      });
    };
    if (typeof IntersectionObserver !== "undefined") {
      const chartObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              runBars();
              chartObserver.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.2 }
      );
      chartObserver.observe(chart);
    } else {
      runBars();
    }
    // Fallback duro: si el observer no dispara, a los 2s igual animamos
    setTimeout(runBars, 2000);
  }
})();

// Alpine.js data (placeholder por si se necesita reactividad en el futuro)
function reportState() {
  return { init() {} };
}
