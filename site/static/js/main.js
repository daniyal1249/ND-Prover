/**
 * Main Application Entry Point
 * 
 * Initializes the application by setting up UI handlers and wiring up
 * all the modules together.
 * 
 * Dependencies: All other modules
 */

import { state } from './state.js';
import {
  renderProof as renderProofFn,
  updateToolbarVisibility,
  updateProofDimensions,
  removeLineFromDOM,
  insertLineInDOM,
  updateLineNumbers,
  updateActionButtons,
  createProofLine
} from './proof/rendering.js';
import {
  deleteLineAt,
  addLineAfterSame,
  beginSubproofBelow,
  endSubproofAt,
  endAndBeginAnotherAt
} from './proof/line-operations.js';
import { focusLineAt, commitActiveEditor } from './proof/focus-management.js';
import { processFormula, processJustification } from './utils/input-processing.js';
import {
  attachKeyboardHandlers,
  attachJustificationKeyboardHandlers
} from './ui/keyboard-shortcuts.js';
import { initProblemUI } from './ui/problem-ui.js';
import { initProofUI } from './ui/proof-ui.js';

/**
 * Creates a bound render function that can be passed around.
 * Also creates wrapper functions for action buttons that do incremental DOM updates.
 * 
 * @returns {Function} Bound render function
 */
function createRenderFunction() {
  const proofRoot = document.getElementById('proof');
  const toolbar = document.getElementById('toolbar');
  
  // Create wrapper functions once - reused for all renders
  const wrappedDeleteLineAt = (i) => {
    commitActiveEditor(state, processFormula, processJustification);
    
    // Find the row(s) to delete before modifying state
    const rowToDelete = proofRoot.querySelector(`.proof-line[data-index="${i}"]`);
    if (!rowToDelete) {
      return;
    }
    
    const line = state.lines[i];
    const lineId = Number(rowToDelete.dataset.id);
    
    // If deleting assumption, find all nested rows
    const rowsToRemove = [];
    if (line && line.isAssumption && line.id === lineId) {
      const startIndent = line.indent;
      let currentRow = rowToDelete.nextElementSibling;
      while (currentRow && currentRow.classList.contains('proof-line')) {
        const currentIdx = parseInt(currentRow.dataset.index, 10);
        const currentLine = state.lines[currentIdx];
        if (!currentLine) break;
        if (currentLine.indent < startIndent) break;
        if (currentLine.indent === startIndent && currentLine.isAssumption) break;
        rowsToRemove.push(currentRow);
        currentRow = currentRow.nextElementSibling;
      }
    }
    
    // Perform state operation
    deleteLineAt(state, i);
    
    // Remove rows from DOM
    removeLineFromDOM(rowToDelete, proofRoot);
    rowsToRemove.forEach(row => removeLineFromDOM(row, proofRoot));
    
    // Update line numbers and action buttons
    updateLineNumbers(proofRoot, state);
    updateActionButtons(
      proofRoot,
      state,
      wrappedDeleteLineAt,
      wrappedAddLineAfterSame,
      wrappedBeginSubproofBelow,
      wrappedEndSubproofAt,
      wrappedEndAndBeginAnotherAt
    );
    
    // Update dimensions and toolbar
    updateProofDimensions(state);
    updateToolbarVisibility(toolbar, state);
  };
  
  const wrappedAddLineAfterSame = (i) => {
    commitActiveEditor(state, processFormula, processJustification);
    
    // Perform state operation
    const newIdx = addLineAfterSame(state, i);
    
    // Insert new line in DOM
    const newRow = insertLineInDOM(
      state,
      newIdx,
      proofRoot,
      wrappedDeleteLineAt,
      wrappedAddLineAfterSame,
      wrappedBeginSubproofBelow,
      wrappedEndSubproofAt,
      wrappedEndAndBeginAnotherAt
    );
    
    // Attach keyboard handlers to new line
    if (newRow) {
      const input = newRow.querySelector('.formula-input');
      const justInput = newRow.querySelector('.justification-input');
      const lineId = Number(newRow.dataset.id);
      
      if (input) {
        attachKeyboardHandlers(
          input,
          state,
          lineId,
          wrappedAddLineAfterSame,
          wrappedBeginSubproofBelow,
          wrappedEndSubproofAt,
          wrappedEndAndBeginAnotherAt,
          focusLineAt
        );
      }
      if (justInput) {
        attachJustificationKeyboardHandlers(justInput, state, focusLineAt);
      }
    }
    
    // Update line numbers and action buttons
    updateLineNumbers(proofRoot, state);
    updateActionButtons(
      proofRoot,
      state,
      wrappedDeleteLineAt,
      wrappedAddLineAfterSame,
      wrappedBeginSubproofBelow,
      wrappedEndSubproofAt,
      wrappedEndAndBeginAnotherAt
    );
    
    // Update dimensions
    updateProofDimensions(state);
    
    // Focus new line
    focusLineAt(newIdx, 'formula-input', state);
  };
  
  const wrappedBeginSubproofBelow = (i) => {
    commitActiveEditor(state, processFormula, processJustification);
    
    // Perform state operation
    const newIdx = beginSubproofBelow(state, i);
    
    // Insert new line in DOM
    const newRow = insertLineInDOM(
      state,
      newIdx,
      proofRoot,
      wrappedDeleteLineAt,
      wrappedAddLineAfterSame,
      wrappedBeginSubproofBelow,
      wrappedEndSubproofAt,
      wrappedEndAndBeginAnotherAt
    );
    
    // Attach keyboard handlers to new line
    if (newRow) {
      const input = newRow.querySelector('.formula-input');
      const justInput = newRow.querySelector('.justification-input');
      const lineId = Number(newRow.dataset.id);
      
      if (input) {
        attachKeyboardHandlers(
          input,
          state,
          lineId,
          wrappedAddLineAfterSame,
          wrappedBeginSubproofBelow,
          wrappedEndSubproofAt,
          wrappedEndAndBeginAnotherAt,
          focusLineAt
        );
      }
      if (justInput) {
        attachJustificationKeyboardHandlers(justInput, state, focusLineAt);
      }
    }
    
    // Update line numbers and action buttons
    updateLineNumbers(proofRoot, state);
    updateActionButtons(
      proofRoot,
      state,
      wrappedDeleteLineAt,
      wrappedAddLineAfterSame,
      wrappedBeginSubproofBelow,
      wrappedEndSubproofAt,
      wrappedEndAndBeginAnotherAt
    );
    
    // Update dimensions
    updateProofDimensions(state);
    
    // Focus new line
    focusLineAt(newIdx, 'formula-input', state);
  };
  
  const wrappedEndSubproofAt = (i) => {
    commitActiveEditor(state, processFormula, processJustification);
    
    // Perform state operation
    const newIdx = endSubproofAt(state, i);
    if (newIdx === null) {
      return;
    }
    
    // Insert new line in DOM
    const newRow = insertLineInDOM(
      state,
      newIdx,
      proofRoot,
      wrappedDeleteLineAt,
      wrappedAddLineAfterSame,
      wrappedBeginSubproofBelow,
      wrappedEndSubproofAt,
      wrappedEndAndBeginAnotherAt
    );
    
    // Attach keyboard handlers to new line
    if (newRow) {
      const input = newRow.querySelector('.formula-input');
      const justInput = newRow.querySelector('.justification-input');
      const lineId = Number(newRow.dataset.id);
      
      if (input) {
        attachKeyboardHandlers(
          input,
          state,
          lineId,
          wrappedAddLineAfterSame,
          wrappedBeginSubproofBelow,
          wrappedEndSubproofAt,
          wrappedEndAndBeginAnotherAt,
          focusLineAt
        );
      }
      if (justInput) {
        attachJustificationKeyboardHandlers(justInput, state, focusLineAt);
      }
    }
    
    // Update line numbers and action buttons
    updateLineNumbers(proofRoot, state);
    updateActionButtons(
      proofRoot,
      state,
      wrappedDeleteLineAt,
      wrappedAddLineAfterSame,
      wrappedBeginSubproofBelow,
      wrappedEndSubproofAt,
      wrappedEndAndBeginAnotherAt
    );
    
    // Update dimensions
    updateProofDimensions(state);
    
    // Focus new line
    focusLineAt(newIdx, 'formula-input', state);
  };
  
  const wrappedEndAndBeginAnotherAt = (i) => {
    commitActiveEditor(state, processFormula, processJustification);
    
    // Perform state operation
    const newIdx = endAndBeginAnotherAt(state, i);
    if (newIdx === null) {
      return;
    }
    
    // Insert new line in DOM
    const newRow = insertLineInDOM(
      state,
      newIdx,
      proofRoot,
      wrappedDeleteLineAt,
      wrappedAddLineAfterSame,
      wrappedBeginSubproofBelow,
      wrappedEndSubproofAt,
      wrappedEndAndBeginAnotherAt
    );
    
    // Attach keyboard handlers to new line
    if (newRow) {
      const input = newRow.querySelector('.formula-input');
      const justInput = newRow.querySelector('.justification-input');
      const lineId = Number(newRow.dataset.id);
      
      if (input) {
        attachKeyboardHandlers(
          input,
          state,
          lineId,
          wrappedAddLineAfterSame,
          wrappedBeginSubproofBelow,
          wrappedEndSubproofAt,
          wrappedEndAndBeginAnotherAt,
          focusLineAt
        );
      }
      if (justInput) {
        attachJustificationKeyboardHandlers(justInput, state, focusLineAt);
      }
    }
    
    // Update line numbers and action buttons
    updateLineNumbers(proofRoot, state);
    updateActionButtons(
      proofRoot,
      state,
      wrappedDeleteLineAt,
      wrappedAddLineAfterSame,
      wrappedBeginSubproofBelow,
      wrappedEndSubproofAt,
      wrappedEndAndBeginAnotherAt
    );
    
    // Update dimensions
    updateProofDimensions(state);
    
    // Focus new line
    focusLineAt(newIdx, 'formula-input', state);
  };
  
  function render() {
    renderProofFn(
      state,
      proofRoot,
      toolbar,
      wrappedDeleteLineAt,
      wrappedAddLineAfterSame,
      wrappedBeginSubproofBelow,
      wrappedEndSubproofAt,
      wrappedEndAndBeginAnotherAt
    );
    
    // Attach keyboard handlers after rendering
    enhanceRenderedLines(
      wrappedAddLineAfterSame,
      wrappedBeginSubproofBelow,
      wrappedEndSubproofAt,
      wrappedEndAndBeginAnotherAt
    );
  }
  
  return render;
}

/**
 * Enhances proof line inputs with keyboard handlers after rendering.
 * This is called after each render to attach handlers to new elements.
 * 
 * @param {Function} wrappedAddLineAfterSame - Wrapper function for addLineAfterSame
 * @param {Function} wrappedBeginSubproofBelow - Wrapper function for beginSubproofBelow
 * @param {Function} wrappedEndSubproofAt - Wrapper function for endSubproofAt
 * @param {Function} wrappedEndAndBeginAnotherAt - Wrapper function for endAndBeginAnotherAt
 */
  function enhanceRenderedLines(
    wrappedAddLineAfterSame,
    wrappedBeginSubproofBelow,
    wrappedEndSubproofAt,
    wrappedEndAndBeginAnotherAt
  ) {
  const proofRoot = document.getElementById('proof');
  const lines = proofRoot.querySelectorAll('.proof-line');
  
  lines.forEach((row) => {
    const idx = parseInt(row.dataset.index, 10);
    const lineId = Number(row.dataset.id);
    const input = row.querySelector('.formula-input');
    const justInput = row.querySelector('.justification-input');
    
    if (input && !input.dataset.handlersAttached) {
      input.dataset.handlersAttached = 'true';
      
      attachKeyboardHandlers(
        input,
        state,
        lineId,
        wrappedAddLineAfterSame,
        wrappedBeginSubproofBelow,
        wrappedEndSubproofAt,
        wrappedEndAndBeginAnotherAt,
        focusLineAt
      );
    }

    if (justInput && !justInput.dataset.handlersAttached) {
      justInput.dataset.handlersAttached = 'true';
      attachJustificationKeyboardHandlers(
        justInput,
        state,
        focusLineAt
      );
    }
  });
}

/**
 * Initializes the application.
 */
function init() {
  // Create render function
  const render = createRenderFunction();
  
  // Initialize UI handlers
  initProblemUI(state, render);
  initProofUI(state, render);

  window.addEventListener('focus', () => {
    const ae = document.activeElement;
    if (ae && ae !== document.body && ae !== document.documentElement) {
      return;
    }

    const last = window.__ndLastFocus;
    if (!last) {
      return;
    }

    if (last.kind === 'proof') {
      focusLineAt(last.index, last.field || 'formula-input', state);
    } else if (last.kind === 'problem' && last.inputId) {
      const el = document.getElementById(last.inputId);
      if (el) {
        el.focus({ preventScroll: true });
      }
    }
  });
  
  // Initial render (if needed)
  render();
}

// Start the application when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

