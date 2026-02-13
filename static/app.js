document.addEventListener('DOMContentLoaded', () => {
  // Vang alle actie-formulieren op om een animatie te tonen voordat het formulier wordt verzonden
  document.querySelectorAll('.action-form').forEach(formulier => {
    formulier.addEventListener('submit', (e) => {
      // Voor niet-tick acties direct verzenden; voor tick/cut eerst animatie
      e.preventDefault();
      const actie = formulier.dataset.action;
      const handIndex = formulier.dataset.handIndex;
      const weergave = document.querySelector('.roll-display[data-hand="' + handIndex + '"]');

      const verzenden = () => {
        formulier.submit();
      };

      if (actie === 'tick' || actie === 'cut') {
        // Laat ~700ms lang willekeurige getallen zien als animatie, daarna verzenden
        let start = Date.now();
        weergave.classList.add('rolling');
        const interval = setInterval(() => {
          const t = Math.floor(Math.random() * 12) + 1;
          weergave.textContent = t;
          if (Date.now() - start > 700) {
            clearInterval(interval);
            weergave.classList.remove('rolling');
            verzenden();
          }
        }, 80);
      } else {
        verzenden();
      }
    });
  });

  // Startformulier: kleine animatie van het Scar-gebied als deze aanwezig is
  const startFormulier = document.querySelector('form[action$="start"]');
  if (startFormulier) {
    startFormulier.addEventListener('submit', (e) => {
      e.preventDefault();
      const scarWeergave = document.querySelector('.roll-display[data-hand="0"]');
      if (scarWeergave) scarWeergave.classList.add('rolling');
      setTimeout(() => startFormulier.submit(), 500);
    });
  }
});
