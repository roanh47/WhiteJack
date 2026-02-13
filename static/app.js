document.addEventListener('DOMContentLoaded', () => {
  // intercept action forms to show a roll animation before submitting
  document.querySelectorAll('.action-form').forEach(form => {
    form.addEventListener('submit', (e) => {
      // For non-tick actions we can submit immediately; for tick/cut we show animation
      e.preventDefault();
      const action = form.dataset.action;
      const handIndex = form.dataset.handIndex;
      const display = document.querySelector('.roll-display[data-hand="' + handIndex + '"]');

      const doSubmit = () => {
        form.submit();
      };

      if (action === 'tick' || action === 'cut') {
        // animate random numbers for ~700ms then submit
        let start = Date.now();
        display.classList.add('rolling');
        const interval = setInterval(() => {
          const t = Math.floor(Math.random() * 12) + 1;
          display.textContent = t;
          if (Date.now() - start > 700) {
            clearInterval(interval);
            display.classList.remove('rolling');
            doSubmit();
          }
        }, 80);
      } else {
        doSubmit();
      }
    });
  });

  // start form: slight animation of scar area if present
  const startForm = document.querySelector('form[action$="start"]');
  if (startForm) {
    startForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const scarDisplay = document.querySelector('.roll-display[data-hand="0"]');
      if (scarDisplay) scarDisplay.classList.add('rolling');
      setTimeout(() => startForm.submit(), 500);
    });
  }
});
