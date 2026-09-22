/**
 * Samachar Spatial 3D & Living Environment Engine
 * 60fps hardware-accelerated pointer tilt, specular glare reflection,
 * and holographic multi-plane Z-axis parallax.
 */
(function () {
  'use strict';

  // Do not activate tilt on reduced-motion preference or coarse touch pointers
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isTouchDevice = window.matchMedia('(hover: none) and (pointer: coarse)').matches;

  class SpatialCardController {
    constructor(el, options = {}) {
      this.el = el;
      this.options = Object.assign({
        maxTilt: 7.5,           // degrees
        perspective: 1000,      // px
        scale: 1.02,           // hover scale
        speed: 400,            // transition speed ms
        easing: 'cubic-bezier(0.16, 1, 0.3, 1)',
        glare: true,
        maxGlare: 0.22
      }, options);

      this.width = null;
      this.height = null;
      this.left = null;
      this.top = null;
      this.targetX = 0;
      this.targetY = 0;
      this.currentX = 0;
      this.currentY = 0;
      this.rafId = null;
      this.isHovered = false;

      this.init();
    }

    init() {
      this.el.classList.add('card-3d-active');
      this.el.style.transformStyle = 'preserve-3d';
      this.el.style.willChange = 'transform';

      this.onMouseEnter = this.handleMouseEnter.bind(this);
      this.onMouseMove = this.handleMouseMove.bind(this);
      this.onMouseLeave = this.handleMouseLeave.bind(this);

      this.el.addEventListener('mouseenter', this.onMouseEnter, { passive: true });
      this.el.addEventListener('mousemove', this.onMouseMove, { passive: true });
      this.el.addEventListener('mouseleave', this.onMouseLeave, { passive: true });
    }

    updateDimensions() {
      const rect = this.el.getBoundingClientRect();
      this.width = rect.width;
      this.height = rect.height;
      this.left = rect.left + window.scrollX;
      this.top = rect.top + window.scrollY;
    }

    handleMouseEnter(e) {
      this.isHovered = true;
      this.updateDimensions();
      this.el.style.transition = 'none';
      if (!this.rafId) {
        this.rafId = requestAnimationFrame(() => this.render());
      }
    }

    handleMouseMove(e) {
      if (!this.width || !this.height) {
        this.updateDimensions();
      }

      this.el.style.transition = 'none';

      const clientX = e.clientX;
      const clientY = e.clientY;

      const rect = this.el.getBoundingClientRect();
      const x = Math.min(Math.max((clientX - rect.left) / rect.width, 0), 1);
      const y = Math.min(Math.max((clientY - rect.top) / rect.height, 0), 1);

      // Tilt angles: pointer up tilts up, pointer left tilts left
      this.targetY = (x - 0.5) * (this.options.maxTilt * 2);
      this.targetX = (0.5 - y) * (this.options.maxTilt * 2);

      // Compute specular glare coordinates
      if (this.options.glare) {
        const glareX = Math.round(x * 100);
        const glareY = Math.round(y * 100);
        this.el.style.setProperty('--glare-x', `${glareX}%`);
        this.el.style.setProperty('--glare-y', `${glareY}%`);
        this.el.style.setProperty('--glare-opacity', `${this.options.maxGlare}`);
      }

      if (!this.rafId) {
        this.rafId = requestAnimationFrame(() => this.render());
      }
    }

    handleMouseLeave() {
      this.isHovered = false;
      this.targetX = 0;
      this.targetY = 0;
      this.el.style.transition = `transform 0.45s cubic-bezier(0.16, 1, 0.3, 1)`;
      this.el.style.setProperty('--glare-opacity', '0');
      this.render();
    }

    render() {
      this.rafId = null;

      // Spring damping interpolation
      const factor = this.isHovered ? 0.2 : 0.15;
      this.currentX += (this.targetX - this.currentX) * factor;
      this.currentY += (this.targetY - this.currentY) * factor;

      const scale = this.isHovered ? this.options.scale : 1;
      this.el.style.transform = `perspective(${this.options.perspective}px) rotateX(${this.currentX.toFixed(2)}deg) rotateY(${this.currentY.toFixed(2)}deg) scale3d(${scale}, ${scale}, ${scale})`;

      // Continue animating until settled
      if (this.isHovered || Math.abs(this.targetX - this.currentX) > 0.05 || Math.abs(this.targetY - this.currentY) > 0.05) {
        this.rafId = requestAnimationFrame(() => this.render());
      } else {
        this.el.style.transform = `perspective(${this.options.perspective}px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
      }
    }

    destroy() {
      if (this.rafId) cancelAnimationFrame(this.rafId);
      this.el.removeEventListener('mouseenter', this.onMouseEnter);
      this.el.removeEventListener('mousemove', this.onMouseMove);
      this.el.removeEventListener('mouseleave', this.onMouseLeave);
      this.el.style.transform = '';
      this.el.classList.remove('card-3d-active');
    }
  }

  // Global registry and dynamic observer
  const activeControllers = new WeakMap();

  function initSpatialCards(root = document) {
    if (prefersReducedMotion || isTouchDevice) return;

    const selectors = [
      '.card-3d',
      '.bento-main',
      '.bento-side-card',
      '.hero-workbench-card',
      '.scorecard-banner',
      '.pillar-card'
    ];

    const elements = root.querySelectorAll(selectors.join(', '));
    elements.forEach(el => {
      if (!activeControllers.has(el)) {
        const controller = new SpatialCardController(el);
        activeControllers.set(el, controller);
      }
    });
  }

  // Living Telemetry Controller: Real-Time Wire Sync Countdown
  let telemetryInterval = null;
  function initLiveTelemetryStream() {
    const liveDisplays = document.querySelectorAll('.live-sync-countdown, #liveSyncCountdown');
    if (!liveDisplays.length) return;

    function updateCountdown() {
      const now = new Date();
      const minutes = now.getMinutes();
      const seconds = now.getSeconds();
      
      const nextSyncMin = minutes < 30 ? 30 : 60;
      const remSeconds = ((nextSyncMin - minutes) * 60) - seconds;
      
      const m = Math.floor(remSeconds / 60);
      const s = remSeconds % 60;
      const formatted = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

      liveDisplays.forEach(el => {
        el.textContent = formatted;
      });
    }

    updateCountdown();
    if (!telemetryInterval) {
      telemetryInterval = setInterval(updateCountdown, 1000);
    }
  }

  // Living Ambient 3D Particle Mesh (Subtle floating glowing depth stars)
  function initAmbientSpatialMesh() {
    if (prefersReducedMotion) return;
    if (document.getElementById('spatialAmbientLayer')) return;
    if (!document.body) return;

    const canvas = document.createElement('div');
    canvas.id = 'spatialAmbientLayer';
    canvas.className = 'spatial-ambient-layer';
    canvas.setAttribute('aria-hidden', 'true');
    canvas.innerHTML = `
      <div class="spatial-depth-orb orb-1"></div>
      <div class="spatial-depth-orb orb-2"></div>
      <div class="spatial-depth-orb orb-3"></div>
      <div class="spatial-grid-mesh"></div>
    `;

    document.body.prepend(canvas);
  }

  function startSpatialEngine() {
    initAmbientSpatialMesh();
    initSpatialCards();
    initLiveTelemetryStream();
  }

  // Auto-init on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startSpatialEngine);
  } else {
    startSpatialEngine();
  }

  // MutationObserver to auto-bind dynamically rendered cards
  const observer = new MutationObserver(mutations => {
    let shouldScan = false;
    for (const m of mutations) {
      if (m.addedNodes.length) {
        for (const n of m.addedNodes) {
          if (n.nodeType === 1 && !n.classList?.contains('spatial-ambient-layer')) {
            shouldScan = true;
            break;
          }
        }
      }
      if (shouldScan) break;
    }
    if (shouldScan) {
      initSpatialCards();
    }
  });

  const attachObserver = () => {
    if (document.body) {
      observer.observe(document.body, { childList: true, subtree: true });
    }
  };

  if (document.body) {
    attachObserver();
  } else {
    document.addEventListener('DOMContentLoaded', attachObserver);
  }

  // Expose API on window
  window.SamacharSpatial = {
    init: initSpatialCards,
    initTelemetry: initLiveTelemetryStream
  };
})();
