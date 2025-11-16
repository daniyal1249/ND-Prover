/**
 * Problem UI Handlers
 * 
 * Handles UI interactions for problem creation, including input box
 * commit handlers and the create problem button.
 * 
 * Dependencies: state.js, utils/input-processing.js, proof/line-operations.js
 */

import { filterInput, symbolize } from '../utils/input-processing.js';
import { addLine } from '../proof/line-operations.js';

/**
 * Commits an input box value to state, filtering and symbolizing the text.
 * 
 * @param {HTMLElement} el - Input element
 * @param {string} target - Target property name in state.problem
 * @param {Object} state - Application state object
 */
export function commitInputBox(el, target, state) {
  const raw = el.value || '';
  const processed = filterInput(raw);
  const sym = processed ? symbolize(processed) : '';
  el.value = sym; // Render symbolized text
  state.problem[target] = sym; // Store symbolized text
}

/**
 * Initializes problem UI handlers.
 * 
 * @param {Object} state - Application state object
 * @param {Function} renderProof - Function to render the proof
 * @returns {Object} Object containing DOM element references
 */
export function initProblemUI(state, renderProof) {
  const logicSelect = document.getElementById('logic');
  const premisesBox = document.getElementById('premises');
  const conclusionBox = document.getElementById('conclusion');

  // Input box blur handlers
  premisesBox.addEventListener('blur', () => {
    commitInputBox(premisesBox, 'premisesText', state);
  });
  
  conclusionBox.addEventListener('blur', () => {
    commitInputBox(conclusionBox, 'conclusionText', state);
  });
  
  // Logic select change handler
  logicSelect.addEventListener('change', () => {
    state.problem.logic = logicSelect.value;
  });

  // Create problem button handler
  const createBtn = document.getElementById('create-problem');
  createBtn.addEventListener('click', () => {
    commitInputBox(premisesBox, 'premisesText', state);
    commitInputBox(conclusionBox, 'conclusionText', state);
    state.problem.logic = logicSelect.value;

    // Reset proof
    state.lines = [];
    state.nextId = 1;

    // Split premises on , or ; and add as PR lines
    const parts = (state.problem.premisesText || '').split(/[;,]/).map((s) => s.trim()).filter(Boolean);

    // Build and show the summary line with mixed fonts
    const logicLabel = state.problem.logic;
    const premStr = parts.join(', ');
    const conclStr = state.problem.conclusionText || '';
    const divider = ' ∴ ';
    const mathContent = premStr ? (premStr + divider + conclStr) : (divider + conclStr);
    const problemSummary = document.getElementById('problem-summary');
    if (problemSummary) {
      // Split text: regular font before colon, math font after
      problemSummary.innerHTML = `Prove the following argument in ${logicLabel}: <span class="math-content">${mathContent}</span>`;
    }

    // Create premise lines
    for (const p of parts) {
      const line = addLine(state, 0, null, false, true);
      line.text = p; // Already symbolized
      line.justText = 'PR'; // Show PR in justification column
    }

    // Reveal the proof section if hidden
    const proofPane = document.getElementById('proof-section');
    if (proofPane && proofPane.style.display === 'none') {
      proofPane.style.display = 'block';
    }

    renderProof();
  });

  return {
    logicSelect,
    premisesBox,
    conclusionBox
  };
}

