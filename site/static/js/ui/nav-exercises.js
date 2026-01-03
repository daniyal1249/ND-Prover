/**
 * Exercises nav toggle
 *
 * Clicking "Exercises" replaces it with the three logic buttons (TFL/FOL/ML).
 * Clicking anywhere outside restores the "Exercises" button.
 *
 * Dependencies: none
 */

function initExercisesNav() {
  const root = document.getElementById('nav-exercises');
  const toggle = document.getElementById('nav-exercises-toggle');
  const options = document.getElementById('nav-exercises-options');

  if (!root || !toggle || !options) {
    return;
  }

  let isOpen = false;

  function open() {
    if (isOpen) return;
    isOpen = true;
    root.classList.add('is-open');
    toggle.setAttribute('aria-expanded', 'true');
    options.hidden = false;
  }

  function close() {
    if (!isOpen) return;
    isOpen = false;
    root.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    options.hidden = true;
  }

  toggle.addEventListener('click', (e) => {
    e.preventDefault();
    open();
  });

  // Close when clicking anywhere outside the exercises nav container.
  document.addEventListener('click', (e) => {
    if (!isOpen) return;
    const target = e.target;
    if (target && root.contains(target)) {
      return;
    }
    close();
  });

  document.addEventListener('keydown', (e) => {
    if (!isOpen) return;
    if (e.key === 'Escape') {
      close();
      toggle.focus({ preventScroll: true });
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initExercisesNav);
} else {
  initExercisesNav();
}
