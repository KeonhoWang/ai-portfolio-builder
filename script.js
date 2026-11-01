// ── Particles ──
const canvas = document.getElementById("bg-canvas");
const ctx = canvas.getContext("2d");
let particles = [];

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

resizeCanvas();
window.addEventListener("resize", resizeCanvas);

for (let i = 0; i < 50; i++) {
  particles.push({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    size: Math.random() * 1.5 + 0.5,
    speedX: (Math.random() - 0.5) * 0.2,
    speedY: (Math.random() - 0.5) * 0.2,
    opacity: Math.random() * 0.3 + 0.05,
  });
}

function animateParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  particles.forEach((p) => {
    p.x += p.speedX;
    p.y += p.speedY;
    if (p.x < 0 || p.x > canvas.width) p.speedX *= -1;
    if (p.y < 0 || p.y > canvas.height) p.speedY *= -1;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(124,58,237,${p.opacity})`;
    ctx.fill();
  });
  requestAnimationFrame(animateParticles);
}

animateParticles();

// ── State ──
let currentStep = 1;
let selectedTheme = "dark";
let selectedFont = "modern";
let projectCount = 1;
let generatedHTML = "";
let formData = {};
let editState = {}; // settings chosen by the Edit panel (colors, fonts, etc.)
let photoBase64 = "";
let selectedTone_ = "professional";
let selectedDur = "60";

// ── Photo ──
function handlePhotoUpload(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    photoBase64 = e.target.result.split(",")[1];
    const img = document.getElementById("photo-img");
    const placeholder = document.getElementById("photo-placeholder");
    const removeBtn = document.getElementById("btn-remove-photo");
    img.src = e.target.result;
    img.classList.remove("hidden");
    placeholder.classList.add("hidden");
    removeBtn.classList.remove("hidden");
    document.getElementById("photo-preview").style.border =
      "2px solid var(--primary)";
  };
  reader.readAsDataURL(file);
}

function removePhoto() {
  photoBase64 = "";
  document.getElementById("photo-img").src = "";
  document.getElementById("photo-img").classList.add("hidden");
  document.getElementById("photo-placeholder").classList.remove("hidden");
  document.getElementById("btn-remove-photo").classList.add("hidden");
  document.getElementById("photo-input").value = "";
  document.getElementById("photo-preview").style.border =
    "2px dashed var(--border)";
}

// ── Navigation ──
function startBuilder() {
  document.getElementById("landing-screen").classList.add("hidden");
  document.getElementById("builder-screen").classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function goToLanding() {
  document.getElementById("builder-screen").classList.add("hidden");
  document.getElementById("landing-screen").classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function buildNew() {
  document.getElementById("result-screen").classList.add("hidden");
  document.getElementById("landing-screen").classList.remove("hidden");
  currentStep = 1;
  projectCount = 1;
  generatedHTML = "";
  formData = {};
  editState = {};
  photoBase64 = "";
  selectedTheme = "dark";
  selectedFont = "modern";
  resetForm();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetForm() {
  const fieldIds = [
    "f-name",
    "f-title",
    "f-bio",
    "f-email",
    "f-github",
    "f-linkedin",
    "f-skills",
  ];
  fieldIds.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  removePhoto();
  document.getElementById("projects-container").innerHTML =
    createProjectEntry(0);
  projectCount = 1;
  document.getElementById("add-project-btn").style.display = "block";
  updateSteps(1);
  document
    .querySelectorAll(".form-step")
    .forEach((s, i) => s.classList.toggle("hidden", i !== 0));
}

// ── Steps ──
function nextStep(step) {
  if (step === 1) {
    const name = document.getElementById("f-name").value.trim();
    const title = document.getElementById("f-title").value.trim();
    if (!name || !title) {
      alert("Please fill in your name and professional title!");
      return;
    }
  }
  document.getElementById(`step-${step}`).classList.add("hidden");
  document.getElementById(`step-${step + 1}`).classList.remove("hidden");
  currentStep = step + 1;
  updateSteps(currentStep);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function prevStep(step) {
  document.getElementById(`step-${step}`).classList.add("hidden");
  document.getElementById(`step-${step - 1}`).classList.remove("hidden");
  currentStep = step - 1;
  updateSteps(currentStep);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function updateSteps(active) {
  for (let i = 1; i <= 4; i++) {
    const dot = document.getElementById(`step-dot-${i}`);
    if (!dot) continue;
    dot.classList.remove("active", "done");
    if (i < active) dot.classList.add("done");
    if (i === active) dot.classList.add("active");
  }
}

// ── Skills ──
function addSkill(skill) {
  const input = document.getElementById("f-skills");
  const current = input.value.trim();
  if (current.includes(skill)) return;
  input.value = current ? `${current}, ${skill}` : skill;
}

// ── Projects ──
function createProjectEntry(index) {
  return `
    <div class="project-entry" id="project-${index}">
      <div class="project-entry-header">
        <span>Project ${index + 1}</span>
        ${index > 0 ? `<button class="btn-remove-project" onclick="removeProject(${index})">✕ Remove</button>` : ""}
      </div>
      <div class="form-grid">
        <div class="form-group"><label>Project Name</label><input type="text" class="p-name" placeholder="e.g. Chat App" /></div>
        <div class="form-group"><label>Tech Stack</label><input type="text" class="p-tech" placeholder="e.g. React, Node.js" /></div>
        <div class="form-group full"><label>Description</label><input type="text" class="p-desc" placeholder="Brief description..." /></div>
        <div class="form-group full"><label>GitHub / Live URL</label><input type="text" class="p-url" placeholder="https://github.com/..." /></div>
      </div>
    </div>
  `;
}

function addProject() {
  if (projectCount >= 6) {
    document.getElementById("add-project-btn").style.display = "none";
    return;
  }
  const container = document.getElementById("projects-container");
  const div = document.createElement("div");
  div.innerHTML = createProjectEntry(projectCount);
  container.appendChild(div.firstElementChild);
  projectCount++;
  if (projectCount >= 6)
    document.getElementById("add-project-btn").style.display = "none";
}

function removeProject(index) {
  const el = document.getElementById(`project-${index}`);
  if (el) el.remove();
  projectCount--;
  document.getElementById("add-project-btn").style.display = "block";
}

// ── Theme & Font ──
function selectTheme(theme) {
  selectedTheme = theme;
  document.querySelectorAll(".theme-option").forEach((el) => {
    el.classList.toggle("active", el.dataset.theme === theme);
  });
}

function selectFont(font) {
  selectedFont = font;
  document.querySelectorAll(".font-option").forEach((el) => {
    el.classList.toggle("active", el.dataset.font === font);
  });
}

function setThemePreview(theme) {
  selectTheme(theme);
}

// ── Collect Data ──
function collectFormData() {
  const projects = [];
  document.querySelectorAll(".project-entry").forEach((entry) => {
    const name = entry.querySelector(".p-name")?.value.trim();
    const tech = entry.querySelector(".p-tech")?.value.trim();
    const desc = entry.querySelector(".p-desc")?.value.trim();
    const url = entry.querySelector(".p-url")?.value.trim();
    if (name) projects.push({ name, tech, desc, url });
  });

  return {
    name: document.getElementById("f-name").value.trim(),
    title: document.getElementById("f-title").value.trim(),
    bio: document.getElementById("f-bio").value.trim(),
    skills: document.getElementById("f-skills").value.trim(),
    email: document.getElementById("f-email").value.trim(),
    github: document.getElementById("f-github").value.trim(),
    linkedin: document.getElementById("f-linkedin").value.trim(),
    projects,
    theme: selectedTheme,
    font_style: selectedFont,
    photo: photoBase64,
  };
}

// ── Result helpers ──
function hideAllPanels() {
  const panelIds = ["score-panel", "edit-panel", "cover-panel", "script-panel"];
  panelIds.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.classList.add("hidden");
  });
}

function getFilename() {
  const base = (formData.name || "portfolio")
    .replace(/\s+/g, "-")
    .toLowerCase();
  return `${base}-portfolio.html`;
}

function showResult() {
  document.getElementById("generating-screen").classList.add("hidden");
  document.getElementById("result-screen").classList.remove("hidden");
  hideAllPanels();
  document.getElementById("preview-frame").srcdoc = generatedHTML;
  document.getElementById("preview-url").textContent = getFilename();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ── Generate ──
async function generatePortfolio(useExisting = false) {
  if (useExisting && formData.name) {
    formData = { ...formData };
  } else {
    formData = collectFormData();
  }
  delete formData.overrides;

  if (!formData.name || !formData.title) {
    alert("Please fill in at least your name and title!");
    prevStep(4);
    return;
  }

  document.getElementById("builder-screen").classList.add("hidden");
  document.getElementById("generating-screen").classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });

  const steps = ["gen-step-1", "gen-step-2", "gen-step-3", "gen-step-4"];
  const labels = [
    "⚡ Analyzing your information",
    "🎨 Designing your layout",
    "💻 Writing your code",
    "✨ Adding finishing touches",
  ];
  const delays = [0, 3000, 6000, 9000];
  const progresses = [15, 40, 70, 90];

  steps.forEach((id, i) => {
    setTimeout(() => {
      steps.slice(0, i).forEach((prev) => {
        const el = document.getElementById(prev);
        if (el) {
          el.classList.remove("active");
          el.classList.add("done");
          el.textContent = "✅ Done";
        }
      });
      const el = document.getElementById(id);
      if (el) {
        el.classList.remove("done");
        el.classList.add("active");
        el.textContent = labels[i];
      }
      document.getElementById("gen-progress-fill").style.width =
        progresses[i] + "%";
    }, delays[i]);
  });

  try {
    const res = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    });

    const data = await res.json();

    if (data.error) {
      alert("Error: " + data.error);
      document.getElementById("generating-screen").classList.add("hidden");
      document.getElementById("builder-screen").classList.remove("hidden");
      return;
    }

    generatedHTML = data.html;
    editState = data.overrides || {};
    document.getElementById("gen-progress-fill").style.width = "100%";

    setTimeout(showResult, 800);
  } catch (err) {
    console.error(err);
    alert("Failed to generate. Make sure app.py is running!");
    document.getElementById("generating-screen").classList.add("hidden");
    document.getElementById("builder-screen").classList.remove("hidden");
  }
}

// ── Regenerate ──
async function regenerate() {
  document.getElementById("result-screen").classList.add("hidden");
  document.getElementById("generating-screen").classList.remove("hidden");

  const labels = [
    "⚡ Analyzing your information",
    "🎨 Designing your layout",
    "💻 Writing your code",
    "✨ Adding finishing touches",
  ];
  document.querySelectorAll(".gen-step").forEach((el, i) => {
    el.classList.remove("active", "done");
    el.textContent = labels[i];
  });
  document.getElementById("gen-progress-fill").style.width = "0%";
  await generatePortfolio(true);
}

// ── Download ──
async function downloadPortfolio() {
  if (!generatedHTML) return;
  const filename = getFilename();

  try {
    const res = await fetch("/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ html: generatedHTML, filename }),
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    const blob = new Blob([generatedHTML], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }
}

// ── Save ──
async function saveCurrentPortfolio() {
  if (!generatedHTML) return;
  try {
    const res = await fetch("/saves", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        html: generatedHTML,
        form: { ...formData, overrides: editState },
      }),
    });
    const data = await res.json();
    if (data.success) {
      showToast("💾 Portfolio saved!");
      loadSaves();
    }
  } catch (e) {
    showToast("Failed to save");
  }
}

// ── Saves Panel ──
let savesVisible = false;

function toggleSavesPanel() {
  savesVisible = !savesVisible;
  document
    .getElementById("saves-panel")
    .classList.toggle("hidden", !savesVisible);
  if (savesVisible) loadSaves();
}

async function loadSaves() {
  try {
    const res = await fetch("/saves");
    const saves = await res.json();
    const list = document.getElementById("saves-list");

    if (!saves.length) {
      list.innerHTML = '<div class="panel-empty">No saved portfolios yet</div>';
      return;
    }

    list.innerHTML = "";
    saves
      .slice()
      .reverse()
      .forEach((save) => {
        const div = document.createElement("div");
        div.classList.add("save-item");
        div.innerHTML = `
        <div class="save-item-name">👤 ${save.name}</div>
        <div class="save-item-meta">${save.title} · ${save.theme} · ${save.created}</div>
        <div class="save-item-actions">
          <button class="btn-load" onclick="loadSave(${save.id})">📂 Load</button>
          <button class="btn-del"  onclick="deleteSave(${save.id})">🗑️</button>
        </div>
      `;
        list.appendChild(div);
      });
  } catch (e) {
    console.error(e);
  }
}

async function loadSave(id) {
  try {
    const res = await fetch(`/saves/${id}`);
    const save = await res.json();
    if (save.html) {
      generatedHTML = save.html;
      formData = save.form || {};
      editState = formData.overrides || {};
      document.getElementById("landing-screen").classList.add("hidden");
      document.getElementById("builder-screen").classList.add("hidden");
      document.getElementById("generating-screen").classList.add("hidden");
      document.getElementById("result-screen").classList.remove("hidden");
      hideAllPanels();
      document.getElementById("preview-frame").srcdoc = generatedHTML;
      document.getElementById("preview-url").textContent = getFilename();
      toggleSavesPanel();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  } catch (e) {
    console.error(e);
  }
}

async function deleteSave(id) {
  try {
    await fetch(`/saves/${id}`, { method: "DELETE" });
    loadSaves();
    showToast("🗑️ Deleted");
  } catch (e) {
    console.error(e);
  }
}

// ── Score ──
async function scorePortfolio() {
  const panel = document.getElementById("score-panel");
  if (!panel.classList.contains("hidden")) {
    panel.classList.add("hidden");
    return;
  }

  panel.classList.remove("hidden");
  document.getElementById("score-content").innerHTML =
    '<div class="panel-loading"><div class="spinner"></div><span>AI is reviewing your portfolio...</span></div>';
  panel.scrollIntoView({ behavior: "smooth" });

  try {
    const res = await fetch("/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ html: generatedHTML, name: formData.name }),
    });
    const data = await res.json();

    if (data.error) {
      document.getElementById("score-content").innerHTML =
        `<div style="color:var(--red);padding:16px">Error: ${data.error}</div>`;
      return;
    }

    const overall = data.overall || 0;
    const color =
      overall >= 80 ? "#4ade80" : overall >= 60 ? "#f59e0b" : "#e94560";
    const cats = data.categories || {};

    document.getElementById("score-content").innerHTML = `
      <div class="score-overall">
        <div class="score-overall-num" style="color:${color}">${overall}</div>
        <div class="score-overall-label">OVERALL SCORE / 100</div>
      </div>
      <div class="score-categories">
        ${Object.entries(cats)
          .map(([key, val]) => {
            const c =
              val.score >= 80
                ? "#4ade80"
                : val.score >= 60
                  ? "#f59e0b"
                  : "#e94560";
            return `
            <div class="score-cat">
              <div class="score-cat-label">${key.replace("_", " ")}</div>
              <div class="score-cat-num" style="color:${c}">${val.score}</div>
              <div class="score-cat-fb">${val.feedback || ""}</div>
            </div>`;
          })
          .join("")}
      </div>
      <div class="score-lists">
        <div class="score-list">
          <h4 class="green">✅ Strengths</h4>
          <ul>${(data.strengths || []).map((s) => `<li>${s}</li>`).join("")}</ul>
        </div>
        <div class="score-list">
          <h4 class="yellow">💡 Improvements</h4>
          <ul>${(data.improvements || []).map((s) => `<li>${s}</li>`).join("")}</ul>
        </div>
      </div>
      ${data.verdict ? `<div class="score-verdict">💬 ${data.verdict}</div>` : ""}
    `;
  } catch (err) {
    document.getElementById("score-content").innerHTML =
      '<div style="color:var(--red);padding:16px">Failed to score. Try again!</div>';
  }
}

// ── Edit ──
const EDIT_EXAMPLES = [
  "Change the main color to gold",
  "Make the hero bigger",
  "Make the text larger",
  "Add a light/dark switch",
  "Add more animations",
  "Turn animations off",
  "Use an elegant font",
  "Switch to the blue theme",
  "Hide the contact section",
];

function initEditPanel() {
  const hint = document.querySelector(".edit-hint");
  if (hint) {
    hint.textContent =
      "Describe a change: colors, fonts, text size, animations, themes, hiding sections, or a new tagline/bio.";
  }

  const input = document.getElementById("edit-input");
  if (input)
    input.placeholder = "e.g. Make the main color teal and the text bigger";

  const box = document.querySelector(".edit-examples");
  if (!box) return;
  box.innerHTML = "";
  EDIT_EXAMPLES.forEach((text) => {
    const btn = document.createElement("button");
    btn.textContent = text;
    btn.addEventListener("click", () => setEditText(text));
    box.appendChild(btn);
  });
}

initEditPanel();

function toggleEditPanel() {
  const panel = document.getElementById("edit-panel");
  panel.classList.toggle("hidden");
  if (!panel.classList.contains("hidden"))
    panel.scrollIntoView({ behavior: "smooth" });
}

function setEditText(text) {
  document.getElementById("edit-input").value = text;
}

async function applyEdit() {
  const changes = document.getElementById("edit-input").value.trim();
  if (!changes) {
    alert("Please describe what you want to change!");
    return;
  }

  const btn = document.querySelector(".btn-apply-edit");
  const btnText = document.getElementById("edit-btn-text");
  btn.disabled = true;
  btnText.innerHTML = '<span class="spinner"></span> Applying...';

  try {
    const res = await fetch("/edit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ form: formData, overrides: editState, changes }),
    });
    const data = await res.json();

    if (data.error) {
      alert("Edit failed: " + data.error);
      return;
    }

    if (data.unsupported) {
      alert("ℹ️ " + data.unsupported);
      return;
    }

    generatedHTML = data.html;
    editState = data.overrides || editState;
    document.getElementById("preview-frame").srcdoc = generatedHTML;
    document.getElementById("edit-input").value = "";
    closePanel("edit-panel");
    showToast("✅ " + (data.summary || "Changes applied!"));
  } catch (err) {
    alert("Edit failed. Try again!");
  } finally {
    btn.disabled = false;
    btnText.innerHTML = "✨ Apply Changes";
  }
}

// ── Cover Letter ──
function toggleCoverPanel() {
  const panel = document.getElementById("cover-panel");
  panel.classList.toggle("hidden");
  if (!panel.classList.contains("hidden"))
    panel.scrollIntoView({ behavior: "smooth" });
}

function selectTone(tone) {
  selectedTone_ = tone;
  document.querySelectorAll(".tone-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.tone === tone);
  });
}

async function generateCoverLetter() {
  const company = document.getElementById("cover-company").value.trim();
  const jobTitle = document.getElementById("cover-job").value.trim();

  const btn = document.querySelector(".btn-generate-cover");
  const btnText = document.getElementById("cover-btn-text");
  btn.disabled = true;
  btnText.innerHTML = '<span class="spinner"></span> Writing...';

  try {
    const res = await fetch("/cover-letter", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: formData.name,
        title: formData.title,
        skills: formData.skills,
        projects: formData.projects,
        company: company || "the company",
        job_title: jobTitle || formData.title,
        tone: selectedTone_,
      }),
    });
    const data = await res.json();

    if (data.error) {
      alert("Error: " + data.error);
      return;
    }

    document.getElementById("cover-result").classList.remove("hidden");
    document.getElementById("cover-letter-text").textContent = data.letter;
  } catch (err) {
    alert("Failed to generate cover letter. Try again!");
  } finally {
    btn.disabled = false;
    btnText.innerHTML = "📝 Generate Cover Letter";
  }
}

function copyCoverLetter() {
  navigator.clipboard.writeText(
    document.getElementById("cover-letter-text").textContent,
  );
  showToast("📋 Copied to clipboard!");
}

function downloadCoverLetter() {
  const text = document.getElementById("cover-letter-text").textContent;
  const filename = `${(formData.name || "portfolio").replace(/\s+/g, "-").toLowerCase()}-cover-letter.txt`;
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Video Script ──
function toggleScriptPanel() {
  const panel = document.getElementById("script-panel");
  panel.classList.toggle("hidden");
  if (!panel.classList.contains("hidden"))
    panel.scrollIntoView({ behavior: "smooth" });
}

function selectDuration(dur) {
  selectedDur = dur;
  document.querySelectorAll(".dur-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.dur === dur);
  });
}

async function generateVideoScript() {
  const btn = document.querySelector(".btn-generate-script");
  const btnText = document.getElementById("script-btn-text");
  btn.disabled = true;
  btnText.innerHTML = '<span class="spinner"></span> Writing...';

  try {
    const res = await fetch("/video-script", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: formData.name,
        title: formData.title,
        skills: formData.skills,
        projects: formData.projects,
        duration: selectedDur,
      }),
    });
    const data = await res.json();

    if (data.error) {
      alert("Error: " + data.error);
      return;
    }

    document.getElementById("script-result").classList.remove("hidden");
    document.getElementById("video-script-text").textContent = data.script;
  } catch (err) {
    alert("Failed to generate script. Try again!");
  } finally {
    btn.disabled = false;
    btnText.innerHTML = "🎥 Generate Script";
  }
}

function copyScript() {
  navigator.clipboard.writeText(
    document.getElementById("video-script-text").textContent,
  );
  showToast("📋 Copied!");
}

function downloadScript() {
  const text = document.getElementById("video-script-text").textContent;
  const filename = `${(formData.name || "portfolio").replace(/\s+/g, "-").toLowerCase()}-video-script.txt`;
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Preview Size ──
function setPreviewSize(size) {
  document.getElementById("preview-container").className =
    `preview-container ${size}`;
  document
    .querySelectorAll(".device-btn")
    .forEach((b) => b.classList.remove("active"));
  document.getElementById(`btn-${size}`).classList.add("active");
}

// ── Panels ──
function closePanel(id) {
  document.getElementById(id).classList.add("hidden");
}

// ── Toast ──
function showToast(msg) {
  let toast = document.getElementById("app-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "app-toast";
    toast.style.cssText = `
      position:fixed; bottom:24px; left:50%; transform:translateX(-50%);
      background:var(--primary); color:#fff; padding:10px 24px; border-radius:50px;
      font-size:0.82rem; font-weight:600; z-index:300; pointer-events:none;
      transition: opacity 0.3s;
    `;
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.opacity = "1";
  setTimeout(() => {
    toast.style.opacity = "0";
  }, 2500);
}

// ── Enter key ──
document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.target.tagName === "INPUT") e.preventDefault();
});
