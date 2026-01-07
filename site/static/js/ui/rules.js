/**
 * Rules page image sizing
 *
 * Dynamically sizes rule image wrappers to accommodate scaled SVG images.
 * Reads the scale factor from CSS custom property and adjusts wrapper dimensions
 * to prevent vertical scrolling while maintaining proper spacing.
 *
 * Dependencies: none
 */

function initRulesPage() {
  const root = getComputedStyle(document.documentElement);
  const scaleFactor = parseFloat(root.getPropertyValue('--rule-scale').trim()) || 1.4;
  
  const wrappers = document.querySelectorAll('.rule__img-wrapper');
  
  wrappers.forEach(function(wrapper) {
    const img = wrapper.querySelector('.rule__img');
    if (!img) return;
    
    if (img.complete) {
      sizeWrapper(wrapper, img, scaleFactor);
    } else {
      img.addEventListener('load', function() {
        sizeWrapper(wrapper, img, scaleFactor);
      });
    }
  });
  
  function sizeWrapper(wrapper, img, scale) {
    const naturalWidth = img.naturalWidth;
    const naturalHeight = img.naturalHeight;
    
    wrapper.style.width = Math.ceil(naturalWidth * scale) + 'px';
    wrapper.style.height = Math.ceil(naturalHeight * scale) + 1 + 'px';
    wrapper.style.flexShrink = '0';
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initRulesPage);
} else {
  initRulesPage();
}
