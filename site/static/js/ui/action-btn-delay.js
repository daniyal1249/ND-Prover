/**
 * Action Button Delay (Touch Only)
 *
 * On touch devices, a single tap can both reveal per-line action buttons (via
 * the browser's touch-to-hover behavior) and activate a button immediately.
 * This module adds a small activation delay so buttons only execute once they've
 * been visible for at least `delayMs`.
 *
 * Dependencies: none
 */

function isHidden(actionsEl) {
  const cs = getComputedStyle(actionsEl);
  return (
    cs.opacity === '0' ||
    cs.pointerEvents === 'none' ||
    cs.visibility === 'hidden'
  );
}

function getRow(target) {
  return target && target.closest ? target.closest('.proof-line') : null;
}

/**
 * Enables a touch-specific activation delay for per-line action buttons.
 *
 * @param {HTMLElement} proofRoot - Root element containing proof lines
 * @param {number} delayMs - Minimum time actions must be visible before clicks work
 */
export function initActionBtnDelay(proofRoot, delayMs = 150) {
  if (!proofRoot) {
    return;
  }

  const revealAtByRow = new WeakMap();

  function markRevealIfHidden(row) {
    const actions = row.querySelector('.line-actions');
    if (!actions) {
      return;
    }
    if (isHidden(actions)) {
      revealAtByRow.set(row, performance.now());
    }
  }

  // Arm the delay on touch interactions that first reveal the actions.
  proofRoot.addEventListener(
    'pointerdown',
    (e) => {
      if (e.pointerType !== 'touch') {
        return;
      }
      const row = getRow(e.target);
      if (!row) {
        return;
      }
      markRevealIfHidden(row);
    },
    true
  );

  // touchstart may fire even when pointerdown doesn't.
  proofRoot.addEventListener(
    'touchstart',
    (e) => {
      const row = getRow(e.target);
      if (!row) {
        return;
      }
      markRevealIfHidden(row);
    },
    { capture: true, passive: true }
  );

  // Block action button clicks until they have been visible for delayMs.
  proofRoot.addEventListener(
    'click',
    (e) => {
      const btn = e.target.closest('.action-btn');
      if (!btn) {
        return;
      }

      const row = btn.closest('.proof-line');
      if (!row) {
        return;
      }

      const t0 = revealAtByRow.get(row);
      if (!t0) {
        return;
      }

      if (performance.now() - t0 < delayMs) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
      }
    },
    true
  );
}
