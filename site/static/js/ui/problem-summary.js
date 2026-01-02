/**
 * Problem summary helpers
 *
 * Splits premises and renders the proof-pane summary line.
 * Uses DOM APIs + textContent (no innerHTML) to avoid XSS.
 */

/**
 * Split premises on commas/semicolons at top-level only.
 *
 * Example: "P(a,b), Q(c); R(d)" -> ["P(a,b)", "Q(c)", "R(d)"]
 *
 * @param {string} text
 * @returns {string[]}
 */
export function splitPremisesTopLevel(text) {
  const s = String(text ?? '');
  const parts = [];
  let depth = 0;
  let start = 0;

  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (ch === '(') {
      depth++;
      continue;
    }
    if (ch === ')') {
      depth = Math.max(0, depth - 1);
      continue;
    }
    if (depth === 0 && (ch === ',' || ch === ';')) {
      const part = s.slice(start, i).trim();
      if (part) {
        parts.push(part);
      }
      start = i + 1;
    }
  }

  const tail = s.slice(start).trim();
  if (tail) {
    parts.push(tail);
  }

  return parts;
}

/**
 * Builds the math-content string (premises + therefore + conclusion).
 *
 * @param {string} premisesText
 * @param {string} conclusionText
 * @returns {{ parts: string[], mathContent: string }}
 */
export function buildProblemMathContent(premisesText, conclusionText) {
  const parts = splitPremisesTopLevel(premisesText || '');
  const premStr = parts.join(', ');
  const conclStr = conclusionText || '';
  const divider = ' ∴ ';
  const mathContent = premStr ? (premStr + divider + conclStr) : (divider + conclStr);
  return { parts, mathContent };
}

/**
 * Renders the summary into the target element.
 *
 * @param {HTMLElement|null} container
 * @param {string} logicLabel
 * @param {string} premisesText
 * @param {string} conclusionText
 */
export function renderProblemSummary(container, logicLabel, premisesText, conclusionText) {
  if (!container) {
    return;
  }

  const { mathContent } = buildProblemMathContent(premisesText, conclusionText);

  container.textContent = '';

  const prefix = document.createTextNode(`Prove the following argument in ${logicLabel}:  `);
  const mathSpan = document.createElement('span');
  mathSpan.className = 'math-content';
  mathSpan.textContent = mathContent;

  container.append(prefix, mathSpan);
}
