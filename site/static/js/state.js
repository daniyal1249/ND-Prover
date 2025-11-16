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

