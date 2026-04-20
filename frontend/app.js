// ── State ──
let currentStream = null;
let facingMode = "environment"; // rear camera by default
let capturedBlob = null;
let cardCount = 0;

// ── DOM refs ──
const homeView = document.getElementById("home-view");
const cameraView = document.getElementById("camera-view");
const previewView = document.getElementById("preview-view");
const errorView = document.getElementById("error-view");

const video = document.getElementById("camera-feed");
const overlayCanvas = document.getElementById("overlay-canvas");
const overlayCtx = overlayCanvas.getContext("2d");

const previewCanvas = document.getElementById("preview-canvas");
const previewCtx = previewCanvas.getContext("2d");

const startScanBtn = document.getElementById("start-scan-btn");
const closeCameraBtn = document.getElementById("close-camera-btn");
const captureBtn = document.getElementById("capture-btn");
const switchCameraBtn = document.getElementById("switch-camera-btn");
const retakeBtn = document.getElementById("retake-btn");
const sendBtn = document.getElementById("send-btn");
const retryBtn = document.getElementById("retry-btn");
const backHomeErrBtn = document.getElementById("back-home-err-btn");

const resolutionBadge = document.getElementById("resolution-badge");
const flashOverlay = document.getElementById("flash-overlay");
const errorMessage = document.getElementById("error-message");

const cardsBody = document.getElementById("cards-body");
const emptyState = document.getElementById("empty-state");
const cardsTable = document.getElementById("cards-table");
const cardCountBadge = document.getElementById("card-count");

// ── MTG card aspect ratio (standard: 63mm × 88mm) ──
const CARD_ASPECT = 63 / 88;

// ── View management ──
function showView(view) {
  [homeView, cameraView, previewView, errorView].forEach((v) =>
    v.classList.remove("active")
  );
  view.classList.add("active");

  // If moving to the home view, completely stop the camera to save battery
  if (view === homeView && currentStream) {
    stopCamera();
  }
}

// ── Table Management ──
window.dropRow = function (button) {
  button.closest("tr").remove();
  cardCount--;
  updateTableState();
};

function updateTableState() {
  cardCountBadge.textContent = cardCount;
  if (cardCount === 0) {
    emptyState.style.display = "block";
    cardsTable.style.display = "none";
  } else {
    emptyState.style.display = "none";
    cardsTable.style.display = "table";
  }
}

function addCardRow(name = "", number = "", set = "", language = "EN", isFoil = false, condition = "NM") {
  const tr = document.createElement("tr");

  tr.innerHTML = `
    <td><input type="text" value="${name}" placeholder="Name"></td>
    <td><input type="number" value="${number}" placeholder="#"></td>
    <td><input type="text" value="${set}" placeholder="Set"></td>
    <td>
      <select>
        <option value="EN" ${language === 'EN' ? 'selected' : ''}>English</option>
        <option value="JP" ${language === 'JP' ? 'selected' : ''}>Japanese</option>
        <option value="FR" ${language === 'FR' ? 'selected' : ''}>French</option>
        <option value="DE" ${language === 'DE' ? 'selected' : ''}>German</option>
        <option value="IT" ${language === 'IT' ? 'selected' : ''}>Italian</option>
        <option value="ES" ${language === 'ES' ? 'selected' : ''}>Spanish</option>
        <option value="PT" ${language === 'PT' ? 'selected' : ''}>Portuguese</option>
        <option value="RU" ${language === 'RU' ? 'selected' : ''}>Russian</option>
        <option value="KO" ${language === 'KO' ? 'selected' : ''}>Korean</option>
        <option value="ZH-S" ${language === 'ZH-S' ? 'selected' : ''}>Simp. Chinese</option>
        <option value="ZH-T" ${language === 'ZH-T' ? 'selected' : ''}>Trad. Chinese</option>
      </select>
    </td>
    <td>
      <label class="switch">
        <input type="checkbox" ${isFoil ? 'checked' : ''}>
        <span class="slider"></span>
      </label>
    </td>
    <td>
      <select>
        <option value="NM" ${condition === 'NM' ? 'selected' : ''}>NM</option>
        <option value="SP" ${condition === 'SP' ? 'selected' : ''}>SP</option>
        <option value="MP" ${condition === 'MP' ? 'selected' : ''}>MP</option>
        <option value="HP" ${condition === 'HP' ? 'selected' : ''}>HP</option>
        <option value="D" ${condition === 'D' ? 'selected' : ''}>D</option>
      </select>
    </td>
    <td>
      <button class="btn-danger" onclick="dropRow(this)" title="Drop">
        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
        Drop
      </button>
    </td>
  `;

  cardsBody.prepend(tr);
  cardCount++;
  updateTableState();
  return tr;
}

// ── Camera Management ──
function stopCamera() {
  if (currentStream) {
    currentStream.getTracks().forEach((t) => t.stop());
    currentStream = null;
  }
  if (overlayRAF) {
    cancelAnimationFrame(overlayRAF);
    overlayRAF = null;
  }
}

async function startCamera() {
  stopCamera();

  try {
    const constraints = {
      video: {
        facingMode: facingMode,
        width: { ideal: 1920 },
        height: { ideal: 1080 },
      },
      audio: false,
    };

    currentStream = await navigator.mediaDevices.getUserMedia(constraints);
    video.srcObject = currentStream;
    await video.play();

    showView(cameraView);
    startOverlay();
  } catch (err) {
    console.error("Camera error:", err);

    if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
      errorMessage.textContent = "Camera permission was denied. Please allow access in your browser settings and try again.";
    } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
      errorMessage.textContent = "No camera found on this device. Please connect a camera and try again.";
    } else {
      errorMessage.textContent = `Camera error: ${err.message}`;
    }
    showView(errorView);
  }
}

let overlayRAF = null;
function startOverlay() {
  if (overlayRAF) cancelAnimationFrame(overlayRAF);

  function draw() {
    const w = overlayCanvas.clientWidth;
    const h = overlayCanvas.clientHeight;

    if (overlayCanvas.width !== w || overlayCanvas.height !== h) {
      overlayCanvas.width = w;
      overlayCanvas.height = h;
    }

    overlayCtx.clearRect(0, 0, w, h);

    const margin = 0.15;
    const availW = w * (1 - 2 * margin);
    const availH = h * (1 - 2 * margin);

    let rectW, rectH;
    if (availW / availH < CARD_ASPECT) {
      rectW = availW;
      rectH = rectW / CARD_ASPECT;
    } else {
      rectH = availH;
      rectW = rectH * CARD_ASPECT;
    }

    const rx = (w - rectW) / 2;
    const ry = (h - rectH) / 2;
    const cornerRadius = 12;

    overlayCtx.fillStyle = "rgba(0, 0, 0, 0.45)";
    overlayCtx.fillRect(0, 0, w, h);

    overlayCtx.save();
    overlayCtx.globalCompositeOperation = "destination-out";
    roundRect(overlayCtx, rx, ry, rectW, rectH, cornerRadius);
    overlayCtx.fill();
    overlayCtx.restore();

    overlayCtx.strokeStyle = "rgba(255, 255, 255, 0.6)";
    overlayCtx.lineWidth = 2;
    roundRect(overlayCtx, rx, ry, rectW, rectH, cornerRadius);
    overlayCtx.stroke();

    const accentLen = 24;
    const accentWidth = 3;
    overlayCtx.strokeStyle = "#3b82f6";
    overlayCtx.lineWidth = accentWidth;
    overlayCtx.lineCap = "round";

    drawCorner(overlayCtx, rx, ry, accentLen, 1, 1);
    drawCorner(overlayCtx, rx + rectW, ry, accentLen, -1, 1);
    drawCorner(overlayCtx, rx, ry + rectH, accentLen, 1, -1);
    drawCorner(overlayCtx, rx + rectW, ry + rectH, accentLen, -1, -1);

    overlayRAF = requestAnimationFrame(draw);
  }

  draw();
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.arcTo(x + w, y, x + w, y + r, r);
  ctx.lineTo(x + w, y + h - r);
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
  ctx.lineTo(x + r, y + h);
  ctx.arcTo(x, y + h, x, y + h - r, r);
  ctx.lineTo(x, y + r);
  ctx.arcTo(x, y, x + r, y, r);
  ctx.closePath();
}

function drawCorner(ctx, x, y, len, dx, dy) {
  ctx.beginPath();
  ctx.moveTo(x, y + dy * len);
  ctx.lineTo(x, y);
  ctx.lineTo(x + dx * len, y);
  ctx.stroke();
}

// ── Capture ──
function capturePhoto() {
  if (!video.videoWidth) return;

  flashOverlay.classList.add("flash");
  setTimeout(() => flashOverlay.classList.remove("flash"), 150);

  const displayW = overlayCanvas.clientWidth;
  const displayH = overlayCanvas.clientHeight;
  const margin = 0.15;
  const availW = displayW * (1 - 2 * margin);
  const availH = displayH * (1 - 2 * margin);

  let rectW, rectH;
  if (availW / availH < CARD_ASPECT) {
    rectW = availW;
    rectH = rectW / CARD_ASPECT;
  } else {
    rectH = availH;
    rectW = rectH * CARD_ASPECT;
  }

  const rx = (displayW - rectW) / 2;
  const ry = (displayH - rectH) / 2;

  const videoAspect = video.videoWidth / video.videoHeight;
  const displayAspect = displayW / displayH;
  let scaleX, scaleY, offsetX, offsetY;

  if (videoAspect > displayAspect) {
    scaleY = video.videoHeight / displayH;
    scaleX = scaleY;
    offsetX = (video.videoWidth - displayW * scaleX) / 2;
    offsetY = 0;
  } else {
    scaleX = video.videoWidth / displayW;
    scaleY = scaleX;
    offsetX = 0;
    offsetY = (video.videoHeight - displayH * scaleY) / 2;
  }

  const cropX = Math.round(rx * scaleX + offsetX);
  const cropY = Math.round(ry * scaleY + offsetY);
  const cropW = Math.round(rectW * scaleX);
  const cropH = Math.round(rectH * scaleY);

  previewCanvas.width = cropW;
  previewCanvas.height = cropH;
  previewCtx.drawImage(video, cropX, cropY, cropW, cropH, 0, 0, cropW, cropH);

  previewCanvas.toBlob((blob) => {
    capturedBlob = blob;
    showView(previewView);
  }, "image/jpeg", 0.92);
}

// ── Send to server ──
async function sendPhoto() {
  if (!capturedBlob) return;

  sendBtn.classList.add("sending");
  sendBtn.innerHTML = '<span class="spinner"></span> Sending…';

  try {
    const formData = new FormData();
    formData.append("image", capturedBlob, "card.jpg");

    const response = await fetch("/api/scan", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    const result = await response.json();
    console.log("Server response:", result);

    // Add a new row to the table for each card found in the crop (normally 1)
    const count = result.cards_found || 1;
    for (let i = 0; i < count; i++) {
      const rowElement = addCardRow(`Detecting...`);

      // Start polling for the result using the frame_id
      if (result.frame_id) {
        pollForResult(result.frame_id, rowElement);
      }
    }

    // Return to camera view for the next scan
    capturedBlob = null;
    showView(cameraView);

  } catch (err) {
    console.error("Send error:", err);
    alert(`Failed to send: ${err.message}`);
  } finally {
    sendBtn.classList.remove("sending");
    sendBtn.innerHTML = '<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M12 5l7 7-7 7"/></svg> Send';
  }
}

function pollForResult(frameId, rowElement) {
  // Check every 1 second for inference result
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/result/${frameId}`);
      if (res.status === 200) {
        clearInterval(interval);
        const data = await res.json();

        // Update the row with the actual data from the AI
        const inputs = rowElement.querySelectorAll('input[type="text"], input[type="number"]');
        if (inputs.length >= 3) {
          inputs[0].value = data.card_name || "";
          inputs[1].value = data.card_number || "";
          inputs[2].value = data.card_set || "";
        }

        console.log("Card successfully detected:", data);
      } else if (res.status === 202) {
        // Still processing, continue polling...
      } else {
        clearInterval(interval);
        console.error("Error polling result:", res.status);
      }
    } catch (err) {
      clearInterval(interval);
      console.error("Polling fetch error:", err);
    }
  }, 1000);
}

// ── Event Listeners ──
startScanBtn.addEventListener("click", startCamera);
closeCameraBtn.addEventListener("click", () => showView(homeView));
captureBtn.addEventListener("click", capturePhoto);

switchCameraBtn.addEventListener("click", () => {
  facingMode = facingMode === "environment" ? "user" : "environment";
  startCamera();
});

retakeBtn.addEventListener("click", () => {
  capturedBlob = null;
  showView(cameraView);
});

sendBtn.addEventListener("click", sendPhoto);
retryBtn.addEventListener("click", startCamera);
backHomeErrBtn.addEventListener("click", () => showView(homeView));

// ── Init ──
updateTableState(); // Start on home view
