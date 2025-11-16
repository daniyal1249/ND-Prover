/**
 * Input Processing Utilities
 * 
 * Functions for processing and normalizing user input, including
 * filtering, symbolization, and justification processing.
 * 
 * Dependencies: utils/symbolization.js
 */

import { symbolize as symbolizeText } from './symbolization.js';

/**
 * Filters and normalizes input text by trimming and collapsing whitespace.
 * 
 * @param {string} s - Input string to filter
 * @returns {string} Filtered and normalized string
 */
export function filterInput(s) {
  let t = (s ?? '').trim();
  // Normalize all whitespace to single spaces
  t = t.replace(/\s/g, ' ');
  // Collapse multiple spaces to single space
  t = t.replace(/ +/g, ' ');
  return t;
}

/**
 * Symbolizes logical formulas by converting natural language operators
 * to logical symbols using the JavaScript symbolization module.
 * 
 * @param {string} raw - Raw input text to symbolize
 * @returns {string} Symbolized text
 */
export function symbolize(raw) {
  if (!raw) {
    return '';
  }
  return symbolizeText(String(raw));
}

/**
 * Processes justification text by symbolizing rule names and preserving
 * line references. Handles comma-separated justifications.
 * 
 * @param {string} raw - Raw justification text
 * @returns {string} Processed justification text
 */
export function processJustification(raw) {
  const s = String(raw ?? '');
  const i = s.indexOf(',');
  const clean = (t) => t.replace(/\s+/g, '');
  
  // If no comma, just symbolize and clean
  if (i === -1) {
    return clean(symbolize(s));
  }
  
  // Split on comma: symbolize left part (rule), preserve right part (line refs)
  const left = clean(symbolize(s.slice(0, i)));
  const right = clean(s.slice(i + 1));
  return `${left}, ${right}`;
}

