/*
 * Mounts a Hairline figure (static/hairline/<name>.js) into the element
 * marked data-hairline-host="<name>", the way the hairline bench does: an svg
 * in a 400 x 320 viewBox, a read-out sink, and the figure's middle intensity.
 * The kernel (kernel.js) is the hairline package's, unchanged.
 */
(() => {
  window.hairline = (figure) => {
    const stage = document.querySelector(`[data-hairline-host="${figure.name}"]`);
    if (!stage || !window.HL) return;
    const out = document.querySelector(`[data-hairline-read="${figure.name}"]`);

    HL.inject(document);
    stage.setAttribute("data-hairline", figure.name);
    stage.setAttribute("role", "img");
    stage.setAttribute("aria-label", figure.means);
    const svg = HL.mk("svg", { viewBox: "0 0 400 320", "aria-hidden": "true" }, stage);

    let text = "";
    const read = {
      get textContent() { return text; },
      set textContent(value) {
        text = value == null ? "" : String(value);
        if (out) out.textContent = text === "rest" ? "" : text;
      },
    };
    figure.mount({ stage, svg, read }, figure.range[1]);
  };
})();
