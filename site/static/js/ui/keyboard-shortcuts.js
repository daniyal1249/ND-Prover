/**
 * Keyboard Shortcuts
 * 
 * Handles keyboard shortcuts for proof line editing, including Enter, Tab,
 * Shift+Enter, and Shift+Tab combinations, as well as arrow-key navigation
 * between editable cells.
 * 
 * Dependencies: proof/focus-management.js
 */


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
 * @param {number} lineId - Stable ID of the line
 * @param {Function} addLineAfterSame - Function to add line after index (takes idx, calls render and focus)
 * @param {Function} beginSubproofBelow - Function to begin subproof (takes idx, calls render and focus)
 * @param {Function} endSubproofAt - Function to end subproof (takes idx, calls render and focus if needed)
 * @param {Function} endAndBeginAnotherAt - Function to end and begin subproof (takes idx, calls render and focus if needed)
 * @param {Function} focusLineAt - Function to focus a line
 */
export function attachKeyboardHandlers(
  input,
  state,
  lineId,
  addLineAfterSame,
  beginSubproofBelow,
  endSubproofAt,
  endAndBeginAnotherAt,
  focusLineAt
) {
  input.addEventListener('keydown', (e) => {
    const noMods = !e.metaKey && !e.ctrlKey && !e.altKey;

    const getCurrentIdx = () => {
      return state.lines.findIndex((l) => l.id === lineId);
    };
    if ((e.key === 'ArrowUp' || e.key === 'ArrowDown') && noMods && !e.shiftKey) {
      const currentIdx = getCurrentIdx();
      if (currentIdx === -1) {
        return;
      }
      const direction = e.key === 'ArrowDown' ? 1 : -1;
      const nextIdx = findNextEditableIndex(state, currentIdx, direction, 'formula-input');
      if (nextIdx !== null) {
        e.preventDefault();
        focusLineAt(nextIdx, 'formula-input', state);
      }
      return;
    }

    // Determine whether this line can "end" its subproof
    const currentIdx = getCurrentIdx();
    if (currentIdx === -1) {
      return;
    }
    const line = state.lines[currentIdx];
    const next = state.lines[currentIdx + 1];
    const canEndHere =
      line &&
      (!next || next.indent < line.indent || (next.indent === line.indent && next.isAssumption));

    if (e.key === 'Enter' && e.shiftKey && noMods) {
      e.preventDefault();
      if (line && line.indent >= 1 && canEndHere) {
        endSubproofAt(currentIdx);
      }
      return;
    }

    if (e.key === 'Tab' && e.shiftKey && noMods) {
      e.preventDefault();
      if (line && line.indent >= 1 && canEndHere) {
        endAndBeginAnotherAt(currentIdx);
      }
      return;
    }

    if (e.key === 'Enter' && !e.shiftKey && noMods) {
      e.preventDefault();
      addLineAfterSame(currentIdx);
      return;
    }

    if (e.key === 'Tab' && !e.shiftKey && noMods) {
      e.preventDefault();
      beginSubproofBelow(currentIdx);
      return;
    }
  });
}

/**
 * Attaches keyboard event handlers to a justification input element.
 * 
 * @param {HTMLElement} justInput - The justification input element
 * @param {Object} state - Application state object
 * @param {Function} focusLineAt - Function to focus a line
 */
export function attachJustificationKeyboardHandlers(
  justInput,
  state,
  focusLineAt
) {
  justInput.addEventListener('keydown', (e) => {
    const noMods = !e.metaKey && !e.ctrlKey && !e.altKey;

    const getCurrentIdx = () => {
      const row = justInput.closest('.proof-line');
      if (!row) return -1;
      const lineId = Number(row.dataset.id);
      return state.lines.findIndex((l) => l.id === lineId);
    };
    if ((e.key === 'ArrowUp' || e.key === 'ArrowDown') && noMods && !e.shiftKey) {
      const currentIdx = getCurrentIdx();
      if (currentIdx === -1) {
        return;
      }
      const direction = e.key === 'ArrowDown' ? 1 : -1;
      const nextIdx = findNextEditableIndex(state, currentIdx, direction, 'justification-input');
      if (nextIdx !== null) {
        e.preventDefault();
        focusLineAt(nextIdx, 'justification-input', state);
      }
      return;
    }

    if (e.key === 'Enter' && !e.shiftKey && noMods) {
      const currentIdx = getCurrentIdx();
      if (currentIdx === -1) {
        return;
      }
      const nextIdx = findNextEditableIndex(state, currentIdx, 1, 'justification-input');

      if (nextIdx !== null) {
        e.preventDefault();
        focusLineAt(nextIdx, 'justification-input', state);
      } else {
        e.preventDefault();
      }
      return;
    }
  });
}

