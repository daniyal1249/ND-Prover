/**
 * Text Measurement Utilities
 * 
 * Functions for measuring text width and reading CSS custom property values.
 * Uses a hidden DOM element for accurate text measurement.
 * 
 * Dependencies: None (but requires DOM to be available)
 */

// Create hidden measurer element for text width calculation
const measurer = document.createElement('span');
measurer.style.position = 'absolute';
measurer.style.visibility = 'hidden';
measurer.style.whiteSpace = 'pre';
document.body.appendChild(measurer);

/**
 * Measures the width of text using the current font settings.
 * 
 * @param {string} text - Text to measure
 * @returns {number} Width in pixels
 */
export function textWidth(text) {
  const root = getComputedStyle(document.documentElement);
  // Use math font for accurate measurement of mathematical symbols and text
  measurer.style.fontFamily = root.getPropertyValue('--math-font') || 'Noto Sans Math, sans-serif';
  measurer.style.fontSize = root.getPropertyValue('--font-size') || '16px';
  measurer.textContent = text || '';
  return measurer.offsetWidth;
}

/**
 * Reads a CSS custom property value and converts it to a number (pixels).
 * 
 * @param {string} name - CSS custom property name (e.g., '--proof-indent')
 * @returns {number} Numeric value in pixels, or 0 if invalid
 */
export function pxVar(name) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  if (v.endsWith('px')) {
    return parseFloat(v);
  }
  const n = parseFloat(v);
  return isNaN(n) ? 0 : n;
}

