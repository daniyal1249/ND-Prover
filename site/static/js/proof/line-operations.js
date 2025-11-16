/**
 * Proof Line Operations
 * 
 * Functions for adding, deleting, and manipulating proof lines and subproofs.
 * 
 * Dependencies: state.js
 */

/**
 * Adds a new proof line to the state.
 * 
 * @param {Object} state - Application state object
 * @param {number} indent - Indentation level (0 = top level)
 * @param {number|null} afterIndex - Index to insert after (null = append)
 * @param {boolean} isAssumption - Whether this is an assumption line
 * @param {boolean} isPremise - Whether this is a premise line
 * @returns {Object} The created line object
 */
export function addLine(state, indent = 0, afterIndex = null, isAssumption = false, isPremise = false) {
  const line = {
    id: state.nextId++,
    indent,
    text: '',
    justText: isAssumption ? 'AS' : '',
    isAssumption,
    isPremise
  };
  
  if (afterIndex == null || afterIndex < 0) {
    state.lines.push(line);
  } else {
    state.lines.splice(afterIndex + 1, 0, line);
  }
  
  return line;
}

/**
 * Deletes a line at the given index. If it's an assumption line,
 * deletes the entire subproof (all nested lines).
 * 
 * @param {Object} state - Application state object
 * @param {number} i - Index of line to delete
 */
export function deleteLineAt(state, i) {
  if (i < 0 || i >= state.lines.length) {
    return;
  }
  
  const line = state.lines[i];
  if (line.isAssumption) {
    // Delete entire subproof
    const startIndent = line.indent;
    let j = i + 1;
    while (j < state.lines.length) {
      const nxt = state.lines[j];
      if (nxt.indent < startIndent) {
        break;
      }
      if (nxt.indent === startIndent && nxt.isAssumption) {
        break;
      }
      j++;
    }
    state.lines.splice(i, j - i);
  } else {
    // Delete single line
    state.lines.splice(i, 1);
  }
}

/**
 * Adds a line after the given index at the same indent level.
 * 
 * @param {Object} state - Application state object
 * @param {number} i - Index to add after
 * @returns {number} Index of the newly added line
 */
export function addLineAfterSame(state, i) {
  const indent = state.lines[i] ? state.lines[i].indent : 0;
  addLine(state, indent, i, false, false);
  return i + 1;
}

/**
 * Begins a subproof below the given index by adding an assumption line.
 * 
 * @param {Object} state - Application state object
 * @param {number} i - Index to add subproof after
 * @returns {number} Index of the newly added assumption line
 */
export function beginSubproofBelow(state, i) {
  const base = state.lines[i] ? state.lines[i].indent : 0;
  addLine(state, base + 1, i, true, false);
  return i + 1;
}

/**
 * Ends the subproof at the given index and adds a line at the parent level.
 * 
 * @param {Object} state - Application state object
 * @param {number} i - Index of line ending the subproof
 * @returns {number|null} Index of newly added line, or null if invalid
 */
export function endSubproofAt(state, i) {
  const line = state.lines[i];
  if (!line || line.indent < 1) {
    return null;
  }
  const parentIndent = line.indent - 1;
  addLine(state, parentIndent, i, false, false);
  return i + 1;
}

/**
 * Ends the subproof at the given index and begins another at the same level.
 * 
 * @param {Object} state - Application state object
 * @param {number} i - Index of line ending the subproof
 * @returns {number|null} Index of newly added assumption line, or null if invalid
 */
export function endAndBeginAnotherAt(state, i) {
  const line = state.lines[i];
  if (!line || line.indent < 1) {
    return null;
  }
  addLine(state, line.indent, i, true, false);
  return i + 1;
}

