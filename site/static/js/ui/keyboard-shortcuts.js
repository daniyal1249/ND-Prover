/**
 * Keyboard Shortcuts
 * 
 * Handles keyboard shortcuts for proof line editing, including Enter, Tab,
 * Shift+Enter, and Shift+Tab combinations.
 * 
 * Dependencies: proof/line-operations.js, utils/input-processing.js,
 *               proof/focus-management.js
 */

import { filterInput, symbolize } from '../utils/input-processing.js';
import { commitActiveEditor } from '../proof/focus-management.js';

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

    // Commit the current text before we mutate state/render
    const commitLineText = () => {
      const processed = filterInput(input.textContent || '');
      const sym = processed ? symbolize(processed) : '';
      const i = state.lines.findIndex((l) => l.id === lineId);
      if (i !== -1) {
        state.lines[i].text = sym;
      }
    };

    // Determine whether this line can "end" its subproof
    const line = state.lines[idx];
    const next = state.lines[idx + 1];
    const canEndHere = !next || next.indent < line.indent || (next.indent === line.indent && next.isAssumption);

    // Shift+Enter => "End subproof" (only if allowed)
    if (e.key === 'Enter' && e.shiftKey && noMods) {
      e.preventDefault(); // Never insert a newline
      if (line.indent >= 1 && canEndHere) {
        commitLineText();
        // endSubproofAt is a wrapper function that handles render and focus
        endSubproofAt(idx);
      }
      return;
    }

    // Shift+Tab => "End subproof and begin another" (only if allowed)
    if (e.key === 'Tab' && e.shiftKey && noMods) {
      e.preventDefault(); // Don't move focus
      if (line.indent >= 1 && canEndHere) {
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

