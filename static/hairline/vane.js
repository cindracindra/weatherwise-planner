/**
 * Vane: a weather vane on a chimney. The stack has a cap and two pots; the
 * mast rises from the taller pot, with four compass arms ending in balls, and
 * the vane on top is one thin plate: arrowhead, shaft and tail fin. The
 * pointer is projected onto the ground, which never moves, and its bearing
 * round the mast is the vane's target, on a spring. At rest it points
 * south-west, London's prevailing wind. The vane holds the bright stroke; the
 * arm nearest its bearing carries the medium dot. The slider is the vane's
 * weight, the spring's mass: heavier swings wider and settles later, and the
 * vane always ends pointing where the pointer is.
 *
 * The pattern: aim, as Dish and Router do. One spring on an angle, unwrapped
 * so it always takes the short way round.
 */
const {
  Cam, clamp, facing, fit, prism, proj, rings, unproj, spring, stepS,
  fillet, poly, seg, flatDot, mk, place, pointer, put, register, disposer, solid,
} = HL;

const MX = 7, MY = 9;                  // mast axis, over the tall pot
const Z_CAP = 24, Z_POT = 27, Z_ARMS = 58, Z_VANE = 80, ARM = 13, V = 1.3;
const REST = Math.atan2(1, -1);        // world angle of south-west: +y is south, -x is west
const NAMES = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
// North is -y, east +x, south +y, west -x.
const ARMS = [[0, -1], [1, 0], [0, 1], [-1, 0]];

/** The angle into (-π, π]. */
const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
/** Compass bearing in degrees, 0 = north, clockwise. */
const bearing = (a) => (Math.round((Math.atan2(Math.cos(a), -Math.sin(a)) * 180) / Math.PI) + 360) % 360;

// The vane's outline in its own plane: s along the arrow, h up from the pivot.
const OUTLINE = [
  [26, 0], [17, 6], [17, 1.1], [-15, 1.1], [-22, 9], [-30, 9], [-26, 0],
  [-30, -7], [-22, -7], [-15, -1.1], [17, -1.1], [17, -6],
];
const RADII = [0.4, 1, 0.6, 0.6, 1.4, 1.4, 1, 1.4, 1.4, 0.6, 0.6, 1];

function mount({ stage, svg, read }, value) {
  const bag = disposer();
  const C = Cam(45, 0.5, 2.45);
  const reach = 31 * V;
  fit(C, [
    [-2, -2, 0], [28, 20, 0], [28, -2, 0], [-2, 20, 0],
    [MX - reach, MY, Z_VANE + 9 * V], [MX + reach, MY, Z_VANE + 9 * V],
    [MX, MY - reach, Z_VANE - 7 * V], [MX, MY + reach, Z_VANE - 7 * V],
  ], 200, 170);
  const P = proj(C), front = facing(C);
  let over = null;

  const g = mk("g", {}, svg);
  const stand = (x0, y0, x1, y1, r, b, z0, z1) => {
    const [ring, inner] = rings(x0, y0, x1, y1, r, b);
    put(solid(g), prism(P, front, ring, inner, z0, z1));
  };
  // Back to front: stack, its cap, the far pot then the near one.
  stand(0, 0, 26, 18, 2, 1.2, 0, Z_CAP);
  stand(-2, -2, 28, 20, 2.4, 1.2, Z_CAP, Z_POT);
  stand(MX - 4.2, MY - 4.2, MX + 4.2, MY + 4.2, 4.2, 0.9, Z_POT, Z_POT + 11);
  stand(18 - 3.6, MY - 3.6, 18 + 3.6, MY + 3.6, 3.6, 0.9, Z_POT, Z_POT + 6);

  // Arms: the far two (north, west) go behind the mast, the near two in front.
  const balls = [];
  const arm = (k) => {
    const [ux, uy] = ARMS[k];
    mk("path", { d: seg(P(MX, MY, Z_ARMS), P(MX + ux * ARM, MY + uy * ARM, Z_ARMS)), class: "sil nf" }, g);
    const ball = flatDot(g, C, 0.9, "dot off");
    place(ball, P(MX + ux * ARM, MY + uy * ARM, Z_ARMS));
    balls[k] = ball;
  };
  arm(0); arm(3);
  stand(MX - 0.8, MY - 0.8, MX + 0.8, MY + 0.8, 0.8, 0.35, Z_POT + 11, Z_VANE);
  arm(1); arm(2);

  // The vane: a back face for the plate's thickness, then the front face.
  const back = mk("path", { class: "lo" }, g);
  const face = mk("path", { class: "sil hi" }, g);
  let ang = spring(REST, { m: value });
  let drawn = NaN, lit = -1;

  function outline(a, off) {
    const c = Math.cos(a), s = Math.sin(a);
    // Offset across the plate, toward or away from the viewer at +x +y.
    const nx = -s, ny = c, side = nx + ny > 0 ? 1 : -1;
    const ox = nx * side * off, oy = ny * side * off;
    const pts = OUTLINE.map(([u, h]) => P(MX + u * V * c + ox, MY + u * V * s + oy, Z_VANE + h * V));
    return poly(fillet(pts, RADII, 3));
  }
  function draw() {
    const a = ang.x;
    if (a === drawn) return;
    drawn = a;
    back.setAttribute("d", outline(a, -1));
    face.setAttribute("d", outline(a, 0.4));
    const k = ((Math.round(wrap(a + Math.PI / 2) / (Math.PI / 2)) % 4) + 4) % 4;
    if (k !== lit) {
      if (lit >= 0) balls[lit].setAttribute("class", "dot off");
      balls[k].setAttribute("class", "dot m");
      lit = k;
    }
  }

  const B = register(stage, (dt) => {
    const m = stepS(ang, dt);
    draw();
    return m;
  });
  bag.add(B.unregister);

  function retarget() {
    let want = REST;
    if (over) {
      const dx = over[0] - MX, dy = over[1] - MY;
      // Too close to the mast to give a bearing: keep the last target.
      if (Math.hypot(dx, dy) < 3) return;
      want = Math.atan2(dy, dx);
      const b = bearing(want);
      read.textContent = `${NAMES[Math.round(b / 45) % 8]} ${b}°`;
    } else read.textContent = "rest";
    // Take the short way round from where the target already is.
    ang.t = ang.t + wrap(want - ang.t);
    B.wake();
  }

  bag.add(pointer(stage, {
    move: (p) => { over = unproj(C, p[0], p[1], 0); retarget(); },
    leave: () => { over = null; retarget(); },
  }));
  bag.add(() => svg.replaceChildren());
  draw();

  return {
    set: (v) => {
      // A new mass keeps the vane where it is and where it is going.
      const next = spring(ang.x, { m: clamp(v, 0.5, 2) });
      next.t = ang.t;
      ang = next;
      B.wake();
    },
    destroy: bag.dispose,
  };
}

hairline({
  name: "vane",
  means: "A weather vane on a chimney swings round on a spring to point where the pointer is.",
  rules: [1, 4, 5, 8],
  range: [0.5, 1, 2],
  mount,
});
