/**
 * Logic mapping helpers
 *
 * Keeps base-logic + "first-order" checkbox mapping consistent across the UI
 * and any persistence layers (e.g., URL state).
 */

/**
 * Maps a base logic to its first-order version if the checkbox is checked.
 *
 * @param {string} baseLogic - Base logic value (TFL, MLK, MLT, MLS4, MLS5)
 * @param {boolean} isFirstOrder - Whether first-order checkbox is checked
 * @returns {string} Logic label to store in state.problemDraft.logic 
 *   (or the committed proof problem)
 */
export function getLogicValue(baseLogic, isFirstOrder) {
  if (!isFirstOrder) {
    return baseLogic;
  }

  const firstOrderMap = {
    'TFL': 'FOL',
    'MLK': 'FOMLK',
    'MLT': 'FOMLT',
    'MLS4': 'FOMLS4',
    'MLS5': 'FOMLS5'
  };

  return firstOrderMap[baseLogic] || baseLogic;
}

/**
 * Inverse of getLogicValue(): determines which base logic and checkbox setting
 * should be shown in the UI for a stored logic label.
 *
 * @param {string} logicLabel - Stored logic label (e.g., TFL, FOL, FOMLK)
 * @returns {{ baseLogic: string, isFirstOrder: boolean }}
 */
export function splitLogicValue(logicLabel) {
  const label = String(logicLabel || '');

  const inverse = {
    'FOL': { baseLogic: 'TFL', isFirstOrder: true },
    'FOMLK': { baseLogic: 'MLK', isFirstOrder: true },
    'FOMLT': { baseLogic: 'MLT', isFirstOrder: true },
    'FOMLS4': { baseLogic: 'MLS4', isFirstOrder: true },
    'FOMLS5': { baseLogic: 'MLS5', isFirstOrder: true }
  };

  if (inverse[label]) {
    return inverse[label];
  }

  return { baseLogic: label || 'TFL', isFirstOrder: false };
}
