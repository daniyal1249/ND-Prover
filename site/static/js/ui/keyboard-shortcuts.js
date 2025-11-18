/**
 * Keyboard Shortcuts
 * 
 * Handles keyboard shortcuts for proof line editing, including Enter, Tab,
 * Shift+Enter, and Shift+Tab combinations, as well as arrow-key navigation
 * between editable cells.
 * 
 * Dependencies: proof/line-operations.js, utils/input-processing.js,
 *               proof/focus-management.js
 */

import { processFormula, processJustification } from '../utils/input-processing.js';
import { commitActiveEditor } from '../proof/focus-management.js';

/**
 * Finds the next editable line index in the given column above or below a start index.
 * This operates on application state so it stays in sync with rendering/focus helpers.
 * 
 * @param {Object} state - Application state object
 * @param {number} startIdx - The starting line index
 * @param {number} direction - +1 for down, -1 for up
 * @param {string} field - Field selector ('formula-input' or 'justification-input')
 * @returns {number|null} The next editable line index, or null if none
 */
function findNextEditableIndex(state, startIdx, direction, field) {
  const lines = state.lines || [];
  const count = lines.length;

  let i = startIdx + direction;
  while (i >= 0 && i < count) {
    const line = lines[i];
    if (!line) {
      break;
    }
    const canEditFormula = !line.isPremise;
    const canEditJust = !(line.isAssumption || line.isPremise);
    const editable = field === 'formula-input' ? canEditFormula : canEditJust;
    if (editable) {
      return i;
    }
    i += direction;
  }

  return null;
}

/**
 * Attaches keyboard event handlers to a formula input element.
 * 
 * @param {HTMLElement} input - The input element to attach handlers to
 * @param {Object} state - Application state object
 * @param {number} idx - Index of the line
 * @param {number} lineId - Stable ID of the line
 * @param {Function} renderProof - Function to re-render the proof
 * @param {Function} addLineAfterSame - Function to add line after index (takes idx, calls render and focus)
 * @param {Function} beginSubproofBelow - Function to begin subproof (takes idx, calls render and focus)
 * @param {Function} endSubproofAt - Function to end subproof (takes idx, calls render and focus if needed)
 * @param {Function} endAndBeginAnotherAt - Function to end and begin subproof (takes idx, calls render and focus if needed)
 * @param {Function} focusLineAt - Function to focus a line
 */
export function attachKeyboardHandlers(
  input,
  state,
  idx,
  lineId,
  renderProof,
  addLineAfterSame,
  beginSubproofBelow,
  endSubproofAt,
  endAndBeginAnotherAt,
  focusLineAt
) {
  input.addEventListener('keydown', (e) => {
    const noMods = !e.metaKey && !e.ctrlKey && !e.altKey;

    const commitLineText = () => {
      const processed = processFormula(input.textContent || '');
      const i = state.lines.findIndex((l) => l.id === lineId);
      if (i !== -1) {
        state.lines[i].text = processed;
      }
    };

    // Arrow up/down => move within the formula column
    if ((e.key === 'ArrowUp' || e.key === 'ArrowDown') && noMods && !e.shiftKey) {
      const direction = e.key === 'ArrowDown' ? 1 : -1;
      const nextIdx = findNextEditableIndex(state, idx, direction, 'formula-input');
      if (nextIdx !== null) {
        e.preventDefault();
        // Mirror click behavior: commit current editor, re-render, then focus target line/field
        commitActiveEditor(state, processFormula, processJustification);
        renderProof();
        focusLineAt(nextIdx, 'formula-input');
      }
      return;
    }

    // Determine whether this line can "end" its subproof
    const line = state.lines[idx];
    const next = state.lines[idx + 1];
    const canEndHere =
      line &&
      (!next || next.indent < line.indent || (next.indent === line.indent && next.isAssumption));

    // Shift+Enter => "End subproof" (only if allowed)
    if (e.key === 'Enter' && e.shiftKey && noMods) {
      e.preventDefault(); // Never insert a newline
      if (line && line.indent >= 1 && canEndHere) {
        commitLineText();
        // endSubproofAt is a wrapper function that handles render and focus
        endSubproofAt(idx);
      }
      return;
    }

    // Shift+Tab => "End subproof and begin another" (only if allowed)
    if (e.key === 'Tab' && e.shiftKey && noMods) {
      e.preventDefault(); // Don't move focus
      if (line && line.indent >= 1 && canEndHere) {
        commitLineText();
        // endAndBeginAnotherAt is a wrapper function that handles render and focus
        endAndBeginAnotherAt(idx);
      }
      return;
    }

    // Enter => "Add line"
    if (e.key === 'Enter' && !e.shiftKey && noMods) {
      e.preventDefault(); // Don't insert a newline
      commitLineText(); // Store the latest edits
      // addLineAfterSame is a wrapper function that handles render and focus
      addLineAfterSame(idx);
      return;
    }

    // Tab => "Begin subproof"
    if (e.key === 'Tab' && !e.shiftKey && noMods) {
      e.preventDefault(); // Don't move focus out of the editor
      commitLineText();
      // beginSubproofBelow is a wrapper function that handles render and focus
      beginSubproofBelow(idx);
      return;
    }
  });
}

/**
 * Attaches keyboard event handlers to a justification input element.
 * 
 * @param {HTMLElement} justInput - The justification input element
 * @param {Object} state - Application state object
 * @param {number} idx - Index of the line
 * @param {Function} renderProof - Function to re-render the proof
 * @param {Function} focusLineAt - Function to focus a line
 */
export function attachJustificationKeyboardHandlers(
  justInput,
  state,
  idx,
  renderProof,
  focusLineAt
) {
  justInput.addEventListener('keydown', (e) => {
    const noMods = !e.metaKey && !e.ctrlKey && !e.altKey;

    // Arrow up/down => move within the justification column
    if ((e.key === 'ArrowUp' || e.key === 'ArrowDown') && noMods && !e.shiftKey) {
      const direction = e.key === 'ArrowDown' ? 1 : -1;
      const nextIdx = findNextEditableIndex(state, idx, direction, 'justification-input');
      if (nextIdx !== null) {
        e.preventDefault();
        // Mirror click behavior: commit current editor, re-render, then focus target line/field
        commitActiveEditor(state, processFormula, processJustification);
        renderProof();
        focusLineAt(nextIdx, 'justification-input');
      }
      return;
    }

    // Enter => same as ArrowDown (move to next editable justification cell)
    if (e.key === 'Enter' && !e.shiftKey && noMods) {
      const nextIdx = findNextEditableIndex(state, idx, 1, 'justification-input');

      if (nextIdx !== null) {
        e.preventDefault(); // Prevent newlines when we actually move
        // Commit before moving, to ensure justification text is captured
        commitActiveEditor(state, processFormula, processJustification);
        renderProof();
        focusLineAt(nextIdx, 'justification-input');
      } else {
        // No editable justification below: behave like ArrowDown would
        // on the last editable cell — do not re-render, just prevent newline.
        e.preventDefault();
      }
      return;
    }
  });
}

