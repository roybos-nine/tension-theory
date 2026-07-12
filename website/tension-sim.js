/* <tension-sim> — live local-update tension graph.
   Nodes carry a scalar state; edges carry tension = |Δstate|.
   Each tick: random local updates move states toward neighbors (cost > 0),
   edges glow with tension. Purely local, discrete, irreversible-ish. */
(function () {
  class TensionSim extends HTMLElement {
    connectedCallback() {
      if (this._started) return;
      this._started = true;
      this.style.display = 'block';
      const canvas = document.createElement('canvas');
      canvas.style.cssText = 'width:100%;height:100%;display:block;';
      this.appendChild(canvas);
      this._canvas = canvas;
      this._ctx = canvas.getContext('2d');
      this._accent = this.getAttribute('accent') || '#ff5c33';
      this._density = parseFloat(this.getAttribute('density') || '1');
      this._resize = this._resize.bind(this);
      window.addEventListener('resize', this._resize);
      this._resize();
      this._init();
      this._raf = requestAnimationFrame(this._tick.bind(this));
    }
    disconnectedCallback() {
      cancelAnimationFrame(this._raf);
      window.removeEventListener('resize', this._resize);
      this._started = false;
      if (this._canvas) this._canvas.remove();
    }
    _resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const r = this.getBoundingClientRect();
      this._w = Math.max(r.width, 10);
      this._h = Math.max(r.height, 10);
      this._canvas.width = this._w * dpr;
      this._canvas.height = this._h * dpr;
      this._ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (this._nodes) this._init();
    }
    _init() {
      const area = this._w * this._h;
      const n = Math.round(Math.min(140, Math.max(40, (area / 16000))) * this._density);
      const nodes = [];
      for (let i = 0; i < n; i++) {
        nodes.push({
          x: Math.random() * this._w,
          y: Math.random() * this._h,
          vx: (Math.random() - 0.5) * 0.15,
          vy: (Math.random() - 0.5) * 0.15,
          s: Math.random(),           // local state
          pulse: 0,
        });
      }
      // edges: connect near neighbors (relational, not metric — but we fake locality with distance)
      const edges = [];
      const maxD = Math.max(90, Math.sqrt(area / n) * 1.6);
      for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
          const dx = nodes[i].x - nodes[j].x, dy = nodes[i].y - nodes[j].y;
          if (dx * dx + dy * dy < maxD * maxD) edges.push([i, j]);
        }
      }
      this._nodes = nodes;
      this._edges = edges;
      this._maxD = maxD;
    }
    _tick(t) {
      this._raf = requestAnimationFrame(this._tick.bind(this));
      const { _nodes: nodes, _edges: edges, _ctx: ctx } = this;
      // discrete local updates: a few random nodes relax toward neighbor mean
      for (let u = 0; u < Math.max(2, nodes.length * 0.06); u++) {
        const i = (Math.random() * nodes.length) | 0;
        let sum = 0, cnt = 0;
        for (const [a, b] of edges) {
          if (a === i) { sum += nodes[b].s; cnt++; }
          else if (b === i) { sum += nodes[a].s; cnt++; }
        }
        if (cnt) {
          const target = sum / cnt;
          const d = target - nodes[i].s;
          nodes[i].s += d * 0.35;            // constrained update
          nodes[i].s += (Math.random() - 0.5) * 0.02; // memory noise (irreversibility)
          nodes[i].pulse = Math.min(1, Math.abs(d) * 3 + 0.15);
        }
      }
      // occasional tension injection — keeps the system from dying
      if (Math.random() < 0.03) {
        const i = (Math.random() * nodes.length) | 0;
        nodes[i].s = Math.random();
        nodes[i].pulse = 1;
      }
      // slow drift
      for (const nd of nodes) {
        nd.x += nd.vx; nd.y += nd.vy;
        if (nd.x < 0 || nd.x > this._w) nd.vx *= -1;
        if (nd.y < 0 || nd.y > this._h) nd.vy *= -1;
        nd.pulse *= 0.96;
      }
      // draw
      ctx.clearRect(0, 0, this._w, this._h);
      const accent = this._accent;
      for (const [a, b] of edges) {
        const na = nodes[a], nb = nodes[b];
        const tension = Math.abs(na.s - nb.s); // edge tension
        const alpha = Math.min(0.85, 0.05 + tension * 1.4);
        ctx.strokeStyle = tension > 0.12 ? accent : 'rgba(255,255,255,0.85)';
        ctx.globalAlpha = tension > 0.12 ? alpha : 0.06;
        ctx.lineWidth = tension > 0.12 ? 1.2 : 0.7;
        ctx.beginPath();
        ctx.moveTo(na.x, na.y);
        ctx.lineTo(nb.x, nb.y);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
      for (const nd of nodes) {
        const r = 1.4 + nd.pulse * 2.6;
        ctx.fillStyle = nd.pulse > 0.3 ? accent : 'rgba(255,255,255,0.55)';
        ctx.beginPath();
        ctx.arc(nd.x, nd.y, r, 0, Math.PI * 2);
        ctx.fill();
        if (nd.pulse > 0.5) {
          ctx.strokeStyle = accent;
          ctx.globalAlpha = nd.pulse * 0.35;
          ctx.beginPath();
          ctx.arc(nd.x, nd.y, r + 5 * nd.pulse, 0, Math.PI * 2);
          ctx.stroke();
          ctx.globalAlpha = 1;
        }
      }
    }
  }
  if (!customElements.get('tension-sim')) customElements.define('tension-sim', TensionSim);
})();
