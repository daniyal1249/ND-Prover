/**
 * Problem UI Handlers
 * 
 * Handles UI interactions for problem creation, including input box
 * commit handlers and the create problem button.
 * 
 * Dependencies: state.js, utils/input-processing.js, proof/line-operations.js
 */

import { processFormula } from '../utils/input-processing.js';
import { addLine } from '../proof/line-operations.js';
import { updateGenerateButtonVisibility } from './proof-ui.js';

/**
 * Commits an input box value to state, processing the text.
 * 
 * @param {HTMLElement} el - Input element
 * @param {string} target - Target property name in state.problem
 * @param {Object} state - Application state object
 */
export function commitInputBox(el, target, state) {
  const raw = el.value || '';
  const processed = processFormula(raw);
  el.value = processed;
  state.problem[target] = processed;
}

/**
 * Maps a base logic to its first-order version if the checkbox is checked.
 * 
 * @param {string} baseLogic - Base logic value (TFL, MLK, MLT, MLS4, MLS5)
 * @param {boolean} isFirstOrder - Whether first-order checkbox is checked
 * @returns {string} Logic value to use
 */
function getLogicValue(baseLogic, isFirstOrder) {
  if (!isFirstOrder) {
    return baseLogic;
  }
  
  const firstOrderMap = {
    'TFL': 'FOL',
    'MLK': 'FOMLK',
    'MLT': 'FOMLT',
    'MLS4': 'FOMLS4',
    'MLS5': 'FOMLS5'
  };
  
  return firstOrderMap[baseLogic] || baseLogic;
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
  const firstOrderCheckbox = document.getElementById('first-order');
  const premisesBox = document.getElementById('premises');
  const conclusionBox = document.getElementById('conclusion');

  premisesBox.addEventListener('focus', () => {
    window.__ndLastFocus = {
      kind: 'problem',
      inputId: 'premises'
    };
  });

  conclusionBox.addEventListener('focus', () => {
    window.__ndLastFocus = {
      kind: 'problem',
      inputId: 'conclusion'
    };
  });

  // Input box blur handlers
  premisesBox.addEventListener('blur', () => {
    commitInputBox(premisesBox, 'premisesText', state);
  });
  
  conclusionBox.addEventListener('blur', () => {
    commitInputBox(conclusionBox, 'conclusionText', state);
  });
  
  // Logic select and first-order checkbox change handlers
  function updateLogic() {
  }
  
  logicSelect.addEventListener('change', updateLogic);
  firstOrderCheckbox.addEventListener('change', updateLogic);

  // Create problem button handler
  const createBtn = document.getElementById('create-problem');
  createBtn.addEventListener('click', async () => {
    commitInputBox(premisesBox, 'premisesText', state);
    commitInputBox(conclusionBox, 'conclusionText', state);
    
    const baseLogic = logicSelect.value;
    const isFirstOrder = firstOrderCheckbox.checked;
    const logicLabel = getLogicValue(baseLogic, isFirstOrder);
    state.problem.logic = logicLabel;
    const premisesText = state.problem.premisesText || '';
    const conclusionText = state.problem.conclusionText || '';

    // Validate problem with backend before creating proof
    const payload = {
      logic: logicLabel,
      premisesText,
      conclusionText
    };

    const resultsSection = document.getElementById('results-pane');
    const resultsBox = document.getElementById('results');

    try {
      const response = await fetch('/api/validate-problem', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      const message = data.message || '';

      if (!response.ok || !data.ok) {
        // Hide the proof pane if visible
        const proofPane = document.getElementById('proof-pane');
        if (proofPane) {
          proofPane.classList.add('hidden');
        }

        // Show error in results pane directly under problem-setup
        if (resultsSection && resultsBox) {
          resultsSection.classList.remove('hidden');
          resultsSection.classList.remove('results-pane--success');
          resultsSection.classList.add('results-pane--error');
          resultsBox.textContent = message;
          resultsBox.classList.add('results--show');
        }
        return;
      }
    } catch (error) {
      // Network or server error; treat as validation failure
      const proofPane = document.getElementById('proof-pane');
      if (proofPane) {
        proofPane.classList.add('hidden');
      }
      if (resultsSection && resultsBox) {
        resultsSection.classList.remove('hidden');
        resultsSection.classList.remove('results-pane--success');
        resultsSection.classList.add('results-pane--error');
        resultsBox.textContent = 'An error occurred while validating the problem.';
        resultsBox.classList.add('results--show');
      }
      return;
    }

    // At this point, validation succeeded; clear any previous results
    if (resultsSection && resultsBox) {
      resultsSection.classList.add('hidden');
      resultsSection.classList.remove('results-pane--success', 'results-pane--error');
      resultsBox.textContent = '';
      resultsBox.classList.remove('results--show');
    }

    // Reset proof
    state.lines = [];
    state.nextId = 1;

    // Split premises on ; and add as PR lines
    const parts = premisesText.split(/;/).map((s) => s.trim()).filter(Boolean);

    // Build and show the summary line with mixed fonts
    const premStr = parts.join(', ');
    const conclStr = conclusionText || '';
    const divider = ' ∴ ';
    const mathContent = premStr ? (premStr + divider + conclStr) : (divider + conclStr);
    const problemSummary = document.getElementById('problem-summary');
    if (problemSummary) {
      // Split text: regular font before colon, math font after
      problemSummary.innerHTML =
        `Prove the following argument in ${logicLabel}:&nbsp;&nbsp;` +
        `<span class="math-content">${mathContent}</span>`;
    }

    // Create premise lines
    for (const p of parts) {
      const line = addLine(state, 0, null, false, true);
      line.text = p; // Already symbolized
      line.justText = 'PR'; // Show PR in justification column
    }

    // Reveal the proof section if hidden
    const proofPane = document.getElementById('proof-pane');
    if (proofPane && proofPane.classList.contains('hidden')) {
      proofPane.classList.remove('hidden');
    }

    // Update GENERATE button visibility based on logic
    updateGenerateButtonVisibility(state);

    renderProof();
  });

  return {
    logicSelect,
    firstOrderCheckbox,
    premisesBox,
    conclusionBox
  };
}

