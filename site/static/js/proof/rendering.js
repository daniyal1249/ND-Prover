/**
 * Proof Rendering
 * 
 * Functions for rendering the proof display, including dynamic width calculation,
 * DOM element creation, and event handler attachment.
 * 
 * Dependencies: state.js, utils/text-measurement.js, proof/line-operations.js,
 *               utils/input-processing.js, proof/focus-management.js
 */

import { textWidth, pxVar } from '../utils/text-measurement.js';
import { filterInput, symbolize, processJustification } from '../utils/input-processing.js';
import { commitActiveEditor, focusLineAt } from './focus-management.js';

/**
 * Computes the required width for the proof formula column based on content.
 * 
 * @param {Object} state - Application state object
 * @returns {number} Required width in pixels
 */
export function computeProofWidth(state) {
  const base = pxVar('--proof-formula-min-width');
  const theIndent = pxVar('--proof-indent');
  const gap = pxVar('--proof-text-gap');
  let maxW = 0;
  
  for (const line of state.lines) {
    const contentSpan = Math.max(base, line.text ? textWidth(line.text) : 0);
    const total = (line.indent * theIndent) + gap + contentSpan;
    if (total > maxW) {
      maxW = total;
    }
  }
  
  if (state.lines.length === 0) {
    maxW = base;
  }
  
  // Pad preserved from original
  return Math.ceil(maxW) + 50;
}

/**
 * Computes the required width for the justification column based on content.
 * 
 * @param {Object} state - Application state object
 * @returns {number} Required width in pixels (minimum 100px)
 */
export function computeJustWidth(state) {
  let maxJust = 0;
  for (const line of state.lines) {
    const w = line.justText ? textWidth(line.justText) : 0;
    if (w > maxJust) {
      maxJust = w;
    }
  }
  // Min 100 + buffer
  return Math.ceil(Math.max(100, maxJust)) + 10;
}

/**
 * Updates the visibility of the toolbar based on whether there are any lines.
 * 
 * @param {HTMLElement} toolbar - Toolbar element
 * @param {Object} state - Application state object
 */
export function updateToolbarVisibility(toolbar, state) {
  if (!toolbar) {
    return;
  }
  toolbar.style.display = state.lines.length === 0 ? 'flex' : 'none';
}

/**
 * Creates vertical bars for subproof visualization.
 * 
 * @param {HTMLElement} container - Container element to add bars to
 * @param {number} depth - Depth/indent level
 * @param {boolean} capLast - Whether to cap the last bar (for assumptions)
 */
export function addBars(container, depth, capLast = false) {
  container.innerHTML = '';
  for (let i = 0; i <= depth; i++) {
    const bar = document.createElement('div');
    bar.className = 'bar';
    if (capLast && i === depth) {
      bar.classList.add('cap');
    }
    bar.style.left = `calc(${i} * var(--proof-indent))`;
    container.appendChild(bar);
  }
}

/**
 * Updates the old active cell's content when switching to a new field.
 * This keeps the keyboard open on mobile while still rendering processed text.
 * 
 * @param {Object} state - Application state object
 */
function updateOldActiveCell(state) {
  const oldActiveEl = document.activeElement;
  if (!oldActiveEl || !oldActiveEl.isContentEditable) {
    return;
  }

  const oldRow = oldActiveEl.closest('.proof-line');
  if (!oldRow) {
    return;
  }

  const oldLineId = Number(oldRow.dataset.id);
  const oldIdx = state.lines.findIndex((l) => l.id === oldLineId);
  if (oldIdx === -1) {
    return;
  }

  if (oldActiveEl.classList.contains('input')) {
    const processed = filterInput(oldActiveEl.textContent || '');
    const sym = processed ? symbolize(processed) : '';
    oldActiveEl.textContent = sym;
  } else if (oldActiveEl.classList.contains('just-input')) {
    const raw = oldActiveEl.textContent || '';
    const processed = raw ? processJustification(raw) : '';
    oldActiveEl.textContent = processed;
    
    // Update filled class and placeholder visibility for justification cells
    const oldJust = oldActiveEl.closest('.just');
    const oldPlaceholder = oldJust ? oldJust.querySelector('.j-placeholder') : null;
    if (processed) {
      if (oldJust) oldJust.classList.add('filled');
      if (oldPlaceholder) oldPlaceholder.classList.remove('show');
    } else {
      if (oldJust) oldJust.classList.remove('filled');
      if (oldPlaceholder) oldPlaceholder.classList.add('show');
    }
  }
}

/**
 * Handles blur event logic: updates state and conditionally re-renders.
 * Prevents keyboard flicker on mobile by updating in place when switching to another editable cell.
 * 
 * @param {HTMLElement} inputElement - The input element that was blurred
 * @param {string} processedText - The processed text to display
 * @param {Function} updateState - Function to update state with processed text
 * @param {Function} renderProof - Function to trigger full re-render
 */
function handleBlurWithConditionalRender(inputElement, processedText, updateState, renderProof) {
  updateState(processedText);
  
  // Check if we're switching to another editable cell (to prevent keyboard flicker on mobile)
  // Use requestAnimationFrame to check after the focus event has fired
  requestAnimationFrame(() => {
    const activeEl = document.activeElement;
    const isSwitchingToEditableCell = activeEl && activeEl.isContentEditable && (
      activeEl.classList.contains('input') || activeEl.classList.contains('just-input')
    );
    
    if (isSwitchingToEditableCell) {
      // Update text content in place to show processed text without recreating DOM
      // This keeps the keyboard open on mobile while still rendering the text
      inputElement.textContent = processedText;
    } else {
      // Full render when blurring to non-editable element
      renderProof();
    }
  });
}

/**
 * Creates a horizontal bar element for assumptions and premise separators.
 * 
 * @param {Object} line - Line object
 * @returns {HTMLElement} Horizontal bar element
 */
function createHorizontalBar(line) {
  const h = document.createElement('div');
  h.className = 'hbar';
  h.style.left = `calc(${line.indent} * var(--proof-indent))`;
  const base = pxVar('--horizontal-bar-length');
  const extra = pxVar('--horizontal-bar-extra-width');
  const width = line.text ? (textWidth(line.text) + pxVar('--proof-text-gap') + extra) : base;
  h.style.width = Math.max(base, width) + 'px';
  return h;
}

/**
 * Creates the formula input cell with all its elements and event handlers.
 * 
 * @param {Object} line - Line object
 * @param {number} idx - Line index
 * @param {number} lineId - Stable line ID
 * @param {Object} state - Application state object
 * @param {Function} renderProof - Function to trigger full re-render
 * @returns {HTMLElement} Formula cell element
 */
function createFormulaCell(line, idx, lineId, state, renderProof) {
  const cell = document.createElement('div');
  cell.className = 'cell';

  // Bars
  const bars = document.createElement('div');
  bars.className = 'bars';
  addBars(bars, line.indent, line.isAssumption);
  cell.appendChild(bars);

  // Hover background
  const hover = document.createElement('div');
  hover.className = 'hover-bg';
  cell.appendChild(hover);

  // Input wrapper
  const wrap = document.createElement('div');
  wrap.className = 'input-wrap';
  wrap.style.marginLeft = `calc(${line.indent} * var(--proof-indent) + var(--proof-text-gap))`;

  // Formula input
  const input = document.createElement('div');
  input.className = 'input';
  input.setAttribute('role', 'textbox');
  const canEditFormula = !line.isPremise;
  input.setAttribute('contenteditable', String(canEditFormula));
  input.spellcheck = false;
  input.textContent = line.text || '';

  if (!canEditFormula) {
    cell.classList.add('disabled');
  }

  // Input focus handler
  input.addEventListener('focus', () => {
    if (!canEditFormula) {
      return;
    }
    cell.classList.add('focused');
    // Remember last focused proof editor so we can restore it after Alt+Tab
    window.__ndLastFocus = {
      kind: 'proof',
      index: idx,
      field: 'input'
    };
  });

  // Input blur handler
  input.addEventListener('blur', () => {
    if (!canEditFormula) {
      return;
    }
    cell.classList.remove('focused');
    const processed = filterInput(input.textContent || '');
    const sym = processed ? symbolize(processed) : '';
    const i = state.lines.findIndex((l) => l.id === lineId);
    if (i === -1) {
      return;
    }
    
    handleBlurWithConditionalRender(
      input,
      sym,
      (text) => { state.lines[i].text = text; },
      renderProof
    );
  });

  // Cell click handler
  cell.addEventListener('pointerup', (e) => {
    e.preventDefault();
    if (!canEditFormula) {
      commitActiveEditor(state, filterInput, symbolize, processJustification);
      const ae = document.activeElement;
      if (ae && typeof ae.blur === 'function') {
        ae.blur();
      }
      return;
    }

    const ae = document.activeElement;
    const currentRow = ae && ae.isContentEditable ? ae.closest('.proof-line') : null;
    const currentIdx = currentRow ? parseInt(currentRow.dataset.index, 10) : -1;
    const alreadyEditingThisFormula =
      ae && ae.isContentEditable &&
      ae.classList.contains('input') &&
      currentIdx === idx;

    if (!alreadyEditingThisFormula) {
      // Switching to a different field - commit current edits and position cursor at end
      commitActiveEditor(state, filterInput, symbolize, processJustification);
      updateOldActiveCell(state);
      focusLineAt(idx, 'input');
    }
    // If already editing this field, let the browser handle cursor positioning naturally
    // (don't call focusLineAt, which would reset cursor to end)
  });

  wrap.appendChild(input);
  cell.appendChild(wrap);

  return cell;
}

/**
 * Creates the justification cell with all its elements and event handlers.
 * 
 * @param {Object} line - Line object
 * @param {number} idx - Line index
 * @param {number} lineId - Stable line ID
 * @param {Object} state - Application state object
 * @param {Function} renderProof - Function to trigger full re-render
 * @returns {HTMLElement} Justification cell element
 */
function createJustificationCell(line, idx, lineId, state, renderProof) {
  const just = document.createElement('div');
  just.className = 'just';

  const jHover = document.createElement('div');
  jHover.className = 'j-hover-bg';
  just.appendChild(jHover);

  const jPlaceholder = document.createElement('div');
  jPlaceholder.className = 'j-placeholder';
  const hasText = !!(line.justText && /\S/.test(line.justText));
  if (!hasText) {
    jPlaceholder.classList.add('show');
  }
  just.appendChild(jPlaceholder);

  const justInput = document.createElement('div');
  justInput.className = 'just-input';
  justInput.setAttribute('role', 'textbox');
  const editable = !(line.isAssumption || line.isPremise);
  justInput.setAttribute('contenteditable', String(editable));
  justInput.spellcheck = false;
  justInput.textContent = line.justText || '';

  if (!editable) {
    just.classList.add('disabled');
  }
  if (hasText) {
    just.classList.add('filled');
  }

  // Justification focus handler
  justInput.addEventListener('focus', () => {
    if (!editable) {
      return;
    }
    just.classList.add('focused');
    jPlaceholder.classList.remove('show');
    // Remember last focused proof editor so we can restore it after Alt+Tab
    window.__ndLastFocus = {
      kind: 'proof',
      index: idx,
      field: 'just-input'
    };
  });

  // Justification blur handler
  justInput.addEventListener('blur', () => {
    if (!editable) {
      return;
    }
    just.classList.remove('focused');
    const raw = justInput.textContent || '';
    const processed = raw ? processJustification(raw) : '';
    const i = state.lines.findIndex((l) => l.id === lineId);
    if (i === -1) {
      return;
    }
    
    handleBlurWithConditionalRender(
      justInput,
      processed,
      (text) => {
        state.lines[i].justText = text;
        if (text) {
          just.classList.add('filled');
          jPlaceholder.classList.remove('show');
        } else {
          just.classList.remove('filled');
          jPlaceholder.classList.add('show');
        }
      },
      renderProof
    );
  });

  // Justification click handler
  just.addEventListener('pointerup', (e) => {
    e.preventDefault();
    if (!editable) {
      commitActiveEditor(state, filterInput, symbolize, processJustification);
      const ae = document.activeElement;
      if (ae && typeof ae.blur === 'function') {
        ae.blur();
      }
      return;
    }

    const ae = document.activeElement;
    const currentRow = ae && ae.isContentEditable ? ae.closest('.proof-line') : null;
    const currentIdx = currentRow ? parseInt(currentRow.dataset.index, 10) : -1;
    const alreadyEditingThisJust =
      ae && ae.isContentEditable &&
      ae.classList.contains('just-input') &&
      currentIdx === idx;

    if (!alreadyEditingThisJust) {
      // Switching to a different field - commit current edits and position cursor at end
      commitActiveEditor(state, filterInput, symbolize, processJustification);
      updateOldActiveCell(state);
      focusLineAt(idx, 'just-input');
    }
    // If already editing this field, let the browser handle cursor positioning naturally
    // (don't call focusLineAt, which would reset cursor to end)
  });

  just.appendChild(justInput);
  return just;
}

/**
 * Creates action buttons for a proof line.
 * 
 * @param {Object} line - Line object
 * @param {number} idx - Line index
 * @param {number} lastPremiseIndex - Index of the last premise
 * @param {Object} state - Application state object
 * @param {Function} deleteLineAt - Function to delete a line
 * @param {Function} addLineAfterSame - Function to add line after index
 * @param {Function} beginSubproofBelow - Function to begin subproof
 * @param {Function} endSubproofAt - Function to end subproof
 * @param {Function} endAndBeginAnotherAt - Function to end and begin subproof
 * @returns {HTMLElement} Actions container element
 */
function createActionButtons(
  line,
  idx,
  lastPremiseIndex,
  state,
  deleteLineAt,
  addLineAfterSame,
  beginSubproofBelow,
  endSubproofAt,
  endAndBeginAnotherAt
) {
  const actions = document.createElement('div');
  actions.className = 'line-actions';

  // Delete button
  const btnDel = document.createElement('button');
  btnDel.className = 'action-btn';
  btnDel.type = 'button';
  btnDel.title = 'Delete this line';
  btnDel.setAttribute('aria-label', 'Delete this line');
  btnDel.textContent = 'x';
  btnDel.addEventListener('pointerup', (e) => {
    e.preventDefault();
    e.stopPropagation();
    deleteLineAt(idx);
  });

  // Add line button
  const btnAdd = document.createElement('button');
  btnAdd.className = 'action-btn';
  btnAdd.type = 'button';
  btnAdd.title = 'Add a line below';
  btnAdd.setAttribute('aria-label', 'Add a line below');
  btnAdd.textContent = '↓';
  btnAdd.addEventListener('pointerup', (e) => {
    e.preventDefault();
    e.stopPropagation();
    addLineAfterSame(idx);
  });

  // Begin subproof button
  const btnSub = document.createElement('button');
  btnSub.className = 'action-btn';
  btnSub.type = 'button';
  btnSub.title = 'Begin a subproof below';
  btnSub.setAttribute('aria-label', 'Begin a subproof below');
  btnSub.textContent = '→';
  btnSub.addEventListener('pointerup', (e) => {
    e.preventDefault();
    e.stopPropagation();
    beginSubproofBelow(idx);
  });

  // End subproof button
  const btnEnd = document.createElement('button');
  btnEnd.className = 'action-btn';
  btnEnd.type = 'button';
  btnEnd.title = 'End this subproof and add a line below';
  btnEnd.setAttribute('aria-label', 'End this subproof and add a line below');
  btnEnd.textContent = '←';
  btnEnd.addEventListener('pointerup', (e) => {
    e.preventDefault();
    e.stopPropagation();
    endSubproofAt(idx);
  });

  // End and begin another button
  const btnEndBegin = document.createElement('button');
  btnEndBegin.className = 'action-btn';
  btnEndBegin.type = 'button';
  btnEndBegin.title = 'End this subproof and begin another below';
  btnEndBegin.setAttribute('aria-label', 'End this subproof and begin another below');
  btnEndBegin.textContent = '↔';
  btnEndBegin.addEventListener('pointerup', (e) => {
    e.preventDefault();
    e.stopPropagation();
    endAndBeginAnotherAt(idx);
  });

  // Determine whether this line can "end" its subproof
  const next = state.lines[idx + 1];
  const canEndHere = !next || next.indent < line.indent || (next.indent === line.indent && next.isAssumption);

  // Add buttons based on line type
  if (line.isPremise) {
    if (idx === lastPremiseIndex) {
      actions.append(btnAdd, btnSub);
    }
  } else {
    actions.append(btnDel, btnAdd, btnSub);
    if (line.indent >= 1 && canEndHere) {
      actions.append(btnEnd, btnEndBegin);
    }
  }

  return actions;
}

/**
 * Creates a single proof line row with all its components.
 * 
 * @param {Object} line - Line object
 * @param {number} idx - Line index
 * @param {number} lastPremiseIndex - Index of the last premise
 * @param {Object} state - Application state object
 * @param {Function} renderProof - Function to trigger full re-render
 * @param {Function} deleteLineAt - Function to delete a line
 * @param {Function} addLineAfterSame - Function to add line after index
 * @param {Function} beginSubproofBelow - Function to begin subproof
 * @param {Function} endSubproofAt - Function to end subproof
 * @param {Function} endAndBeginAnotherAt - Function to end and begin subproof
 * @returns {HTMLElement} Proof line row element
 */
function createProofLine(
  line,
  idx,
  lastPremiseIndex,
  state,
  renderProof,
  deleteLineAt,
  addLineAfterSame,
  beginSubproofBelow,
  endSubproofAt,
  endAndBeginAnotherAt
) {
  const row = document.createElement('div');
  row.className = 'proof-line';
  row.dataset.index = idx;
  const lineId = line.id; // Stable id
  row.dataset.id = String(lineId);

  // Line number
  const ln = document.createElement('div');
  ln.className = 'lineno';
  ln.textContent = String(idx + 1);

  // Formula cell
  const cell = createFormulaCell(line, idx, lineId, state, renderProof);

  // Horizontal bars for assumptions and premise separator
  if (line.isAssumption) {
    cell.appendChild(createHorizontalBar(line));
  }
  if (idx === lastPremiseIndex) {
    cell.appendChild(createHorizontalBar(line));
  }

  // Justification column
  const just = createJustificationCell(line, idx, lineId, state, renderProof);

  // Actions column
  const actions = createActionButtons(
    line,
    idx,
    lastPremiseIndex,
    state,
    deleteLineAt,
    addLineAfterSame,
    beginSubproofBelow,
    endSubproofAt,
    endAndBeginAnotherAt
  );

  row.append(ln, cell, just, actions);
  return row;
}

/**
 * Updates CSS custom properties for proof dimensions.
 * 
 * @param {Object} state - Application state object
 */
function updateProofDimensions(state) {
  const justW = computeJustWidth(state);
  document.documentElement.style.setProperty('--justification-width', justW + 'px');

  const proofW = computeProofWidth(state);
  document.documentElement.style.setProperty('--proof-formula-width', proofW + 'px');
}

/**
 * Renders the entire proof by creating DOM elements for each line.
 * This is the main rendering function that updates the proof display.
 * 
 * @param {Object} state - Application state object
 * @param {HTMLElement} proofRoot - Root element for proof lines
 * @param {HTMLElement} toolbar - Toolbar element
 * @param {Function} renderProof - Reference to renderProof for recursive calls
 * @param {Function} deleteLineAt - Function to delete a line
 * @param {Function} addLineAfterSame - Function to add line after index
 * @param {Function} beginSubproofBelow - Function to begin subproof
 * @param {Function} endSubproofAt - Function to end subproof
 * @param {Function} endAndBeginAnotherAt - Function to end and begin subproof
 */
export function renderProof(
  state,
  proofRoot,
  toolbar,
  renderProof,
  deleteLineAt,
  addLineAfterSame,
  beginSubproofBelow,
  endSubproofAt,
  endAndBeginAnotherAt
) {
  // Update dynamic widths
  updateProofDimensions(state);
  updateToolbarVisibility(toolbar, state);

  // Compute once, use inside the loop
  const lastPremiseIndex = state.lines.reduce((acc, l, i) => l.isPremise ? i : acc, -1);

  proofRoot.innerHTML = '';
  
  state.lines.forEach((line, idx) => {
    const row = createProofLine(
      line,
      idx,
      lastPremiseIndex,
      state,
      renderProof,
      deleteLineAt,
      addLineAfterSame,
      beginSubproofBelow,
      endSubproofAt,
      endAndBeginAnotherAt
    );
    proofRoot.append(row);
  });
}
