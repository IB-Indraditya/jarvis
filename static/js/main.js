// ============================================================
// J.A.R.V.I.S dashboard front-end
// Talks to the Flask REST API in routes/api.py and drives the
// central voice-reactive orb + all module widgets.
//
// Voice note: Speech-to-Text and Text-to-Speech here run in the
// BROWSER via the Web Speech API (SpeechRecognition / speechSynthesis).
// This works out of the box on any device the dashboard is opened on
// (desktop or mobile) without needing server-side mic/speaker access.
// The backend also exposes /api/voice/transcribe and /api/voice/speak
// (core/speech.py, using SpeechRecognition + pyttsx3) for server-side/
// automation use cases - e.g. a headless script speaking through the
// JARVIS host machine's own speakers.
// ============================================================

const SESSION_ID = "web-session";
let authToken = localStorage.getItem("jarvis_token") || null;

// ---------------------------------------------------------------
// Orb state machine: idle -> listening -> thinking -> speaking -> idle
// ---------------------------------------------------------------
const orb = document.getElementById("jarvisOrb");
const orbStateLabel = document.getElementById("orbStateLabel");
const micStateLabel = document.getElementById("micStateLabel");
const voiceStateLabel = document.getElementById("voiceStateLabel");
const wakeStateLabel = document.getElementById("wakeStateLabel");

function setOrbState(state) {
  orb.classList.remove("idle", "listening", "thinking", "speaking");
  orb.classList.add(state);
  orbStateLabel.textContent = state.toUpperCase();
}
setOrbState("idle");

// Build tick marks around the outer ring (24 ticks)
(function buildTicks() {
  const g = document.querySelector(".orb-ticks");
  const cx = 200, cy = 200, rOuter = 195, rInner = 186;
  for (let i = 0; i < 24; i++) {
    const angle = (i / 24) * Math.PI * 2;
    const x1 = cx + rInner * Math.cos(angle);
    const y1 = cy + rInner * Math.sin(angle);
    const x2 = cx + rOuter * Math.cos(angle);
    const y2 = cy + rOuter * Math.sin(angle);
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", x1); line.setAttribute("y1", y1);
    line.setAttribute("x2", x2); line.setAttribute("y2", y2);
    g.appendChild(line);
  }
})();

// Build audio-reactive bars ring (32 bars) — heights driven by mic volume
const BAR_COUNT = 32;
const audioBarEls = [];
(function buildAudioBars() {
  const g = document.getElementById("audioBars");
  const cx = 200, cy = 200, r = 118;
  for (let i = 0; i < BAR_COUNT; i++) {
    const angle = (i / BAR_COUNT) * Math.PI * 2;
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("width", 3);
    rect.setAttribute("height", 4);
    rect.setAttribute("x", cx + r * Math.cos(angle) - 1.5);
    rect.setAttribute("y", cy + r * Math.sin(angle) - 2);
    rect.setAttribute("transform", `rotate(${(angle * 180) / Math.PI + 90} ${cx + r * Math.cos(angle)} ${cy + r * Math.sin(angle)})`);
    g.appendChild(rect);
    audioBarEls.push({ el: rect, cx: cx + r * Math.cos(angle), cy: cy + r * Math.sin(angle), angle });
  }
})();

function pulseBarsRandom(intensity) {
  audioBarEls.forEach(({ el }) => {
    const h = 4 + Math.random() * intensity;
    el.setAttribute("height", h);
    el.setAttribute("y", 200 - h / 2);
  });
}
function resetBars() {
  audioBarEls.forEach(({ el }) => { el.setAttribute("height", 4); el.setAttribute("y", 198); });
}

// ---------------------------------------------------------------
// Live mic volume analyser (purely visual — reacts the orb to real
// input level while listening). Runs alongside SpeechRecognition.
// ---------------------------------------------------------------
let audioCtx, analyser, micStream, rafId;

async function startAudioVisualizer() {
  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaStreamSource(micStream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 64;
    source.connect(analyser);
    const data = new Uint8Array(analyser.frequencyBinCount);

    function tick() {
      analyser.getByteFrequencyData(data);
      const avg = data.reduce((a, b) => a + b, 0) / data.length;
      audioBarEls.forEach(({ el }, i) => {
        const v = data[i % data.length] || 0;
        const h = 4 + (v / 255) * 34;
        el.setAttribute("height", h);
        el.setAttribute("y", 200 - h / 2);
      });
      rafId = requestAnimationFrame(tick);
    }
    tick();
  } catch (err) {
    console.warn("Mic visualizer unavailable:", err);
  }
}

function stopAudioVisualizer() {
  if (rafId) cancelAnimationFrame(rafId);
  if (micStream) micStream.getTracks().forEach((t) => t.stop());
  if (audioCtx) audioCtx.close();
  resetBars();
}

// ---------------------------------------------------------------
// Chat
// ---------------------------------------------------------------
const chatLog = document.getElementById("chatLog");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const liveTranscript = document.getElementById("liveTranscript");
const speakerBtn = document.getElementById("speakerBtn");
let autoSpeak = true;

function appendMessage(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = `<b>${role === "user" ? "You" : "JARVIS"}:</b> ${text}`;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function sendToJarvis(message) {
  if (!message.trim()) return;
  appendMessage("user", message);
  setOrbState("thinking");
  liveTranscript.textContent = "";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: SESSION_ID }),
    });
    const data = await res.json();
    const reply = data.reply || data.error || "…";
    appendMessage("jarvis", reply);
    if (autoSpeak) {
      speak(reply);
    } else {
      setOrbState("idle");
    }
  } catch (err) {
    appendMessage("jarvis", "Connection error talking to the brain.");
    setOrbState("idle");
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;
  chatInput.value = "";
  sendToJarvis(message);
});

// ---------------------------------------------------------------
// Text-to-Speech (browser Web Speech API — speechSynthesis)
// ---------------------------------------------------------------
const synth = window.speechSynthesis;

function speak(text) {
  if (!synth) { setOrbState("idle"); return; }
  synth.cancel(); // stop anything currently speaking
  const utter = new SpeechSynthesisUtterance(text);
  utter.rate = 1.02;
  utter.pitch = 0.9;
  const voices = synth.getVoices();
  const preferred = voices.find((v) => /english/i.test(v.lang) && /male|david|daniel|google uk english male/i.test(v.name));
  if (preferred) utter.voice = preferred;

  utter.onstart = () => setOrbState("speaking");
  utter.onend = () => setOrbState("idle");
  utter.onerror = () => setOrbState("idle");
  synth.speak(utter);
}

speakerBtn.addEventListener("click", () => {
  autoSpeak = !autoSpeak;
  speakerBtn.classList.toggle("active", autoSpeak);
  if (!autoSpeak) synth.cancel();
});

// ---------------------------------------------------------------
// Speech-to-Text (browser Web Speech API — SpeechRecognition)
// ---------------------------------------------------------------
const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
const voiceSupportNote = document.getElementById("voiceSupportNote");
const micBtn = document.getElementById("micBtn");
const wakeBtn = document.getElementById("wakeBtn");

let recognizer = null;
let micActive = false;
let wakeModeActive = false;
const WAKE_PHRASES = ["hey jarvis", "jarvis"];

if (!SpeechRecognitionAPI) {
  voiceSupportNote.textContent = "Voice input needs Chrome or Edge — typing still works.";
  micBtn.disabled = true;
  wakeBtn.disabled = true;
  voiceStateLabel.textContent = "UNAVAILABLE";
} else {
  voiceSupportNote.textContent = "Voice ready — click the mic or say 'Hey Jarvis'.";
  recognizer = new SpeechRecognitionAPI();
  recognizer.lang = "en-US";
  recognizer.interimResults = true;
  recognizer.continuous = false;

  recognizer.onstart = () => {
    micActive = true;
    micBtn.classList.add("listening");
    micStateLabel.textContent = "ON";
    micStateLabel.classList.add("on");
    setOrbState("listening");
    startAudioVisualizer();
  };

  recognizer.onresult = (event) => {
    let interim = "", final = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) final += transcript;
      else interim += transcript;
    }
    liveTranscript.textContent = final || interim;

    if (final) {
      const cleaned = wakeModeActive ? stripWakeWord(final) : final;
      if (!wakeModeActive || cleaned) {
        sendToJarvis(cleaned.trim());
      }
    }
  };

  recognizer.onerror = (e) => {
    console.warn("SpeechRecognition error:", e.error);
  };

  recognizer.onend = () => {
    micActive = false;
    micBtn.classList.remove("listening");
    micStateLabel.textContent = "OFF";
    micStateLabel.classList.remove("on");
    stopAudioVisualizer();
    if (orb.classList.contains("listening")) setOrbState("idle");

    // In always-listening wake-word mode, immediately restart.
    if (wakeModeActive) {
      try { recognizer.start(); } catch (_) { /* already starting */ }
    }
  };
}

function stripWakeWord(text) {
  let lower = text.toLowerCase().trim();
  for (const phrase of WAKE_PHRASES) {
    if (lower.startsWith(phrase)) {
      return text.slice(phrase.length).replace(/^[,:]?\s*/, "");
    }
  }
  return wakeModeActive ? "" : text; // ignore utterances without the wake word while in wake mode
}

// Push-to-talk mic button: single utterance
micBtn.addEventListener("click", () => {
  if (!recognizer) return;
  if (wakeModeActive) { toggleWakeMode(); } // exit wake mode if active
  if (micActive) {
    recognizer.stop();
  } else {
    liveTranscript.textContent = "";
    try { recognizer.start(); } catch (_) { /* already running */ }
  }
});

// "Hey Jarvis" continuous wake-word mode
function toggleWakeMode() {
  if (!recognizer) return;
  wakeModeActive = !wakeModeActive;
  wakeBtn.classList.toggle("active", wakeModeActive);
  wakeStateLabel.textContent = wakeModeActive ? "ON" : "OFF";
  wakeStateLabel.classList.toggle("on", wakeModeActive);

  if (wakeModeActive) {
    recognizer.continuous = true;
    try { recognizer.start(); } catch (_) {}
  } else {
    recognizer.continuous = false;
    recognizer.stop();
  }
}
wakeBtn.addEventListener("click", toggleWakeMode);

// ---------------------------------------------------------------
// Clock
// ---------------------------------------------------------------
function tickClock() {
  const now = new Date();
  document.getElementById("clock").textContent = now.toLocaleTimeString();
  document.getElementById("dateStr").textContent = now.toLocaleDateString(undefined, {
    weekday: "short", month: "short", day: "numeric",
  });
}
setInterval(tickClock, 1000);
tickClock();

// ---------------------------------------------------------------
// System monitor polling
// ---------------------------------------------------------------
const RING_CIRC = 2 * Math.PI * 34; // r=34

function setRing(el, percent) {
  const offset = RING_CIRC - (Math.min(100, Math.max(0, percent)) / 100) * RING_CIRC;
  el.style.strokeDashoffset = offset;
}

async function pollSystem() {
  try {
    const res = await fetch("/api/system/snapshot");
    const data = await res.json();

    document.getElementById("cpuVal").textContent = `${Math.round(data.cpu.percent)}%`;
    setRing(document.getElementById("cpuRing"), data.cpu.percent);

    document.getElementById("memVal").textContent = `${Math.round(data.memory.percent)}%`;
    setRing(document.getElementById("memRing"), data.memory.percent);

    const disk = data.disk && data.disk[0];
    document.getElementById("diskVal").textContent = disk ? `${Math.round(disk.percent)}%` : "--";
    setRing(document.getElementById("diskRing"), disk ? disk.percent : 0);

    document.getElementById("battVal").textContent = data.battery ? `${data.battery.percent}%` : "N/A";
    document.getElementById("battFooter").textContent = data.battery ? `BATTERY ${data.battery.percent}%` : "BATTERY N/A";
    document.getElementById("netSent").textContent = data.network.bytes_sent;
    document.getElementById("netRecv").textContent = data.network.bytes_recv;

    document.getElementById("connStatus").textContent = "Online";
  } catch (err) {
    document.getElementById("connStatus").textContent = "Offline";
  }
}
setInterval(pollSystem, 3000);
pollSystem();

// ---------------------------------------------------------------
// Weather widget
// ---------------------------------------------------------------
document.getElementById("weatherForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const city = document.getElementById("weatherCity").value.trim();
  const box = document.getElementById("weatherResult");
  if (!city) return;
  box.textContent = "Fetching…";
  try {
    const res = await fetch(`/api/info/weather?city=${encodeURIComponent(city)}`);
    const data = await res.json();
    if (data.error) {
      box.textContent = data.error;
    } else {
      box.innerHTML = `<b>${data.city}</b>: ${data.temp_c}°C, ${data.description}<br>Feels like ${data.feels_like_c}°C · Humidity ${data.humidity}%`;
    }
  } catch (err) {
    box.textContent = "Weather lookup failed.";
  }
});

// ---------------------------------------------------------------
// Web search widget
// ---------------------------------------------------------------
document.getElementById("searchForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = document.getElementById("searchQuery").value.trim();
  const list = document.getElementById("searchResults");
  if (!q) return;
  list.innerHTML = "<li>Searching…</li>";
  try {
    const res = await fetch(`/api/info/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    list.innerHTML = "";
    (data.results || []).forEach((r) => {
      const li = document.createElement("li");
      li.innerHTML = `<a href="${r.url}" target="_blank" rel="noopener">${r.title}</a>`;
      list.appendChild(li);
    });
    if (!data.results || !data.results.length) list.innerHTML = "<li>No results.</li>";
  } catch (err) {
    list.innerHTML = "<li>Search failed.</li>";
  }
});

// ---------------------------------------------------------------
// IoT widget
// ---------------------------------------------------------------
document.querySelectorAll('#iotList input[type="checkbox"]').forEach((input) => {
  input.addEventListener("change", async () => {
    const device = input.dataset.device;
    const state = input.checked ? "on" : "off";
    try {
      await fetch("/api/iot/set", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: device, state }),
      });
    } catch (err) {
      console.warn("IoT set failed", err);
    }
  });
});

// ---------------------------------------------------------------
// Reminders widget
// ---------------------------------------------------------------
async function loadReminders() {
  const list = document.getElementById("reminderList");
  try {
    const res = await fetch("/api/automation/reminders");
    const data = await res.json();
    list.innerHTML = "";
    (data.reminders || []).forEach((r) => {
      const li = document.createElement("li");
      if (r.status === "done") li.classList.add("done");
      li.innerHTML = `<input type="checkbox" ${r.status === "done" ? "checked disabled" : ""} data-id="${r.id}"/> ${r.title}`;
      list.appendChild(li);
    });
  } catch (err) {
    console.warn("loadReminders failed", err);
  }
}

document.getElementById("reminderForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("reminderInput");
  const title = input.value.trim();
  if (!title) return;
  input.value = "";
  await fetch("/api/automation/reminders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  loadReminders();
});

document.getElementById("reminderList").addEventListener("change", async (e) => {
  if (e.target.matches('input[type="checkbox"]')) {
    const id = e.target.dataset.id;
    await fetch(`/api/automation/reminders/${id}/complete`, { method: "POST" });
    loadReminders();
  }
});

loadReminders();
setInterval(loadReminders, 15000);

// ---------------------------------------------------------------
// Security / login modal
// ---------------------------------------------------------------
const lockBtn = document.getElementById("lockBtn");
const lockLabel = document.getElementById("lockLabel");
const loginModal = document.getElementById("loginModal");
const loginForm = document.getElementById("loginForm");
const loginError = document.getElementById("loginError");
const modSecurityDot = document.getElementById("modSecurityDot");

function refreshLockUI() {
  const unlocked = !!authToken;
  lockBtn.classList.toggle("unlocked", unlocked);
  lockLabel.textContent = unlocked ? "Unlocked" : "Locked";
  modSecurityDot.classList.toggle("on", unlocked);
}
refreshLockUI();

lockBtn.addEventListener("click", () => {
  if (authToken) {
    authToken = null;
    localStorage.removeItem("jarvis_token");
    refreshLockUI();
  } else {
    loginModal.classList.remove("hidden");
  }
});

document.getElementById("loginCancel").addEventListener("click", () => {
  loginModal.classList.add("hidden");
  loginError.textContent = "";
});

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const password = document.getElementById("loginPassword").value;
  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    const data = await res.json();
    if (data.token) {
      authToken = data.token;
      localStorage.setItem("jarvis_token", authToken);
      loginModal.classList.add("hidden");
      loginError.textContent = "";
      document.getElementById("loginPassword").value = "";
      refreshLockUI();
    } else {
      loginError.textContent = data.error || "Invalid credentials.";
    }
  } catch (err) {
    loginError.textContent = "Could not reach the server.";
  }
});

// ---------------------------------------------------------------
// Boot message
// ---------------------------------------------------------------
appendMessage("jarvis", "Systems online. Click the mic, say &ldquo;Hey Jarvis&rdquo;, or type below.");
document.addEventListener("DOMContentLoaded", () => {

    /* =========================================================
       FOUR SIDE REACTORS
       ========================================================= */

    const reactors = {

        red: {
            element: document.querySelector(".side-orb-left"),
            name: "SYSTEM",
            color: "#ff304f"
        },

        orange: {
            element: document.querySelector(".side-orb-right"),
            name: "VOICE",
            color: "#ff8c00"
        },

        gold: {
            element: document.querySelector(".arc-reactor-gold"),
            name: "ENERGY",
            color: "#ffd21c"
        },

        green: {
            element: document.querySelector(".arc-reactor-green"),
            name: "SECURITY",
            color: "#45ff64"
        }

    };


    /* =========================================================
       INITIALIZE
       ========================================================= */

    Object.entries(reactors).forEach(([key, reactor]) => {

        if (!reactor.element) return;

        reactor.element.dataset.reactor = key;

        reactor.element.style.setProperty(
            "--reactor-color",
            reactor.color
        );

        reactor.element.style.setProperty(
            "--reactor-glow",
            reactor.color
        );

        /* Click event */
        reactor.element.addEventListener("click", () => {
            activateReactor(key);
        });

        /* Mouse enter */
        reactor.element.addEventListener("mouseenter", () => {
            reactor.element.classList.add("reactor-active");
        });

        /* Mouse leave */
        reactor.element.addEventListener("mouseleave", () => {
            reactor.element.classList.remove("reactor-active");
        });

    });


    /* =========================================================
       ACTIVATE REACTOR
       ========================================================= */

    function activateReactor(name) {

        Object.entries(reactors).forEach(([key, reactor]) => {

            if (!reactor.element) return;

            if (key === name) {

                reactor.element.classList.add("reactor-selected");

                reactor.element.style.setProperty(
                    "--reactor-intensity",
                    "1"
                );

            } else {

                reactor.element.classList.remove(
                    "reactor-selected"
                );

                reactor.element.style.setProperty(
                    "--reactor-intensity",
                    "0.45"
                );

            }

        });

        console.log(`${reactors[name].name} reactor activated`);
    }


    /* =========================================================
       RANDOM ENERGY PULSE
       ========================================================= */

    function randomPulse() {

        const keys = Object.keys(reactors);

        const randomKey =
            keys[Math.floor(Math.random() * keys.length)];

        const reactor = reactors[randomKey];

        if (!reactor.element) return;

        reactor.element.classList.add("energy-pulse");

        setTimeout(() => {

            reactor.element.classList.remove(
                "energy-pulse"
            );

        }, 900);

    }


    /* =========================================================
       PERIODIC ENERGY ACTIVITY
       ========================================================= */

    setInterval(() => {

        randomPulse();

    }, 3000);


    /* =========================================================
       SYSTEM STATUS
       ========================================================= */

    function updateReactorStatus() {

        /* RED - SYSTEM */
        const cpu = document.getElementById("sideCpu");

        if (cpu) {

            const value =
                Math.floor(Math.random() * 30) + 20;

            cpu.textContent = value + "%";

        }


        /* ORANGE - VOICE */
        const voice = document.getElementById(
            "voiceStatus"
        );

        if (voice) {

            voice.textContent = "READY";

        }


        /* GOLD - POWER */
        const power = document.getElementById(
            "powerValue"
        );

        if (power) {

            const value =
                Math.floor(Math.random() * 10) + 90;

            power.textContent =
                value + "%";

        }


        /* GREEN - SECURITY */
        const security = document.getElementById(
            "securityValue"
        );

        if (security) {

            security.textContent = "ACTIVE";

        }

    }


    /* Update status every 2 seconds */

    updateReactorStatus();

    setInterval(
        updateReactorStatus,
        2000
    );


    /* =========================================================
       START WITH ALL FOUR ACTIVE
       ========================================================= */

    Object.values(reactors).forEach(reactor => {

        if (!reactor.element) return;

        reactor.element.classList.add(
            "reactor-active"
        );

    });

});