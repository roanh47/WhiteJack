// WhiteJack - No Flash Version using fetch
(function() {
    'use strict';
    
    const ROLL_DURATION = 1500;  // Longer roll (was 600ms)
    const SCROLL_SPEED = 80;     // Slower number changes (was 50ms)
    let actionLocked = false;

    function lockActionUI() {
        actionLocked = true;
        setButtonsEnabled(false);
    }

    function unlockActionUI() {
        actionLocked = false;
        setButtonsEnabled(true);
    }

    function isWinningResult(resultText) {
        const text = String(resultText || '').toLowerCase();
        return text.includes('wint') || text.includes('auto-win');
    }

    function playConfetti() {
        const script = document.createElement('script');
        script.src = 'https://run.confettipage.com/here.js';
        script.dataset.confetticode = 'U2FsdGVkX1/mueQ6QB9Kdu4EuZlSHJWt4hos+OMOwhNnTx8i+zKlK2UHSdhBlRLaFRWioL7WwrxfTRWEaqYAhTTC6pGzPCwIIuGdp0SAaMSCaaGrpRJYCd/m6HJAPASTrOC4CWtswIkD9s3XuY/Don4yWYWJlhzbJoGy5LxFGK7+M6uXqmkrBQLXkjiqAp3y99raeC9plPVJAu+3BdJ5YHwtL2yL+QBzdeWvjgXckH8zMWoUaVpMF9c28OEJWVq5MZDYYa983uaI2gMs9iQHfGtmPfYP0bvdIYuaMnoausq8bsyBP4IsopsNIiF7bu+LGdle/BYeg79BmRZzbiEgzJwPaMN1tgTr6SFUJ8aadPwupBMWlmlv5dDE2JnmL+NWRhvd/yv/fpciaMNgjonlPHW8qLLDOePhiuBy77x3g7K3y/Q+BrMRH8UOlStKWdxwKfAF8L8KChzbrzV9/kmRoZPNv1QBqk1hI1Qu/u+jeBOQFmh/PEUCnSxBYH7jwQQABQo7kfHBUBkFa63ibwRvjf1nb3y4T+Ou3+aQfM7LJ+p8F+6ZpXQYlYr8sMck9G7NyuFNTa1lcgYm0Jfldd1zAUlq1ttXBHjzXvLdUGh4iCm7R5S30+GNfsK0hYT0F6wUwQkKb40q1x4ZnDk5alEI9OaoZoJaztIi/0TpCEeAIDIlvimlRTSl22zLVMdkZzb9a+C4o/lYlGWwMHBq5hFgzHuQTmfSYqQSIEGZTMZLtvOKblw1fZLxVYur/3PcgXfaXZjGjEOHGFLTrxZ/KePHqQ==';
        document.body.appendChild(script);
    }
    
    // Helper to show/hide totals
    function showTotals(show) {
        const playerTotal = document.querySelector('.player-slot .total');
        const scarTotal = document.querySelector('.scar-slot .scar-total');
        if (playerTotal) playerTotal.style.visibility = show ? 'visible' : 'hidden';
        if (scarTotal) scarTotal.style.visibility = show ? 'visible' : 'hidden';
    }
    
    function getPlayerRolls() { return document.getElementById('player-rolls'); }
    function getScarRolls() { return document.getElementById('scar-rolls'); }

    function clearPlaceholder(container) {
        container?.querySelector('.scar-placeholder')?.remove();
    }

    function buildActionForm(action, buttonClass, label) {
        return `
            <form method="post" action="/game" style="margin:0;">
                <input type="hidden" name="actie" value="${action}">
                <button type="submit" class="btn ${buttonClass}">${label}</button>
            </form>
        `;
    }

    function updateActionButtons(data) {
        const actions = document.querySelector('.actions');
        if (!actions || data.game_over) {
            return;
        }

        const buttons = [];
        if (!data.cut_used && (data.rolls?.length || 0) >= 2) {
            buttons.push(buildActionForm('cut', 'warn', 'Cut the Fuse (2x inzet)'));
        }

        buttons.push(buildActionForm('tick', 'primary', 'Tick (Hit)'));

        if ((data.rolls?.length || 0) >= 2) {
            buttons.push(buildActionForm('snip', 'secondary', 'Snip (Stand)'));
        }

        actions.innerHTML = buttons.join('');
        setupForms(actions);
        setButtonsEnabled(!actionLocked);
    }
    
    // Helper to enable/disable buttons
    function setButtonsEnabled(enabled) {
        document.querySelectorAll('.actions button').forEach(btn => {
            btn.disabled = !enabled;
        });
    }
    
    // Scroll a number element
    function scrollNumber(element, duration = ROLL_DURATION) {
        const finalValue = element?.dataset?.value;

        const interval = setInterval(() => {
            element.textContent = Math.floor(Math.random() * 12) + 1;
        }, SCROLL_SPEED);
        
        return new Promise(resolve => {
            setTimeout(() => {
                clearInterval(interval);
                if (finalValue !== undefined && finalValue !== null && finalValue !== '') {
                    element.textContent = String(finalValue);
                }
                resolve();
            }, duration);
        });
    }
    
    // Update game UI with new data (no page reload)
    function updateGameUI(data) {
        // Update player dice
        const playerRolls = getPlayerRolls();
        if (playerRolls && data.rolls) {
            playerRolls.innerHTML = data.rolls.length
                ? data.rolls.map(r =>
                    `<span class="card scar-roll" data-value="${r}">${r}</span>`
                ).join('')
                : '<span class="card scar-placeholder">?</span>';
        }
        
        // Update Scar dice
        const scarRolls = getScarRolls();
        if (scarRolls && data.scar_rolls) {
            scarRolls.innerHTML = data.scar_rolls.length
                ? data.scar_rolls.map(r =>
                    `<span class="card scar-roll" data-value="${r}">${r}</span>`
                ).join('')
                : '<span class="card scar-placeholder">?</span>';
            scarRolls.dataset.count = data.scar_rolls.length;
        }
        
        // Update totals
        const playerTotalEl = document.querySelector('.player-slot .total');
        if (playerTotalEl && data.player_total !== undefined) {
            playerTotalEl.textContent = `Totaal: ${data.player_total}`;
            playerTotalEl.style.display = data.rolls?.length ? 'inline' : 'none';
        }
        
        const scarTotalEl = document.querySelector('.scar-slot .scar-total');
        if (scarTotalEl && data.scar_total !== undefined) {
            scarTotalEl.textContent = `Totaal: ${data.scar_total}`;
            scarTotalEl.style.display = data.scar_rolls?.length ? 'inline' : 'none';
        }
        
        // Update game stage data attribute
        const gameStage = document.querySelector('.game-stage');
        if (gameStage) {
            gameStage.dataset.initialDeal = data.is_initial_deal ? 'true' : 'false';
            if (!data.game_over) {
                gameStage.classList.remove('game-over');
            }
        }

        updateActionButtons(data);
        
        // Handle game over
        if (data.game_over) {
            showGameOver(data);
        }
    }
    
    // Show game over state
    function showGameOver(data) {
        actionLocked = true;
        const gameStage = document.querySelector('.game-stage');
        if (gameStage) {
            gameStage.classList.add('game-over');
        }

        // Update title
        const title = document.querySelector('.ronde-titel');
        if (title) title.textContent = 'Uitslag';
        
        // Hide action buttons, show new game buttons
        const actions = document.querySelector('.actions');
        if (actions) {
            actions.innerHTML = `
                <a href="/reset" class="btn primary">Opnieuw spelen</a>
                <a href="/" class="btn secondary">Home</a>
            `;
        }
        
        // Show result panel
        let resultPanel = document.querySelector('.result-panel');
        if (!resultPanel) {
            resultPanel = document.createElement('div');
            resultPanel.className = 'result-panel game-result-panel';
            gameStage?.appendChild(resultPanel);
        } else {
            resultPanel.classList.add('game-result-panel');
        }
        resultPanel.innerHTML = `
            <div style="font-size: 24px; margin-bottom: 10px;">
                <strong>${data.resultaat}</strong>
            </div>
        `;
        resultPanel.style.display = 'block';
        
        // Update money display
        const moneyEl = document.querySelector('[style*="color:#4CAF50"]');
        if (moneyEl && data.money !== undefined) {
            moneyEl.textContent = '€' + data.money;
        }

        if (isWinningResult(data.resultaat)) {
            playConfetti();
        }
    }
    
    // Submit action via fetch (no page reload)
    async function submitAction(form) {
        const formData = new FormData(form);
        
        try {
            const response = await fetch('/game', {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            
            if (!response.ok) throw new Error('Request failed');
            
            return await response.json();
        } catch (err) {
            // Fallback to normal form submission on error
            form.submit();
            return null;
        }
    }
    
    // Handle player tick (hit)
    async function handleTick(form) {
        const playerRolls = getPlayerRolls();
        const scarRolls = getScarRolls();
        if (!playerRolls) {
            form.submit();
            return;
        }

        const isOpeningDeal =
            playerRolls.querySelectorAll('.card.scar-roll').length === 0 &&
            scarRolls?.querySelectorAll('.card.scar-roll').length === 0;

        // Play velvet shuffle mp3 on first tick
        if (!window._velvetShufflePlayed) {
            window._velvetShufflePlayed = true;
            try {
                let audio = document.getElementById('velvet-shuffle-audio');
                if (!audio) {
                    audio = document.createElement('audio');
                    audio.id = 'velvet-shuffle-audio';
                    audio.src = '/static/media/Velvet Shuffle.mp3';
                    audio.preload = 'auto';
                    document.body.appendChild(audio);
                }
                audio.currentTime = 0;
                audio.play();
            } catch (e) { /* ignore playback errors */ }
        }

        lockActionUI();
        showTotals(false); // Hide totals during roll

        if (isOpeningDeal) {
            const data = await submitAction(form);
            if (!data) {
                showTotals(true);
                unlockActionUI();
                return;
            }

            updateGameUI({...data, game_over: false});
            await animateInitialDeal();

            if (data.game_over) {
                showGameOver(data);
            } else {
                unlockActionUI();
            }
            return;
        }

        // Add new die that scrolls
        clearPlaceholder(playerRolls);
        const newDie = document.createElement('span');
        newDie.className = 'card scar-roll';
        newDie.textContent = Math.floor(Math.random() * 12) + 1;
        playerRolls.appendChild(newDie);

        // Scroll animation
        await scrollNumber(newDie, ROLL_DURATION);
        
        // Submit and update
        const data = await submitAction(form);
        if (!data) {
            showTotals(true);
            unlockActionUI();
            return;
        }
        
        // If game over with Scar rolling, delay showing result
        if (data.game_over && data.scar_rolls.length > 2) {
            // Update UI but hide game over state
            updateGameUI({...data, game_over: false});
            showTotals(true);
            
            // Animate Scar's dice, then show result
            await animateScarExtraDice(data.scar_rolls, () => {
                showGameOver(data);
            });
        } else {
            // Normal update
            updateGameUI(data);
            showTotals(true);
            
            // Re-enable buttons if game not over
            if (!data.game_over) {
                unlockActionUI();
            }
        }
    }
    
    // Handle player cut (double down)
    async function handleCut(form) {
        const playerRolls = getPlayerRolls();
        if (!playerRolls) {
            form.submit();
            return;
        }
        
        lockActionUI();
        showTotals(false); // Hide totals during roll
        
        // Double the bet display
        const betEl = document.querySelector('.player-slot .bet');
        if (betEl) {
            const currentBet = betEl.textContent.match(/\d+/)?.[0] || '0';
            betEl.textContent = `Speler - Inzet: €${parseInt(currentBet) * 2}`;
        }
        
        // Add new die that scrolls
        clearPlaceholder(playerRolls);
        const newDie = document.createElement('span');
        newDie.className = 'card scar-roll';
        newDie.textContent = Math.floor(Math.random() * 12) + 1;
        playerRolls.appendChild(newDie);
        
        // Scroll animation
        await scrollNumber(newDie, ROLL_DURATION);
        
        // Submit and update
        const previousScarCount = getScarRolls()?.querySelectorAll('.card.scar-roll').length || 0;
        const data = await submitAction(form);
        if (!data) {
            showTotals(true);
            unlockActionUI();
            return;
        }

        if (data.game_over && data.scar_rolls.length > previousScarCount) {
            updateGameUI({...data, game_over: false});
            showTotals(true);

            await animateScarExtraDice(data.scar_rolls, () => {
                showGameOver(data);
            }, previousScarCount);
        } else {
            updateGameUI(data);
            showTotals(true); // Show totals after roll

            // Re-enable buttons if game not over
            if (!data.game_over) {
                unlockActionUI();
            }
        }
    }
    
    // Handle player snip (stand)
    async function handleSnip(form) {
        lockActionUI();
        showTotals(false); // Hide totals during Scar's roll
        
        // Submit and update (Scar's dice added but result hidden)
        const previousScarCount = getScarRolls()?.querySelectorAll('.card.scar-roll').length || 0;
        const data = await submitAction(form);
        if (!data) {
            showTotals(true);
            unlockActionUI();
            return;
        }
        
        // Update dice but NOT the result panel yet
        updateGameUI({...data, game_over: false}); // Temporarily hide game over
        
        // Animate Scar's extra dice one by one with progressive totals
        if (data.scar_rolls.length > previousScarCount) {
            await animateScarExtraDice(data.scar_rolls, () => {
                // This callback runs after all dice finish
                showGameOver(data);
                showTotals(true);
            }, previousScarCount);
        } else {
            // No extra dice, just show result
            showGameOver(data);
            showTotals(true);
        }

        if (!data.game_over) {
            unlockActionUI();
        }
    }
    
    // Animate Scar's extra dice with progressive total updates
    async function animateScarExtraDice(scarRollsData, gameOverCallback, existingDiceCount = 2) {
        const scarContainer = getScarRolls();
        if (!scarContainer) return;
        
        const dice = scarContainer.querySelectorAll('.card.scar-roll');
        const extraDice = Array.from(dice).slice(existingDiceCount);

        // Hide all newly added Scar dice so they can be revealed one-by-one.
        extraDice.forEach(die => {
            die.style.visibility = 'hidden';
        });
        
        // Calculate running total from dice that were already visible before this action.
        let runningTotal = 0;
        const allDice = Array.from(dice);
        if (existingDiceCount > 0) {
            const existingDice = allDice.slice(0, existingDiceCount);
            runningTotal = existingDice.reduce((sum, d) => {
                const val = parseInt(d.dataset.value || d.textContent, 10);
                return sum + (isNaN(val) ? 0 : val);
            }, 0);
        }
        
        // Animate each extra die and update total progressively
        for (let i = 0; i < extraDice.length; i++) {
            const die = extraDice[i];

            // Reveal exactly one die at a time.
            die.style.visibility = 'visible';
            await scrollNumber(die, 800); // Slightly longer for drama
            
            // Add this die's value to running total
            const dieValue = parseInt(die.dataset.value || die.textContent, 10);
            if (!isNaN(dieValue)) {
                runningTotal += dieValue;
            }
            
            // Update Scar's total display
            const scarTotalEl = document.querySelector('.scar-slot .scar-total');
            if (scarTotalEl) {
                scarTotalEl.textContent = `Totaal: ${runningTotal}`;
            }
            
            // Pause between dice
            if (i < extraDice.length - 1) {
                await new Promise(r => setTimeout(r, 300));
            }
        }
        
        // Now show the final result
        if (gameOverCallback) {
            gameOverCallback();
        }
    }
    
    // Animate initial deal
    async function animateInitialDeal() {
        // Hide totals during animation
        showTotals(false);
        
        const playerDice = getPlayerRolls()?.querySelectorAll('.card.scar-roll');
        const scarDice = getScarRolls()?.querySelectorAll('.card.scar-roll');
        
        const promises = [];
        if (playerDice?.length === 2) {
            playerDice.forEach(die => promises.push(scrollNumber(die, ROLL_DURATION)));
        }
        if (scarDice?.length === 2) {
            scarDice.forEach(die => promises.push(scrollNumber(die, ROLL_DURATION)));
        }
        
        // Wait for all dice to finish
        await Promise.all(promises);
        
        // Show totals after animation
        showTotals(true);
    }
    
    // Setup forms
    function setupForms(root = document) {
        root.querySelectorAll('form[action*="game"]').forEach(form => {
            if (form.dataset.jsBound === 'true') {
                return;
            }

            form.dataset.jsBound = 'true';
            form.addEventListener('submit', async function(e) {
                e.preventDefault();
                if (actionLocked) {
                    return;
                }
                const action = form.querySelector('input[name="actie"]')?.value;
                
                if (action === 'tick') await handleTick(form);
                else if (action === 'cut') await handleCut(form);
                else if (action === 'snip') await handleSnip(form);
            });
        });
    }
    
    // Auto-hide flash messages after 5 seconds
    function setupFlashMessages() {
        const flashContainer = document.querySelector('.flash-messages');
        if (flashContainer) {
            setTimeout(() => {
                flashContainer.style.opacity = '0';
                setTimeout(() => flashContainer.remove(), 500);
            }, 5000);
        }
    }
    
    // Init
    function init() {
        setupForms();
        setupFlashMessages();
        
        const gameStage = document.querySelector('.game-stage');
        if (gameStage?.dataset.initialDeal === 'true') {
            // Hide totals initially, they'll show after animation
            showTotals(false);
            setTimeout(animateInitialDeal, 100);
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
