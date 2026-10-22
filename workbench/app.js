/* B-CAD local workbench. Exact geometry comes from the local API; this canvas
 * only displays the returned tessellation. It never supplies CAD measurements. */
"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));
  const fields = {
    width: ["Width", "X"], depth: ["Depth", "Y"], height: ["Height", "Z"],
    diameter: ["Diameter", "Ø"], hole_diameter: ["Hole diameter", "Ø"],
  };
  const kinds = {
    box: { label: "Box", heading: "A solid beginning", icon: "cube", keys: ["width", "depth", "height"] },
    plate: { label: "Drilled plate", heading: "Form meets function", icon: "plate", keys: ["width", "depth", "height", "hole_diameter"] },
    cylinder: { label: "Cylinder", heading: "A different perspective", icon: "cylinder", keys: ["diameter", "height"] },
    imported: { label: "Imported solid", heading: "Bring your ideas in", icon: "upload", keys: [] },
  };
  const significant = new Intl.NumberFormat("en-US", { maximumSignificantDigits: 7 });
  const concise = new Intl.NumberFormat("en-US", { maximumSignificantDigits: 6 });
  const fmt = (value) => typeof value === "number" && Number.isFinite(value) ? significant.format(value) : "—";
  const fmtShort = (value) => typeof value === "number" && Number.isFinite(value) ? concise.format(value) : "—";
  const clone = (value) => JSON.parse(JSON.stringify(value));
  const icon = (name, className = "") => {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    if (className) svg.setAttribute("class", className);
    svg.setAttribute("aria-hidden", "true");
    const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
    use.setAttribute("href", `#i-${name}`);
    svg.append(use);
    return svg;
  };

  let token = "";
  let committed = null;
  let displayed = null;
  let draft = {};
  let draftKind = "box";
  let pending = false;
  let previewing = false;
  let stale = false;
  let savedFingerprint = "";
  let kernelAvailable = false;
  let responseSequence = 0;
  let lastError = null;
  let commandIndex = 0;
  let visibleCommands = [];

  function fingerprint(state = committed) { return state?.document ? JSON.stringify(state.document) : ""; }
  function isDirty() {
    return !!committed && (draftKind !== committed.document.part.kind ||
      JSON.stringify(draft) !== JSON.stringify(committed.document.part.parameters || {}));
  }
  function hasUnsavedChanges() { return isDirty() || fingerprint() !== savedFingerprint; }
  function normalizeState(value) {
    const state = value?.state || value;
    if (!state?.document?.part) throw new Error("The local server returned an incomplete document.");
    return state;
  }
  function status(message) { $("status-message").textContent = message; }
  function setBusy(busy) {
    pending = busy;
    document.body.classList.toggle("busy", busy);
    $("parameter-form").setAttribute("aria-busy", String(busy));
    updateControls();
  }
  function updateControls() {
    const dirty = isDirty();
    $$('[data-idle]').forEach((button) => { button.disabled = pending || !kernelAvailable; });
    $("undo-button").disabled = pending || !committed?.history?.can_undo;
    $("redo-button").disabled = pending || !committed?.history?.can_redo;
    $("save-button").disabled = pending || !committed || dirty || previewing;
    $("export-button").disabled = pending || !committed?.result || dirty || previewing || stale;
    $("preview-button").disabled = pending || !kernelAvailable || !dirty || !kinds[draftKind]?.keys.length;
    $("apply-button").disabled = pending || !kernelAvailable || !dirty || !kinds[draftKind]?.keys.length;
    $("cancel-button").disabled = pending;
    $("cancel-button").hidden = !dirty && !previewing && !stale;
    $("new-button").disabled = pending || !kernelAvailable;
    $("open-button").disabled = pending || !kernelAvailable;
    $("parameter-fields").querySelectorAll("input").forEach((input) => { input.disabled = pending; });
    $("edit-state").classList.toggle("dirty", dirty);
    $("edit-state-label").textContent = dirty ? (previewing ? "Preview · changes not yet applied" : "Unapplied parameter changes") : "All changes applied";
    $("document-dot").classList.toggle("saved", !hasUnsavedChanges());
    $("document-dot").title = hasUnsavedChanges() ? "Project has unsaved changes" : "No unsaved changes";
    $("save-button").title = dirty || previewing ? "Apply or discard parameter changes before saving" : "Save editable B-CAD project (Ctrl+S)";
    $("export-button").title = dirty || previewing ? "Apply or discard parameter changes before exporting" : "Export the committed solid";
  }

  async function api(path, payload) {
    const request = { method: payload === undefined ? "GET" : "POST", cache: "no-store", credentials: "same-origin", headers: { "X-BCAD-Token": token } };
    if (payload !== undefined) {
      request.headers["Content-Type"] = "application/json";
      request.body = JSON.stringify(payload);
    }
    const response = await fetch(`/api/${path}`, request);
    let data;
    try { data = await response.json(); } catch { throw new Error("The local server did not return a readable response. Check the server terminal."); }
    if (!response.ok) {
      const error = new Error(data?.error?.message || `The request failed (${response.status}).`);
      error.code = data?.error?.code;
      error.field = data?.error?.field;
      throw error;
    }
    return data;
  }
  async function perform(action, message, successMessage) {
    if (pending) return false;
    const sequence = ++responseSequence;
    setBusy(true);
    status(message);
    try {
      await action(sequence);
      if (successMessage) status(successMessage);
      return true;
    } catch (error) {
      if (sequence === responseSequence) showError(error);
      return false;
    } finally { if (sequence === responseSequence) setBusy(false); }
  }
  function clearError() {
    lastError = null;
    $("error-card").hidden = true;
    $$(".field-error").forEach((element) => element.remove());
    $$("#parameter-fields input").forEach((input) => input.removeAttribute("aria-invalid"));
  }
  function showError(error, geometryError = true) {
    lastError = error;
    $("error-title").textContent = error.code === "KERNEL_UNAVAILABLE" ? "Geometry engine unavailable" : "This action could not finish";
    $("error-message").textContent = error.message || "An unexpected error occurred. Check the local server terminal.";
    $("error-card").hidden = false;
    const fieldName = String(error.field || "").split(".").pop();
    const input = $("parameter-fields").querySelector(`input[name="${Object.hasOwn(fields, fieldName) ? fieldName : "_"}"]`);
    if (input) {
      input.setAttribute("aria-invalid", "true");
      const note = document.createElement("p");
      note.className = "field-error";
      note.textContent = error.message;
      note.id = `error-${fieldName}`;
      input.setAttribute("aria-describedby", note.id);
      input.closest(".parameter-field").append(note);
    }
    if (geometryError && displayed?.result) stale = true;
    status(error.message || "The action failed");
    renderBadges();
    updateControls();
  }
  function renderBadges() {
    const badge = $("geometry-badge");
    badge.classList.toggle("preview", previewing && !stale);
    badge.classList.toggle("error", stale || !kernelAvailable);
    $("geometry-badge-text").textContent = stale ? "Last valid geometry" : previewing ? "Unapplied preview" : displayed?.result ? "Exact solid" : kernelAvailable ? "Ready to create" : "Engine unavailable";
    const notice = $("viewport-notice");
    notice.hidden = !stale && !previewing;
    notice.classList.toggle("error", stale);
    $("viewport-notice-text").textContent = stale ? "The latest action failed. This is the last valid geometry; discard changes to return to the committed part." : "Preview only. Apply these dimensions to update your project.";
    $("measurements-title").textContent = stale ? "LAST VALID MEASUREMENTS" : previewing ? "PREVIEW MEASUREMENTS" : "EXACT MEASUREMENTS";
  }
  function acceptState(raw, { preview = false, resetView = false } = {}) {
    const state = normalizeState(raw);
    if (!preview && committed && state.document.document_id === committed.document.document_id &&
        Number(state.document.revision) < Number(committed.document.revision) && !resetView) {
      throw new Error("An older document revision was rejected. Reload the workbench to reconnect.");
    }
    clearError();
    stale = false;
    previewing = preview;
    displayed = state;
    if (!preview) {
      committed = state;
      draftKind = state.document.part.kind;
      draft = clone(state.document.part.parameters || {});
      renderFields();
    }
    renderState(state);
    viewer.setMesh(state.result?.mesh, state.result?.metrics, state.document.part.kind, resetView);
    renderBadges();
    updateControls();
  }
  function renderFields() {
    const container = $("parameter-fields");
    container.replaceChildren();
    const kind = kinds[draftKind] || kinds.imported;
    const keys = kind.keys;
    keys.forEach((key) => {
      const field = document.createElement("div");
      field.className = "parameter-field";
      const label = document.createElement("label");
      label.htmlFor = `parameter-${key}`;
      label.append(document.createTextNode(fields[key][0]));
      const variable = document.createElement("span");
      variable.textContent = key;
      label.append(variable);
      const wrap = document.createElement("div");
      wrap.className = "input-wrap";
      const input = document.createElement("input");
      input.id = `parameter-${key}`;
      input.name = key;
      input.type = "text";
      input.spellcheck = false;
      input.value = draft[key] ?? "";
      input.setAttribute("aria-label", `${fields[key][0]} expression, defaults to millimeters`);
      input.addEventListener("input", () => {
        draft[key] = input.value;
        input.removeAttribute("aria-invalid");
        input.removeAttribute("aria-describedby");
        field.querySelector(".field-error")?.remove();
        if (previewing) {
          $("viewport-notice-text").textContent = "Parameters have changed since this preview. Preview again or apply to recompute.";
          $("geometry-badge-text").textContent = "Previous preview";
        }
        updateControls();
      });
      const suffix = document.createElement("span");
      suffix.className = "input-suffix";
      suffix.textContent = fields[key][1];
      wrap.append(input, suffix);
      field.append(label, wrap);
      container.append(field);
    });
    if (!keys.length) {
      const note = document.createElement("div");
      note.className = "read-only-note";
      const title = document.createElement("strong");
      title.textContent = "Exact imported geometry";
      note.append(title, document.createTextNode("The STEP solid keeps its geometry. Its original feature history and dimensions are not editable here."));
      container.append(note);
    }
    $("expression-tip").hidden = !keys.length;
    $("edit-state").hidden = !keys.length;
    $("preview-button").parentElement.hidden = !keys.length;
  }
  function renderState(state) {
    const doc = state.document;
    const kind = kinds[doc.part.kind] || kinds.imported;
    const result = state.result;
    const metrics = result?.metrics || {};
    $("project-title").textContent = doc.name || kind.label;
    $("tree-project-name").textContent = doc.name || kind.label;
    $("revision-label").textContent = `r${doc.revision ?? 0}`;
    $("tree-body-name").textContent = kind.label;
    $("tree-solid-count").textContent = metrics.solid_count ?? "—";
    $("tree-body-icon").querySelector("use").setAttribute("href", `#i-${kind.icon}`);
    $("inspector-kind-icon").querySelector("use").setAttribute("href", `#i-${kind.icon}`);
    $("part-heading").replaceChildren(document.createTextNode(kind.heading));
    const dot = document.createElement("span"); dot.className = "part-heading-dot"; dot.textContent = "."; $("part-heading").append(dot);
    $("inspector-title").textContent = kind.label;
    $("inspector-subtitle").textContent = doc.part.kind === "imported" ? "STEP base geometry" : "Parametric solid";
    document.querySelector(".featurebar-note").textContent = doc.part.kind === "imported" ? "Imported STEP geometry" : "One parametric part";
    $$('[data-kind]').forEach((button) => button.classList.toggle("is-current", button.dataset.kind === doc.part.kind));
    $("metric-volume").textContent = fmt(metrics.volume_mm3);
    $("metric-area").textContent = fmt(metrics.area_mm2);
    ["x", "y", "z"].forEach((axis) => { $(`metric-${axis}`).textContent = fmt(metrics.bounds_mm?.[axis]); });
    ["solids", "faces", "edges"].forEach((type) => { $(`metric-${type}`).textContent = fmt(metrics[`${type.slice(0, -1)}_count`]); });
    $("validity-label").textContent = result ? (metrics.valid ? "Valid solid geometry" : "Geometry validity check failed") : "Awaiting geometry";
    $("validity-row").classList.toggle("invalid", !!result && !metrics.valid);
    renderFeatures(result?.features || [], kind);
    $("empty-state").hidden = !!result?.mesh?.vertices?.length;
    const kernel = result?.kernel;
    if (kernel) {
      $("engine-status").textContent = `${kernel.name || "OCCT"}${kernel.version ? ` ${kernel.version}` : ""} · exact geometry`;
      $("engine-indicator").classList.add("connected");
      $("engine-indicator").classList.remove("error");
    }
    const triangleCount = result?.mesh?.triangles?.length || 0;
    $("mesh-status").textContent = triangleCount ? `${significant.format(triangleCount)} TRIANGLES` : "NO MESH";
  }
  function renderFeatures(features, kind) {
    $("tree-features").replaceChildren();
    $("feature-strip").replaceChildren();
    if (!features.length) {
      const empty = document.createElement("span"); empty.className = "feature-empty"; empty.textContent = "No evaluated features"; $("feature-strip").append(empty);
    }
    features.forEach((feature, index) => {
      const type = String(feature.type || "");
      const featureIcon = /hole|cut/i.test(type) ? "plate" : /cylinder/i.test(type) ? "cylinder" : /import/i.test(type) ? "upload" : kind.icon;
      const row = document.createElement("div"); row.className = "tree-feature-row";
      const treeLabel = document.createElement("span"); treeLabel.textContent = feature.label || type || "Feature"; treeLabel.title = treeLabel.textContent;
      row.append(icon(featureIcon), treeLabel);
      $("tree-features").append(row);
      if (index) { const connector = document.createElement("span"); connector.className = "feature-connector"; $("feature-strip").append(connector); }
      const chip = document.createElement("div"); chip.className = "feature-chip";
      const text = document.createElement("span"); text.append(document.createTextNode(feature.label || type || "Feature"));
      const small = document.createElement("small"); small.textContent = `${String(index + 1).padStart(2, "0")} / ${type.replaceAll("_", " ").toUpperCase() || "FEATURE"}`; text.append(small);
      chip.append(icon(featureIcon), text);
      $("feature-strip").append(chip);
    });
  }

  function payload() { return { kind: draftKind, parameters: { ...draft } }; }
  function preview() {
    if (!isDirty() || !kernelAvailable) return;
    perform(async () => acceptState(await api("preview", payload()), { preview: true }), "Computing exact preview…", "Preview ready · apply to keep these dimensions");
  }
  function apply() {
    if (!isDirty() || !kernelAvailable) return;
    perform(async () => acceptState(await api("commit", payload())), "Recomputing the solid…", "Dimensions applied · save your project to keep them");
  }
  function discard() {
    if (pending || !committed) return;
    acceptState(committed);
    status("Restored the committed part");
  }
  function confirmDiscard() { return !hasUnsavedChanges() || window.confirm("This project has unsaved changes. Replace it and discard those changes?"); }
  function newPart(kind = "box") {
    if (pending || !kernelAvailable || !confirmDiscard()) return;
    perform(async () => {
      acceptState(await api("new", { kind }), { resetView: true });
      savedFingerprint = "";
      updateControls();
    }, "Creating a new part…", "New part ready · edit its dimensions in the inspector");
  }
  function history(direction) {
    if (pending || !committed?.history?.[`can_${direction}`]) return;
    if (isDirty() && !window.confirm("Discard the unapplied parameter changes and move through project history?")) return;
    perform(async () => acceptState(await api(direction, {}), { resetView: true }), `${direction === "undo" ? "Undoing" : "Redoing"} the last change…`, direction === "undo" ? "Previous revision restored" : "Change restored");
  }
  function safeName(name) { return (String(name || "B-CAD-part").replace(/[^a-zA-Z0-9._ -]/g, "_").slice(0, 100) || "B-CAD-part").replace(/\.(bcad|json|step|stp|stl)$/i, ""); }
  function download(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a"); link.href = url; link.download = filename; document.body.append(link); link.click(); link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 30000);
  }
  function saveProject() {
    if (pending || !committed || isDirty() || previewing) { if (isDirty() || previewing) status("Apply or discard parameter changes before saving"); return; }
    download(new Blob([JSON.stringify(committed.document, null, 2) + "\n"], { type: "application/json" }), `${safeName(committed.document.name)}.bcad`);
    savedFingerprint = fingerprint(); updateControls(); status("Editable .bcad project downloaded");
  }
  function exportSolid(format) {
    if (pending || !committed?.result || isDirty() || previewing || stale) return;
    closeExport();
    perform(async () => {
      const data = await api("export", { format });
      if (typeof data.data_base64 !== "string") throw new Error("The export response did not include a file.");
      const binary = atob(data.data_base64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      download(new Blob([bytes], { type: data.mime || "application/octet-stream" }), data.filename || `${safeName(committed.document.name)}.${format}`);
    }, `Preparing ${format.toUpperCase()} export…`, `${format.toUpperCase()} exported${format === "stl" ? " · mesh coordinates are in millimeters" : " · exact CAD geometry"}`);
  }
  async function openProject(file) {
    if (!file || pending) return;
    if (file.size > 15 * 1024 * 1024) { showError(new Error("This project is too large. B-CAD projects can be at most 15 MiB, including embedded STEP geometry."), false); return; }
    let doc;
    try { doc = JSON.parse(await file.text()); } catch { showError(new Error("This file is not a readable B-CAD JSON document. The current project has been preserved."), false); return; }
    if (!confirmDiscard()) return;
    perform(async () => {
      acceptState(await api("load", { document: doc }), { resetView: true });
      savedFingerprint = fingerprint(); updateControls();
    }, "Opening the project and rebuilding geometry…", "Project opened · exact geometry rebuilt");
  }
  async function importStep(file) {
    if (!file || pending) return;
    if (file.size > 10 * 1024 * 1024) { showError(new Error("This STEP file is too large. The experimental workbench accepts STEP files up to 10 MiB."), false); return; }
    if (!confirmDiscard()) return;
    perform(async () => {
      const bytes = new Uint8Array(await file.arrayBuffer());
      let binary = "";
      for (let i = 0; i < bytes.length; i += 8192) binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
      acceptState(await api("import-step", { data_base64: btoa(binary), filename: file.name }), { resetView: true });
      savedFingerprint = ""; updateControls();
    }, "Reading STEP geometry…", "STEP imported · original feature history is not editable");
  }
  function closeExport() { $("export-menu").hidden = true; $("export-button").setAttribute("aria-expanded", "false"); }

  // Dependency-free 3D display. World coordinates are millimeters; the mesh and
  // its apparent precision are never used as an engineering measurement source.
  function makeViewer() {
    const canvas = $("viewport");
    const context = canvas.getContext("2d", { alpha: true });
    const axisContext = $("axis-canvas").getContext("2d");
    let width = 1, height = 1, pixelRatio = 1;
    let vertices = [], triangles = [], metrics = {}, kind = "box";
    let minimum = [-40, -25, 0], maximum = [40, 25, 8], center = [0, 0, 4], radius = 50;
    let yaw = -0.62, pitch = 0.48, zoom = 1, panX = 0, panY = 0;
    let grid = true, dimensions = true, perspective = false, currentView = "iso";
    let requested = false, pointer = null;
    const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    const subtract = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
    const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    const normalize = (v) => { const length = Math.hypot(...v) || 1; return v.map((x) => x / length); };
    let right, up, direction, scale;
    function axes() {
      direction = [Math.cos(pitch) * Math.sin(yaw), -Math.cos(pitch) * Math.cos(yaw), Math.sin(pitch)];
      right = [Math.cos(yaw), Math.sin(yaw), 0];
      up = cross(direction, right);
      scale = Math.min(width, height) * 0.74 / (Math.max(radius, 0.001) * 2) * zoom;
    }
    function project(point) {
      const v = subtract(point, center);
      const z = dot(v, direction);
      const factor = perspective ? radius * 4.5 / (radius * 4.5 - z) : 1;
      return [width / 2 + panX + dot(v, right) * scale * factor, height / 2 + panY - dot(v, up) * scale * factor, z];
    }
    function line(a, b, color, lineWidth = 1, dash = []) {
      const p = project(a), q = project(b);
      context.beginPath(); context.moveTo(p[0], p[1]); context.lineTo(q[0], q[1]); context.strokeStyle = color; context.lineWidth = lineWidth; context.setLineDash(dash); context.stroke(); context.setLineDash([]);
    }
    function drawGrid() {
      if (!grid) return;
      const targetStep = radius / 5;
      const magnitude = 10 ** Math.floor(Math.log10(Math.max(targetStep, 0.00001)));
      const step = [1, 2, 5, 10].map((n) => n * magnitude).find((n) => n >= targetStep) || magnitude * 10;
      const extent = step * 16;
      const gx = Math.round(center[0] / step) * step, gy = Math.round(center[1] / step) * step;
      const z = minimum[2] - radius * 0.003;
      for (let i = -16; i <= 16; i++) {
        const x = gx + i * step, y = gy + i * step;
        const alpha = (0.115 * (1 - Math.abs(i) / 23)).toFixed(3);
        line([x, gy - extent, z], [x, gy + extent, z], `rgba(119,164,152,${alpha})`, 0.65);
        line([gx - extent, y, z], [gx + extent, y, z], `rgba(119,164,152,${alpha})`, 0.65);
      }
      if (Math.abs(center[1]) < extent) line([gx - extent, 0, z], [gx + extent, 0, z], "rgba(189,128,104,.26)", 0.8);
      if (Math.abs(center[0]) < extent) line([0, gy - extent, z], [0, gy + extent, z], "rgba(113,163,127,.28)", 0.8);
    }
    function drawShadow() {
      if (!vertices.length) return;
      const p = project([center[0], center[1], minimum[2] - radius * .004]);
      context.save(); context.translate(p[0], p[1] + scale * radius * .035);
      context.scale(1, .34); const r = radius * scale * 1.08;
      const gradient = context.createRadialGradient(0, 0, 0, 0, 0, r);
      gradient.addColorStop(0, "rgba(8,15,14,.34)"); gradient.addColorStop(.5, "rgba(8,15,14,.16)"); gradient.addColorStop(1, "rgba(8,15,14,0)");
      context.fillStyle = gradient; context.beginPath(); context.arc(0, 0, r, 0, Math.PI * 2); context.fill(); context.restore();
    }
    function drawModel() {
      const projected = vertices.map(project);
      const light = [-.35, -.45, .82];
      const order = triangles.map((tri) => ({ tri, depth: (projected[tri.ids[0]][2] + projected[tri.ids[1]][2] + projected[tri.ids[2]][2]) / 3 }));
      order.sort((a, b) => a.depth - b.depth);
      for (const item of order) {
        const tri = item.tri, p = tri.ids.map((index) => projected[index]);
        // The worker returns consistently oriented, closed solids. Omit the
        // back-facing surface so long bottom-face triangles cannot paint over
        // a top face merely because their centroids sort closer to the camera.
        let facing = dot(tri.normal, direction);
        if (perspective) {
          const triangleCenter = [0, 1, 2].map((axis) => (vertices[tri.ids[0]][axis] + vertices[tri.ids[1]][axis] + vertices[tri.ids[2]][axis]) / 3);
          const toCamera = center.map((value, axis) => value + direction[axis] * radius * 4.5 - triangleCenter[axis]);
          facing = dot(tri.normal, toCamera);
        }
        if (facing <= 1e-10) continue;
        if (Math.max(p[0][0], p[1][0], p[2][0]) < -10 || Math.min(p[0][0], p[1][0], p[2][0]) > width + 10 || Math.max(p[0][1], p[1][1], p[2][1]) < -10 || Math.min(p[0][1], p[1][1], p[2][1]) > height + 10) continue;
        const faceLight = .47 + .44 * Math.max(0, dot(tri.normal, light)) + .1 * Math.abs(dot(tri.normal, direction));
        const color = `rgb(${Math.round(170 * faceLight)},${Math.round(189 * faceLight)},${Math.round(182 * faceLight)})`;
        context.beginPath(); context.moveTo(p[0][0], p[0][1]); context.lineTo(p[1][0], p[1][1]); context.lineTo(p[2][0], p[2][1]); context.closePath();
        context.fillStyle = color; context.fill(); context.strokeStyle = color; context.lineWidth = .45; context.stroke();
        context.beginPath();
        for (let edge = 0; edge < 3; edge++) if (tri.sharp[edge]) { context.moveTo(p[edge][0], p[edge][1]); context.lineTo(p[(edge + 1) % 3][0], p[(edge + 1) % 3][1]); }
        context.strokeStyle = "rgba(237,194,127,.72)"; context.lineWidth = .85; context.stroke();
      }
    }
    function dimension(a, b, anchorA, anchorB, label) {
      const p = project(a), q = project(b);
      if (Math.hypot(p[0] - q[0], p[1] - q[1]) < 17) return;
      line(anchorA, a, "rgba(147,190,168,.26)", .7, [3, 4]); line(anchorB, b, "rgba(147,190,168,.26)", .7, [3, 4]);
      line(a, b, "rgba(146,191,168,.58)", .75);
      context.strokeStyle = "#92b9a2"; context.lineWidth = 1;
      for (const point of [p, q]) { context.beginPath(); context.moveTo(point[0] - 3, point[1] + 4); context.lineTo(point[0] + 3, point[1] - 4); context.stroke(); }
      const x = (p[0] + q[0]) / 2, y = (p[1] + q[1]) / 2;
      context.font = "9px 'Cascadia Code', Consolas, monospace";
      const labelWidth = context.measureText(label).width + 16;
      context.fillStyle = "rgba(29,45,40,.97)"; context.strokeStyle = "rgba(104,143,116,.65)"; context.lineWidth = .6;
      context.beginPath(); context.roundRect(x - labelWidth / 2, y - 11, labelWidth, 22, 4); context.fill(); context.stroke();
      context.fillStyle = "#bdd4b8"; context.textAlign = "center"; context.textBaseline = "middle"; context.fillText(label, x, y + .5);
    }
    function drawDimensions() {
      if (!dimensions || !vertices.length || !metrics.bounds_mm) return;
      const [x0, y0, z0] = minimum, [x1, y1, z1] = maximum;
      const offset = radius * .32;
      dimension([x0, y0 - offset, z0], [x1, y0 - offset, z0], [x0, y0, z0], [x1, y0, z0], `${kind === "cylinder" ? "Ø" : "X"} ${fmtShort(metrics.bounds_mm.x)} mm`);
      dimension([x1 + offset, y0, z0], [x1 + offset, y1, z0], [x1, y0, z0], [x1, y1, z0], `Y ${fmtShort(metrics.bounds_mm.y)} mm`);
      dimension([x0 - offset, y0, z0], [x0 - offset, y0, z1], [x0, y0, z0], [x0, y0, z1], `Z ${fmtShort(metrics.bounds_mm.z)} mm`);
    }
    function drawAxes() {
      const c = axisContext; c.clearRect(0, 0, 150, 150);
      const axesToDraw = [
        { value: [1, 0, 0], color: "#c98d74", label: "X" },
        { value: [0, 1, 0], color: "#9bbb8c", label: "Y" },
        { value: [0, 0, 1], color: "#86b7c2", label: "Z" },
      ].sort((a, b) => dot(a.value, direction) - dot(b.value, direction));
      c.fillStyle = "#455b4d"; c.beginPath(); c.arc(75, 75, 4, 0, Math.PI * 2); c.fill();
      for (const axis of axesToDraw) {
        const x = dot(axis.value, right), y = -dot(axis.value, up);
        const px = 75 + x * 36, py = 75 + y * 36;
        c.strokeStyle = axis.color; c.lineWidth = 1.4; c.beginPath(); c.moveTo(75, 75); c.lineTo(px, py); c.stroke();
        c.fillStyle = "#24362d"; c.beginPath(); c.arc(px, py, 10, 0, Math.PI * 2); c.fill();
        c.strokeStyle = axis.color; c.lineWidth = .7; c.stroke(); c.fillStyle = axis.color; c.font = "10px 'Segoe UI', sans-serif"; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText(axis.label, px, py + .6);
      }
    }
    function draw() {
      requested = false; axes();
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0); context.clearRect(0, 0, width, height);
      drawShadow(); drawGrid(); drawModel(); drawDimensions(); drawAxes();
      $("viewport-scale").textContent = perspective ? "Perspective preview" : `${fmtShort(1 / scale)} mm / px`;
    }
    function schedule() { if (!requested) { requested = true; requestAnimationFrame(draw); } }
    function updateViewButtons() { $$('[data-view]').forEach((button) => { const active = button.dataset.view === currentView; button.classList.toggle("active", active); button.setAttribute("aria-pressed", String(active)); }); }
    function fit() { zoom = 1; panX = 0; panY = 0; schedule(); }
    function view(name) {
      currentView = name;
      if (name === "iso") { yaw = -.62; pitch = .48; }
      if (name === "top") { yaw = 0; pitch = Math.PI / 2; }
      if (name === "front") { yaw = 0; pitch = 0; }
      if (name === "right") { yaw = Math.PI / 2; pitch = 0; }
      updateViewButtons(); schedule();
    }
    function setMesh(mesh, exactMetrics = {}, partKind = "box", resetView = false) {
      metrics = exactMetrics || {}; kind = partKind;
      const source = mesh?.vertices || [];
      vertices = source.filter((v) => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite));
      if (vertices.length !== source.length) vertices = [];
      if (vertices.length) {
        minimum = [Infinity, Infinity, Infinity]; maximum = [-Infinity, -Infinity, -Infinity];
        for (const vertex of vertices) for (let axis = 0; axis < 3; axis++) { minimum[axis] = Math.min(minimum[axis], vertex[axis]); maximum[axis] = Math.max(maximum[axis], vertex[axis]); }
        center = minimum.map((v, i) => (v + maximum[i]) / 2);
        radius = Math.max(Math.hypot(...maximum.map((v, i) => v - minimum[i])) / 2, .001);
      }
      const tolerance = Math.max(radius * 1e-8, 1e-10);
      const vertexKeys = vertices.map((v) => v.map((n) => Math.round(n / tolerance)).join(","));
      const edgeMap = new Map();
      triangles = [];
      for (const ids of mesh?.triangles || []) {
        if (!Array.isArray(ids) || ids.length !== 3 || !ids.every((index) => Number.isInteger(index) && index >= 0 && index < vertices.length)) continue;
        const normal = normalize(cross(subtract(vertices[ids[1]], vertices[ids[0]]), subtract(vertices[ids[2]], vertices[ids[0]])));
        const tri = { ids, normal, sharp: [false, false, false] };
        triangles.push(tri);
        for (let edge = 0; edge < 3; edge++) {
          const a = vertexKeys[ids[edge]], b = vertexKeys[ids[(edge + 1) % 3]];
          const key = a < b ? `${a}|${b}` : `${b}|${a}`;
          if (!edgeMap.has(key)) edgeMap.set(key, []);
          edgeMap.get(key).push({ tri, edge });
        }
      }
      for (const entries of edgeMap.values()) {
        const sharp = entries.length !== 2 || dot(entries[0].tri.normal, entries[1].tri.normal) < .985;
        if (sharp) for (const entry of entries) entry.tri.sharp[entry.edge] = true;
      }
      if (resetView) { fit(); view("iso"); }
      schedule();
    }
    function toggleGrid() { grid = !grid; $("grid-button").classList.toggle("active", grid); $("grid-button").setAttribute("aria-pressed", String(grid)); schedule(); }
    function toggleDimensions() { dimensions = !dimensions; $("dimensions-button").classList.toggle("active", dimensions); $("dimensions-button").setAttribute("aria-pressed", String(dimensions)); schedule(); }
    function toggleProjection() { perspective = !perspective; $("projection-button").textContent = perspective ? "PERSP" : "ORTHO"; $("projection-button").setAttribute("aria-label", `Switch projection; currently ${perspective ? "perspective" : "orthographic"}`); schedule(); }
    canvas.addEventListener("pointerdown", (event) => {
      if (event.button !== 0 && event.button !== 1 && event.button !== 2) return;
      pointer = { id: event.pointerId, x: event.clientX, y: event.clientY, pan: event.shiftKey || event.button !== 0 };
      canvas.setPointerCapture(event.pointerId); canvas.focus({ preventScroll: true }); event.preventDefault();
    });
    canvas.addEventListener("pointermove", (event) => {
      if (!pointer || event.pointerId !== pointer.id) return;
      const dx = event.clientX - pointer.x, dy = event.clientY - pointer.y;
      pointer.x = event.clientX; pointer.y = event.clientY;
      if (pointer.pan || event.shiftKey) { panX += dx; panY += dy; }
      else { yaw += dx * .008; pitch = Math.max(-Math.PI / 2 + .005, Math.min(Math.PI / 2 - .005, pitch + dy * .008)); currentView = "custom"; updateViewButtons(); }
      schedule();
    });
    const release = () => { pointer = null; };
    canvas.addEventListener("pointerup", release); canvas.addEventListener("pointercancel", release); canvas.addEventListener("lostpointercapture", release);
    canvas.addEventListener("contextmenu", (event) => event.preventDefault());
    canvas.addEventListener("wheel", (event) => { event.preventDefault(); zoom = Math.max(.08, Math.min(18, zoom * Math.exp(-event.deltaY * .001))); schedule(); }, { passive: false });
    canvas.addEventListener("dblclick", fit);
    new ResizeObserver(() => {
      const rect = canvas.getBoundingClientRect(); width = Math.max(rect.width, 1); height = Math.max(rect.height, 1); pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(width * pixelRatio); canvas.height = Math.round(height * pixelRatio); schedule();
    }).observe(canvas);
    $("fit-button").addEventListener("click", fit);
    $("grid-button").addEventListener("click", toggleGrid);
    $("dimensions-button").addEventListener("click", toggleDimensions);
    $("projection-button").addEventListener("click", toggleProjection);
    $$('[data-view]').forEach((button) => button.addEventListener("click", () => view(button.dataset.view)));
    return { setMesh, fit, view, toggleGrid, toggleDimensions, toggleProjection };
  }
  const viewer = makeViewer();

  const commands = [
    { name: "New box", icon: "cube", hint: "Create", action: () => newPart("box") },
    { name: "New drilled plate", icon: "plate", hint: "Create", action: () => newPart("plate") },
    { name: "New cylinder", icon: "cylinder", hint: "Create", action: () => newPart("cylinder") },
    { name: "Open B-CAD project", icon: "folder", hint: "Ctrl O", action: () => $("project-input").click() },
    { name: "Save project", icon: "save", hint: "Ctrl S", action: saveProject },
    { name: "Import STEP solid", icon: "upload", hint: "Exchange", action: () => $("step-input").click() },
    { name: "Export exact STEP", icon: "download", hint: "Exchange", action: () => exportSolid("step") },
    { name: "Export STL mesh", icon: "download", hint: "Exchange", action: () => exportSolid("stl") },
    { name: "Preview dimensions", icon: "eye", hint: "Parameters", action: preview },
    { name: "Apply dimensions", icon: "check", hint: "Parameters", action: apply },
    { name: "Discard parameter changes", icon: "close", hint: "Parameters", action: discard },
    { name: "Undo", icon: "undo", hint: "Ctrl Z", action: () => history("undo") },
    { name: "Redo", icon: "redo", hint: "Ctrl Shift Z", action: () => history("redo") },
    { name: "Fit model", icon: "fit", hint: "F", action: viewer.fit },
    { name: "Isometric view", icon: "cube", hint: "1", action: () => viewer.view("iso") },
    { name: "Top view", icon: "box", hint: "2", action: () => viewer.view("top") },
    { name: "Front view", icon: "box", hint: "3", action: () => viewer.view("front") },
    { name: "Right view", icon: "box", hint: "4", action: () => viewer.view("right") },
    { name: "Toggle construction grid", icon: "grid", hint: "View", action: viewer.toggleGrid },
    { name: "Toggle overall dimensions", icon: "ruler", hint: "View", action: viewer.toggleDimensions },
    { name: "Toggle orthographic / perspective projection", icon: "box", hint: "View", action: viewer.toggleProjection },
    { name: "Workbench guide and shortcuts", icon: "info", hint: "Help", action: () => $("help-dialog").showModal() },
  ];
  function commandEnabled(command) {
    if (pending) return /view|Fit|Toggle|guide/i.test(command.name);
    if (/^New|^Open|^Import/.test(command.name)) return kernelAvailable;
    if (/^Save|^Export/.test(command.name)) return !!committed && !isDirty() && !previewing && !stale;
    if (/^Preview|^Apply/.test(command.name)) return kernelAvailable && isDirty();
    if (/^Discard/.test(command.name)) return !!committed && (isDirty() || previewing || stale);
    if (command.name === "Undo") return !!committed?.history?.can_undo;
    if (command.name === "Redo") return !!committed?.history?.can_redo;
    return true;
  }
  function renderCommands() {
    const query = $("command-search").value.toLowerCase().trim();
    visibleCommands = commands.filter((command) => command.name.toLowerCase().includes(query));
    commandIndex = Math.max(0, Math.min(commandIndex, visibleCommands.length - 1));
    $("command-results").replaceChildren();
    if (!visibleCommands.length) { const empty = document.createElement("p"); empty.className = "command-empty"; empty.textContent = "No matching command. Try ‘box’, ‘export’ or ‘view’."; $("command-results").append(empty); }
    visibleCommands.forEach((command, index) => {
      const button = document.createElement("button"); button.className = `command-result${index === commandIndex ? " selected" : ""}`; button.disabled = !commandEnabled(command);
      const hint = document.createElement("small"); hint.textContent = command.hint;
      button.append(icon(command.icon), document.createTextNode(command.name), hint);
      button.addEventListener("click", () => executeCommand(command));
      $("command-results").append(button);
    });
    $("command-results").querySelector(".selected")?.scrollIntoView({ block: "nearest" });
  }
  function executeCommand(command) { if (!command || !commandEnabled(command)) return; $("command-dialog").close(); command.action(); }
  function openCommands() { closeExport(); $("command-search").value = ""; commandIndex = 0; renderCommands(); $("command-dialog").showModal(); $("command-search").focus(); }
  $("command-search").addEventListener("input", () => { commandIndex = 0; renderCommands(); });
  $("command-search").addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") { event.preventDefault(); commandIndex = (commandIndex + (event.key === "ArrowDown" ? 1 : -1) + visibleCommands.length) % Math.max(visibleCommands.length, 1); renderCommands(); }
    if (event.key === "Enter") { event.preventDefault(); executeCommand(visibleCommands[commandIndex]); }
  });
  $("command-button").addEventListener("click", openCommands);
  $("command-close").addEventListener("click", () => $("command-dialog").close());
  ["help-button", "guide-button"].forEach((id) => $(id).addEventListener("click", () => $("help-dialog").showModal()));
  ["help-close", "help-start"].forEach((id) => $(id).addEventListener("click", () => $("help-dialog").close()));
  $("parameter-form").addEventListener("submit", (event) => { event.preventDefault(); apply(); });
  $("preview-button").addEventListener("click", preview);
  $("cancel-button").addEventListener("click", discard);
  $("new-button").addEventListener("click", () => newPart("box"));
  $$('[data-kind]').forEach((button) => button.addEventListener("click", () => newPart(button.dataset.kind)));
  $("open-button").addEventListener("click", () => $("project-input").click());
  $("save-button").addEventListener("click", saveProject);
  $("import-button").addEventListener("click", () => $("step-input").click());
  $("undo-button").addEventListener("click", () => history("undo"));
  $("redo-button").addEventListener("click", () => history("redo"));
  $("export-button").addEventListener("click", () => { const open = $("export-menu").hidden; $("export-menu").hidden = !open; $("export-button").setAttribute("aria-expanded", String(open)); });
  $$('[data-export]').forEach((button) => button.addEventListener("click", () => exportSolid(button.dataset.export)));
  document.addEventListener("click", (event) => { if (!event.target.closest(".export-wrap")) closeExport(); });
  $("project-input").addEventListener("change", (event) => { const file = event.target.files[0]; event.target.value = ""; openProject(file); });
  $("step-input").addEventListener("change", (event) => { const file = event.target.files[0]; event.target.value = ""; importStep(file); });
  document.addEventListener("keydown", (event) => {
    const modifier = event.ctrlKey || event.metaKey;
    const typing = /INPUT|TEXTAREA|SELECT/.test(event.target.tagName) || event.target.isContentEditable;
    const modalOpen = $("command-dialog").open || $("help-dialog").open;
    if (modifier && event.key.toLowerCase() === "k") { event.preventDefault(); if (!modalOpen) openCommands(); return; }
    if (event.key === "Escape") { closeExport(); return; }
    if (modalOpen) return;
    if (modifier && event.key.toLowerCase() === "s") { event.preventDefault(); saveProject(); return; }
    if (modifier && event.key.toLowerCase() === "o") { event.preventDefault(); if (!pending && kernelAvailable) $("project-input").click(); return; }
    if (!typing && modifier && event.key.toLowerCase() === "z") { event.preventDefault(); history(event.shiftKey ? "redo" : "undo"); return; }
    if (typing || modifier || event.altKey) return;
    if (event.key.toLowerCase() === "f" || event.key === "Home") { event.preventDefault(); viewer.fit(); }
    const view = { "1": "iso", "2": "top", "3": "front", "4": "right" }[event.key];
    if (view) { event.preventDefault(); viewer.view(view); }
    if (event.key === "?") $("help-dialog").showModal();
  });
  window.addEventListener("beforeunload", (event) => { if (hasUnsavedChanges()) { event.preventDefault(); event.returnValue = ""; } });

  async function start() {
    setBusy(true);
    try {
      const response = await fetch("/api/bootstrap", { cache: "no-store", credentials: "same-origin" });
      const bootstrap = await response.json();
      if (!response.ok) throw new Error(bootstrap?.error?.message || "The local server could not start the workbench.");
      token = bootstrap.token;
      if (typeof token !== "string" || !token.length) throw new Error("The local server did not provide a session token. Reload the workbench.");
      kernelAvailable = bootstrap.state?.kernel_available ?? bootstrap.kernel_available ?? !!bootstrap.state?.result;
      if (bootstrap.state?.document) {
        acceptState(bootstrap.state, { resetView: true });
        savedFingerprint = fingerprint();
      }
      if (!kernelAvailable) throw new Error("The geometry engine is unavailable. Start B-CAD from the Python environment where its CAD dependencies are installed, then reload this page. Check the server terminal for details.");
      status("Ready · create a part or explore its dimensions");
      $("engine-indicator").classList.add("connected");
    } catch (error) {
      $("engine-status").textContent = "Geometry engine unavailable";
      $("engine-indicator").classList.add("error");
      $("empty-state").hidden = false;
      $("empty-state").querySelector("h2").textContent = "Your workspace needs its engine.";
      $("empty-state").querySelector("p").textContent = "Check the local server terminal, then reload this page.";
      showError(error, false);
    } finally { setBusy(false); renderBadges(); }
  }
  start();
})();
