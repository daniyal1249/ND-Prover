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
  const base = pxVar('--min-line-span');
  const theIndent = pxVar('--indent');
  const gap = pxVar('--text-gap');
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
    bar.style.left = `calc(${i} * var(--indent))`;
    container.appendChild(bar);
  }
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
  const justW = computeJustWidth(state);
  document.documentElement.style.setProperty('--just-w', justW + 'px');

  const proofW = computeProofWidth(state);
  document.documentElement.style.setProperty('--proof-w', proofW + 'px');

  updateToolbarVisibility(toolbar, state);

  // Compute once, use inside the loop
  const lastPremiseIndex = state.lines.reduce((acc, l, i) => l.isPremise ? i : acc, -1);

  proofRoot.innerHTML = '';
  
  state.lines.forEach((line, idx) => {
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
    wrap.style.marginLeft = `calc(${line.indent} * var(--indent) + var(--text-gap))`;

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
    // Note: We don't position cursor here - let the browser handle natural cursor positioning
    // Cursor is only positioned at end when programmatically focusing (switching fields)
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
      state.lines[i].text = sym;
      renderProof();
    });

    // Keyboard handlers will be attached by main.js after rendering
    // The input element is stored with a data attribute for later enhancement

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
        renderProof();
        focusLineAt(idx, 'input');
      }
      // If already editing this field, let the browser handle cursor positioning naturally
      // (don't call focusLineAt, which would reset cursor to end)
    });

    wrap.appendChild(input);
    cell.appendChild(wrap);

    // Horizontal bars for assumptions and premise separator
    if (line.isAssumption) {
      const h = document.createElement('div');
      h.className = 'hbar';
      h.style.left = `calc(${line.indent} * var(--indent))`;
      const base = pxVar('--hbar-len');
      const extra = pxVar('--hbar-extra');
      const width = line.text ? (textWidth(line.text) + pxVar('--text-gap') + extra) : base;
      h.style.width = Math.max(base, width) + 'px';
      cell.appendChild(h);
    }
    if (idx === lastPremiseIndex) {
      const h = document.createElement('div');
      h.className = 'hbar';
      h.style.left = `calc(${line.indent} * var(--indent))`;
      const base = pxVar('--hbar-len');
      const extra = pxVar('--hbar-extra');
      const width = line.text ? (textWidth(line.text) + pxVar('--text-gap') + extra) : base;
      h.style.width = Math.max(base, width) + 'px';
      cell.appendChild(h);
    }

    // Justification column
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
      state.lines[i].justText = processed;
      if (processed) {
        just.classList.add('filled');
        jPlaceholder.classList.remove('show');
      } else {
        just.classList.remove('filled');
        jPlaceholder.classList.add('show');
      }
      renderProof();
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
        renderProof();
        focusLineAt(idx, 'just-input');
      }
      // If already editing this field, let the browser handle cursor positioning naturally
      // (don't call focusLineAt, which would reset cursor to end)
    });

    just.appendChild(justInput);

    // Actions column (hover buttons)
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
      // deleteLineAt is a wrapper function from main.js that handles commitActiveEditor, delete, and render
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
      // addLineAfterSame is a wrapper function from main.js that takes idx and handles render/focus
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
      // beginSubproofBelow is a wrapper function from main.js that takes idx and handles render/focus
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
      // endSubproofAt is a wrapper function from main.js that takes idx and handles render/focus
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
      // endAndBeginAnotherAt is a wrapper function from main.js that takes idx and handles render/focus
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

    row.append(ln, cell, just, actions);
    proofRoot.append(row);
  });
}

