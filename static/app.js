document.addEventListener('DOMContentLoaded', () => {
  // Animate initial rolls on the playing screen
  const diceCards = document.querySelectorAll('.card.dice[data-roll]');
  const scarCards = document.querySelectorAll('.card.scar-roll[data-roll]');
  if (diceCards.length > 0 || scarCards.length > 0) {
    // Hide totals initially
    document.querySelectorAll('.total, .scar-total').forEach(el => el.style.display = 'none');
    const duur = 3000 + Math.random() * 2000; // 3000ms tot 5000ms
    let start = Date.now();
    const animate = () => {
      diceCards.forEach(card => {
        card.textContent = Math.floor(Math.random() * 12) + 1;
        card.classList.add('rolling');
      });
      scarCards.forEach(card => {
        card.textContent = Math.floor(Math.random() * 12) + 1;
        card.classList.add('rolling');
      });
      if (Date.now() - start < duur) {
        setTimeout(animate, 80);
      } else {
        diceCards.forEach(card => {
          card.textContent = card.dataset.roll;
          card.classList.remove('rolling');
        });
        scarCards.forEach(card => {
          card.textContent = card.dataset.roll;
          card.classList.remove('rolling');
        });
        // Show totals after animation
        document.querySelectorAll('.total, .scar-total').forEach(el => el.style.display = 'inline');
      }
    };
    animate();
  }

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
        // Laat 3 tot 5 seconden lang willekeurige getallen zien als animatie, daarna verzenden
        const duur = 3000 + Math.random() * 2000; // 3000ms tot 5000ms
        let start = Date.now();
        weergave.classList.add('rolling');
        const interval = setInterval(() => {
          const t = Math.floor(Math.random() * 12) + 1;
          weergave.textContent = t;
          if (Date.now() - start > duur) {
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
});
