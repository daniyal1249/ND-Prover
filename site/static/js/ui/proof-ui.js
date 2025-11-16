/**
 * Proof UI Handlers
 * 
 * Handles UI interactions for the proof editor, including toolbar buttons.
 * 
 * Dependencies: state.js, proof/line-operations.js, proof/focus-management.js
 */

import { addLine } from '../proof/line-operations.js';
import { focusLineAt } from '../proof/focus-management.js';

/**
 * Initializes proof UI handlers (toolbar buttons).
 * 
 * @param {Object} state - Application state object
 * @param {Function} renderProof - Function to render the proof
 */
export function initProofUI(state, renderProof) {
  // Add line button (first-line only)
  const btnAddLine = document.getElementById('btn-add-line');
  btnAddLine.addEventListener('click', () => {
    if (state.lines.length !== 0) {
      return;
    }
    addLine(state, 0, null, false, false); // First top-level line
    renderProof();
    focusLineAt(0, 'input');
  });

  // Begin subproof button (first-line only)
  const btnBeginSubproof = document.getElementById('btn-begin-subproof');
  btnBeginSubproof.addEventListener('click', () => {
    if (state.lines.length !== 0) {
      return;
    }
    addLine(state, 1, null, true, false); // First assumption at indent 1
    renderProof();
    focusLineAt(0, 'input');
  });
}

