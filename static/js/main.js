// ---------------------------------------------------------------
// HYBRID TEXT-TO-SPEECH
//
// Desktop/Laptop:
//     Uses Python pyttsx3 through /api/voice/speak
//
// Mobile:
//     Uses browser JavaScript speechSynthesis
// ---------------------------------------------------------------

const synth = window.speechSynthesis;

// Detect mobile/tablet
function isMobileDevice() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i
    .test(navigator.userAgent);
}

// ---------------------------------------------------------------
// Browser TTS - Mobile
// ---------------------------------------------------------------
function speakMobile(text) {
  if (!("speechSynthesis" in window)) {
    console.warn("Browser speech synthesis is not supported.");
    setOrbState("idle");
    return;
  }

  synth.cancel();

  const utter = new SpeechSynthesisUtterance(text);

  utter.rate = 1.02;
  utter.pitch = 0.9;
  utter.volume = 1;

  // Get available voices
  const voices = synth.getVoices();

  const preferred =
    voices.find(v =>
      /en-US/i.test(v.lang) &&
      /male|david|daniel|google/i.test(v.name)
    ) ||
    voices.find(v => /en-US/i.test(v.lang)) ||
    voices.find(v => /^en/i.test(v.lang));

  if (preferred) {
    utter.voice = preferred;
  }

  utter.onstart = () => {
    setOrbState("speaking");
  };

  utter.onend = () => {
    setOrbState("idle");
  };

  utter.onerror = (event) => {
    console.warn("Mobile TTS error:", event.error);
    setOrbState("idle");
  };

  synth.speak(utter);
}


// ---------------------------------------------------------------
// Python TTS - Desktop/Laptop
// ---------------------------------------------------------------
async function speakDesktop(text) {
  try {
    setOrbState("speaking");

    const response = await fetch("/api/voice/speak", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        text: text
      })
    });

    if (!response.ok) {
      throw new Error("Python TTS request failed");
    }

    const data = await response.json();

    console.log("Python TTS:", data);

    setOrbState("idle");

  } catch (error) {

    console.warn(
      "Desktop Python TTS unavailable. Falling back to browser TTS.",
      error
    );

    // Fallback
    speakMobile(text);
  }
}


// ---------------------------------------------------------------
// MAIN SPEAK FUNCTION
// ---------------------------------------------------------------
function speak(text) {

  if (!text || !text.trim()) {
    setOrbState("idle");
    return;
  }

  console.log(
    isMobileDevice()
      ? "JARVIS TTS → Mobile Browser"
      : "JARVIS TTS → Python pyttsx3"
  );

  if (isMobileDevice()) {

    // PHONE / TABLET
    speakMobile(text);

  } else {

    // LAPTOP / DESKTOP
    speakDesktop(text);

  }
}


// ---------------------------------------------------------------
// Speaker button
// ---------------------------------------------------------------
speakerBtn.addEventListener("click", () => {

  autoSpeak = !autoSpeak;

  speakerBtn.classList.toggle("active", autoSpeak);

  if (!autoSpeak) {

    // Stop browser speech
    if (synth) {
      synth.cancel();
    }

    setOrbState("idle");
  }
});


// ---------------------------------------------------------------
// Mobile browsers sometimes load voices asynchronously
// ---------------------------------------------------------------
if ("speechSynthesis" in window) {

  synth.onvoiceschanged = () => {
    const voices = synth.getVoices();

    console.log(
      "Available TTS voices:",
      voices.map(v => `${v.name} (${v.lang})`)
    );
  };

}
