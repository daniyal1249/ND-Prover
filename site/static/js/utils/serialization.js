/**
 * Proof serialization helpers
 *
 * These helpers prepare the frontend state for sending to the Python backend.
 * The shapes are chosen to map cleanly onto nd_prover.Proof operations.
 */

/**
 * Builds the raw line string expected by nd_prover.parser.parse_line.
 *
 * Examples:
 *   text: 'P → Q', justText: '→E, 1,2'
 *   => 'P → Q; →E, 1,2'
 *
 *   text: 'P', justText: ''
 *   => 'P'
 *
 * @param {Object} line - Line object from state.lines
 * @returns {string} Raw line string
 */
export function buildRawLineString(line) {
  const formula = (line.text || '').trim();
  const just = (line.justText || '').trim();
  if (!formula) {
    return '';
  }
  return just ? `${formula}; ${just}` : formula;
}

/**
 * Serializes the entire proof state into a JSON-ready object.
 *
 * Backend contract (per-line):
 *   {
 *     kind: 'premise' | 'assumption' | 'line' | 'close_subproof' | 'end_and_begin',
 *     indent: number,
 *     isAssumption: boolean,
 *     isPremise: boolean,
 *     raw: string  // output of buildRawLineString
 *   }
 *
 * @param {Object} state - Global application state
 * @returns {Object} JSON-serializable proof payload
 */
export function serializeProofState(state) {
  return {
    logic: state.problem.logic,
    premisesText: state.problem.premisesText,
    conclusionText: state.problem.conclusionText,
    lines: state.lines.map((line, index) => {
      const kind = line.kind;
      const isAssumptionLike = kind === 'assumption' || kind === 'end_and_begin';
      const formulaText = (line.text || '').trim();
      const justText = (line.justText || '').trim();

      return {
        lineNumber: index + 1,
        kind,
        indent: line.indent,
        isAssumption: line.isAssumption,
        isPremise: line.isPremise,
        formulaText,
        justText,
        // For assumptions, parse_assumption only takes the formula, not "formula; AS".
        raw: isAssumptionLike
          ? formulaText
          : buildRawLineString(line)
      };
    })
  };
}


