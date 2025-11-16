/**
 * State Management
 * 
 * Manages the application's global state including proof lines and problem data.
 * This is the single source of truth for application state.
 */

/**
 * Application state object
 * @type {Object}
 * @property {Array} lines - Array of proof line objects
 *   Each line has the shape:
 *   {
 *     id: number,
 *     indent: number,
 *     text: string,        // symbolized formula text
 *     justText: string,    // symbolized rule + citations, e.g. "∧E, 1,2"
 *     isAssumption: boolean,
 *     isPremise: boolean,
 *     // kind indicates how this line should be replayed by the backend:
 *     // - 'premise'       -> part of the initial Proof context
 *     // - 'assumption'    -> begin_subproof(assumption)
 *     // - 'line'          -> add_line(formula, justification)
 *     // - 'close_subproof'-> end_subproof(formula, justification)
 *     // - 'end_and_begin' -> end_and_begin_subproof(assumption)
 *     kind: 'premise' | 'assumption' | 'line' | 'close_subproof' | 'end_and_begin'
 *   }
 * @property {number} nextId - Counter for generating unique line IDs
 * @property {Object} problem - Problem configuration
 * @property {string} problem.logic - Selected logic system (TFL, FOL, etc.)
 * @property {string} problem.premisesText - Symbolized premises text
 * @property {string} problem.conclusionText - Symbolized conclusion text
 */
export const state = {
  lines: [],
  nextId: 1,
  problem: {
    logic: 'TFL',
    premisesText: '',
    conclusionText: ''
  }
};

