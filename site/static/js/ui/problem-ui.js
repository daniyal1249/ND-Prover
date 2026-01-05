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
import { getLogicValue } from '../utils/logic-mapping.js';
import { renderProblemSummary, splitPremisesTopLevel } from './problem-summary.js';
import { scheduleUrlUpdate } from '../utils/url-state.js';

function hideAndClearProof(state) {
  const proofPane = document.getElementById('proof-pane');
  if (proofPane) {
    proofPane.classList.add('hidden');
  }

  const summary = document.getElementById('problem-summary');
  if (summary) {
    summary.textContent = '';
  }

  state.lines = [];
  state.nextId = 1;
  state.proofProblem = null;
}

/**
 * Commits an input box value to state, processing the text.
 * 
 * @param {HTMLElement} el - Input element
 * @param {string} target - Target property name in state.problemDraft
 * @param {Object} state - Application state object
 */
export function commitInputBox(el, target, state) {
  const raw = el.value || '';
  const processed = processFormula(raw);
  el.value = processed;
  state.problemDraft[target] = processed;
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

  // Input box blur handlers
  premisesBox.addEventListener('blur', () => {
    commitInputBox(premisesBox, 'premisesText', state);
    scheduleUrlUpdate();
  });
  
  conclusionBox.addEventListener('blur', () => {
    commitInputBox(conclusionBox, 'conclusionText', state);
    scheduleUrlUpdate();
  });
  
  // Logic select and first-order checkbox change handlers
  function updateLogic() {
    const baseLogic = logicSelect.value;
    const isFirstOrder = firstOrderCheckbox.checked;
    state.problemDraft.logic = getLogicValue(baseLogic, isFirstOrder);
    updateGenerateButtonVisibility(state);
    scheduleUrlUpdate();
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
    state.problemDraft.logic = logicLabel;
    const premisesText = state.problemDraft.premisesText || '';
    const conclusionText = state.problemDraft.conclusionText || '';

    // Validate problem before creating a proof.
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
        hideAndClearProof(state);
        scheduleUrlUpdate();

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
      // Network/server error; treat as validation failure.
      hideAndClearProof(state);
      scheduleUrlUpdate();
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

    // Reset proof editor state and commit the problem to the proof pane.
    state.lines = [];
    state.nextId = 1;
    state.proofProblem = {
      logic: logicLabel,
      premisesText,
      conclusionText
    };

    // Split premises on commas/semicolons at top level and add as PR lines
    const parts = splitPremisesTopLevel(premisesText);

    // Proof-pane summary.
    renderProblemSummary(
      document.getElementById('problem-summary'),
      state.proofProblem.logic,
      state.proofProblem.premisesText,
      state.proofProblem.conclusionText
    );

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
    scheduleUrlUpdate();
  });

  return {
    logicSelect,
    firstOrderCheckbox,
    premisesBox,
    conclusionBox
  };
}
