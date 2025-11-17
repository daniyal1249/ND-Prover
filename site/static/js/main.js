/**
 * Main Application Entry Point
 * 
 * Initializes the application by setting up UI handlers and wiring up
 * all the modules together.
 * 
 * Dependencies: All other modules
 */

import { state } from './state.js';
import { renderProof as renderProofFn, updateToolbarVisibility } from './proof/rendering.js';
import { deleteLineAt, addLineAfterSame, beginSubproofBelow, endSubproofAt, endAndBeginAnotherAt } from './proof/line-operations.js';
import { focusLineAt, commitActiveEditor } from './proof/focus-management.js';
import { filterInput, symbolize, processJustification } from './utils/input-processing.js';
import { attachKeyboardHandlers, attachJustificationKeyboardHandlers } from './ui/keyboard-shortcuts.js';
import { initProblemUI } from './ui/problem-ui.js';
import { initProofUI } from './ui/proof-ui.js';

/**
 * Creates a bound render function that can be passed around.
 * This allows renderProof to call itself recursively.
 * 
 * @returns {Function} Bound render function
 */
function createRenderFunction() {
  const proofRoot = document.getElementById('proof');
  const toolbar = document.getElementById('toolbar');
  
  function render() {
    // Create wrapper functions that handle render and focus
    // These are passed to rendering.js for button handlers and keyboard shortcuts
    const wrappedDeleteLineAt = (i) => {
      commitActiveEditor(state, filterInput, symbolize, processJustification);
      deleteLineAt(state, i);
      render();
    };
    
    const wrappedAddLineAfterSame = (i) => {
      const newIdx = addLineAfterSame(state, i);
      render();
      focusLineAt(newIdx, 'formula-input');
    };
    
    const wrappedBeginSubproofBelow = (i) => {
      const newIdx = beginSubproofBelow(state, i);
      render();
      focusLineAt(newIdx, 'formula-input');
    };
    
    const wrappedEndSubproofAt = (i) => {
      const newIdx = endSubproofAt(state, i);
      if (newIdx !== null) {
        render();
        focusLineAt(newIdx, 'formula-input');
      }
    };
    
    const wrappedEndAndBeginAnotherAt = (i) => {
      const newIdx = endAndBeginAnotherAt(state, i);
      if (newIdx !== null) {
        render();
        focusLineAt(newIdx, 'formula-input');
      }
    };
    
    renderProofFn(
      state,
      proofRoot,
      toolbar,
      render, // Pass self for recursive calls
      wrappedDeleteLineAt,
      wrappedAddLineAfterSame,
      wrappedBeginSubproofBelow,
      wrappedEndSubproofAt,
      wrappedEndAndBeginAnotherAt
    );
    
    // Attach keyboard handlers after rendering
    enhanceRenderedLines(render, wrappedAddLineAfterSame, wrappedBeginSubproofBelow, wrappedEndSubproofAt, wrappedEndAndBeginAnotherAt);
  }
  
  return render;
}

/**
 * Enhances proof line inputs with keyboard handlers after rendering.
 * This is called after each render to attach handlers to new elements.
 * 
 * @param {Function} render - The render function to call after operations
 * @param {Function} wrappedAddLineAfterSame - Wrapper function for addLineAfterSame
 * @param {Function} wrappedBeginSubproofBelow - Wrapper function for beginSubproofBelow
 * @param {Function} wrappedEndSubproofAt - Wrapper function for endSubproofAt
 * @param {Function} wrappedEndAndBeginAnotherAt - Wrapper function for endAndBeginAnotherAt
 */
function enhanceRenderedLines(render, wrappedAddLineAfterSame, wrappedBeginSubproofBelow, wrappedEndSubproofAt, wrappedEndAndBeginAnotherAt) {
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
        idx,
        lineId,
        render,
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
        idx,
        render,
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

  // Restore last-focused editor/input when the window regains focus (e.g., after Alt+Tab)
  window.addEventListener('focus', () => {
    // If something is already focused (e.g., user clicked elsewhere), don't override it
    const ae = document.activeElement;
    if (ae && ae !== document.body && ae !== document.documentElement) {
      return;
    }

    const last = window.__ndLastFocus;
    if (!last) {
      return;
    }

    if (last.kind === 'proof') {
      focusLineAt(last.index, last.field || 'formula-input');
    } else if (last.kind === 'problem' && last.inputId) {
      const el = document.getElementById(last.inputId);
      if (el) {
        el.focus();
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

