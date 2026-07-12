// ===================== State (mirip app.py tkinter) =====================
const state = {
  username: null,
  email: null,
  verified: false,
};

const $ = (id) => document.getElementById(id);

// ===================== Feedback (flash-list seperti pjar_web) =====================
function flash(message, type = "info") {
  const list = $("flash-list");
  const li = document.createElement("li");
  li.textContent = message;
  if (type === "ok") li.style.color = "#166534";
  if (type === "err") li.style.color = "#991b1b";
  list.appendChild(li);
  list.hidden = false;
  setTimeout(() => {
    li.remove();
    if (!list.children.length) list.hidden = true;
  }, 4000);
}

// ===================== Connection status =====================
function setStatus(ok, text) {
  const el = $("status");
  el.className = "status-bar " + (ok ? "ok" : "error");
  el.textContent = text;
}

async function checkServer() {
  try {
    const resp = await fetch("/api/health");
    if (resp.ok) {
      setStatus(true, "✓ Terhubung ke server");
    } else {
      setStatus(false, "✗ Server merespons dengan error");
    }
  } catch {
    setStatus(false, "✗ Tidak dapat terhubung ke server");
  }
}

// ===================== Render berdasarkan state =====================
function render() {
  const loggedIn = Boolean(state.username);
  $("auth-view").hidden = loggedIn;
  $("verify-view").hidden = !(loggedIn && !state.verified);
  $("dashboard-view").hidden = !loggedIn;

  if (loggedIn) {
    $("session-user").textContent = state.username;
    $("verify-status").textContent = state.verified ? "Terverifikasi" : "Belum terverifikasi";
    if (state.email) {
      $("verify-email-hint").textContent = `Kode verifikasi telah dikirim ke ${state.email}`;
    }

    // Upload & stream hanya aktif setelah verifikasi
    $("file-input").disabled = !state.verified;
    $("upload-form").querySelector("button").disabled = !state.verified;
    $("stream-button").disabled = !state.verified;
    if (state.verified) {
      loadVideos();
    } else {
      $("video-list").innerHTML = "";
      $("video-player").hidden = true;
    }
  }
}

// ===================== Login =====================
$("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const username = form.username.value.trim();
  const password = form.password.value.trim();
  if (!username || !password) {
    flash("Username dan password wajib diisi", "err");
    return;
  }
  try {
    const resp = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await resp.json();
    if (resp.ok) {
      state.username = username;
      state.email = data.email;
      state.verified = false;
      form.reset();
      render();
      flash("Login berhasil! Cek email Anda untuk kode verifikasi.", "ok");
    } else {
      flash(data.error || "Login gagal", "err");
    }
  } catch {
    flash("Gagal menghubungi server", "err");
  }
});

// ===================== Register =====================
$("register-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const payload = {
    username: form.username.value.trim(),
    password: form.password.value.trim(),
    email: form.email.value.trim(),
  };
  if (!payload.username || !payload.password || !payload.email) {
    flash("Semua kolom wajib diisi", "err");
    return;
  }
  try {
    const resp = await fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (resp.ok || resp.status === 201) {
      form.reset();
      flash("Akun berhasil dibuat. Silakan login.", "ok");
    } else {
      flash(data.error || "Register gagal", "err");
    }
  } catch {
    flash("Gagal menghubungi server", "err");
  }
});

// ===================== Verify =====================
$("verify-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const code = form.code.value.trim();
  if (!state.username) {
    flash("Lakukan login terlebih dahulu", "err");
    return;
  }
  try {
    const resp = await fetch("/api/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: state.username, code }),
    });
    const data = await resp.json();
    if (resp.ok) {
      state.verified = true;
      form.reset();
      render();
      flash("Verifikasi berhasil. Selamat datang!", "ok");
    } else {
      flash(data.error || "Verifikasi gagal", "err");
    }
  } catch {
    flash("Gagal menghubungi server", "err");
  }
});

// ===================== Upload (TCP) =====================
$("upload-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!state.verified) {
    flash("Lakukan verifikasi terlebih dahulu", "err");
    return;
  }
  const fileInput = $("file-input");
  if (!fileInput.files.length) {
    flash("Pilih file terlebih dahulu", "err");
    return;
  }
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  const resultEl = $("upload-result");
  resultEl.textContent = "Mengirim file...";
  resultEl.hidden = false;
  try {
    const resp = await fetch("/api/upload", { method: "POST", body: formData });
    const data = await resp.json();
    resultEl.textContent = data.message || data.error || "Gagal mengupload";
    if (resp.ok) flash("Upload berhasil", "ok");
    else flash(data.error || "Upload gagal", "err");
  } catch {
    flash("Gagal menghubungi server", "err");
  }
});

// ===================== Stream (UDP) =====================
$("stream-button").addEventListener("click", async () => {
  if (!state.verified) {
    flash("Lakukan verifikasi terlebih dahulu", "err");
    return;
  }
  const resultEl = $("stream-result");
  resultEl.textContent = "Memulai streaming UDP...";
  resultEl.hidden = false;
  try {
    const resp = await fetch("/api/stream", { method: "POST" });
    const data = await resp.json();
    resultEl.textContent = data.message || data.error || "Gagal streaming";
    if (resp.ok) flash("Streaming dimulai", "ok");
    else flash(data.error || "Streaming gagal", "err");
  } catch {
    flash("Gagal menghubungi server", "err");
  }
});

// ===================== Videos (tonton dari server) =====================
async function loadVideos() {
  const listEl = $("video-list");
  listEl.innerHTML = "";
  try {
    const resp = await fetch("/api/videos");
    const data = await resp.json();
    const videos = data.videos || [];
    if (!videos.length) {
      listEl.innerHTML =
        '<li style="cursor:default;background:transparent;border:none">Tidak ada video di server.</li>';
      return;
    }
    videos.forEach((v) => {
      const li = document.createElement("li");
      li.textContent = v.name;
      li.addEventListener("click", () => playVideo(v.name));
      listEl.appendChild(li);
    });
  } catch {
    listEl.innerHTML =
      '<li style="cursor:default;background:transparent;border:none">Gagal memuat daftar video.</li>';
  }
}

function playVideo(name) {
  const player = $("video-player");
  player.src = "/videos/" + encodeURIComponent(name);
  player.hidden = false;
  player.load();
  player.play().catch(() => {});
  const res = $("video-result");
  res.textContent = "Memutar: " + name;
  res.hidden = false;
}

// ===================== Logout (reset sisi client) =====================
$("logout-btn").addEventListener("click", (e) => {
  e.preventDefault();
  state.username = null;
  state.email = null;
  state.verified = false;
  ["verify-result", "upload-result", "stream-result"].forEach((id) => {
    $(id).hidden = true;
    $(id).textContent = "";
  });
  flash("Sesi diakhiri", "info");
  render();
});

// ===================== Init =====================
render();
checkServer();
