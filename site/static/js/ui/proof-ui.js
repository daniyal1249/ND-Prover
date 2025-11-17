/**
 * Proof UI Handlers
 * 
 * Handles UI interactions for the proof editor, including toolbar buttons.
 * 
 * Dependencies: state.js, proof/line-operations.js, proof/focus-management.js
 */

import { addLine } from '../proof/line-operations.js';
import { focusLineAt } from '../proof/focus-management.js';
import { serializeProofState } from '../utils/serialization.js';

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
    focusLineAt(0, 'formula-input');
  });

  // Begin subproof button (first-line only)
  const btnBeginSubproof = document.getElementById('btn-begin-subproof');
  btnBeginSubproof.addEventListener('click', () => {
    if (state.lines.length !== 0) {
      return;
    }
    addLine(state, 1, null, true, false); // First assumption at indent 1
    renderProof();
    focusLineAt(0, 'formula-input');
  });

  // Check proof button
  const btnCheckProof = document.getElementById('check-proof');
  const resultsSection = document.getElementById('results-pane');
  const resultsBox = document.getElementById('results');

  if (btnCheckProof && resultsBox) {
    btnCheckProof.addEventListener('click', async () => {
      // Reveal the results section if hidden (mirror proof-pane behavior)
      if (resultsSection && resultsSection.classList.contains('hidden')) {
        resultsSection.classList.remove('hidden');
      }

      resultsBox.classList.add('results--show');
      const payload = serializeProofState(state);

      resultsBox.textContent = 'Checking proof...';

      try {
        const response = await fetch('/api/check-proof', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        const data = await response.json();
        const message = data.message || '';

        if (!response.ok || !data.ok) {
          if (resultsSection) {
            resultsSection.classList.remove('results-pane--success');
            resultsSection.classList.add('results-pane--error');
          }
          resultsBox.textContent = message;
          return;
        }

        if (data.isComplete) {
          if (resultsSection) {
            resultsSection.classList.remove('results-pane--error');
            resultsSection.classList.add('results-pane--success');
          }
          resultsBox.textContent = message;
        } else {
          if (resultsSection) {
            resultsSection.classList.remove('results-pane--success');
            resultsSection.classList.add('results-pane--error');
          }
          resultsBox.textContent = message;
        }
      } catch (error) {
        if (resultsSection) {
          resultsSection.classList.remove('results-pane--success');
          resultsSection.classList.add('results-pane--error');
        }
        resultsBox.textContent = 'An error occurred while checking the proof.';
      }
    });
  }
}

