// ── State ──
let currentStream = null;
let facingMode = "environment"; // rear camera by default
let capturedBlob = null;

// ── DOM refs ──
const cameraView = document.getElementById("camera-view");
const previewView = document.getElementById("preview-view");
const errorView = document.getElementById("error-view");

const video = document.getElementById("camera-feed");
const overlayCanvas = document.getElementById("overlay-canvas");
const overlayCtx = overlayCanvas.getContext("2d");

const previewCanvas = document.getElementById("preview-canvas");
const previewCtx = previewCanvas.getContext("2d");

const captureBtn = document.getElementById("capture-btn");
const switchCameraBtn = document.getElementById("switch-camera-btn");
const retakeBtn = document.getElementById("retake-btn");
const sendBtn = document.getElementById("send-btn");
const retryBtn = document.getElementById("retry-btn");

const resolutionBadge = document.getElementById("resolution-badge");
const guideText = document.getElementById("guide-text");
const flashOverlay = document.getElementById("flash-overlay");
const errorMessage = document.getElementById("error-message");

// ── MTG card aspect ratio (standard: 63mm × 88mm) ──
const CARD_ASPECT = 63 / 88;

// ── View management ──
function showView(view) {
  [cameraView, previewView, errorView].forEach((v) =>
    v.classList.remove("active")
  );
  view.classList.add("active");
}

// ── Camera ──
async function startCamera() {
  // Stop any existing stream
  if (currentStream) {
    currentStream.getTracks().forEach((t) => t.stop());
  }

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

    if (
      err.name === "NotAllowedError" ||
      err.name === "PermissionDeniedError"
    ) {
      errorMessage.textContent =
        "Camera permission was denied. Please allow access in your browser settings and try again.";
    } else if (
      err.name === "NotFoundError" ||
      err.name === "DevicesNotFoundError"
    ) {
      errorMessage.textContent =
        "No camera found on this device. Please connect a camera and try again.";
    } else {
      errorMessage.textContent = `Camera error: ${err.message}`;
    }
    showView(errorView);
  }
}

// ── Overlay: draw the card guide rectangle ──
let overlayRAF = null;

function startOverlay() {
  if (overlayRAF) cancelAnimationFrame(overlayRAF);

  function draw() {
    const w = overlayCanvas.clientWidth;
    const h = overlayCanvas.clientHeight;

    // Match canvas resolution to its display size
    if (overlayCanvas.width !== w || overlayCanvas.height !== h) {
      overlayCanvas.width = w;
      overlayCanvas.height = h;
    }

    overlayCtx.clearRect(0, 0, w, h);

    // Calculate card rectangle (70% of the smaller dimension)
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

    // Dim everything outside the rectangle
    overlayCtx.fillStyle = "rgba(0, 0, 0, 0.45)";
    overlayCtx.fillRect(0, 0, w, h);

    // Cut out the card area (transparent hole)
    overlayCtx.save();
    overlayCtx.globalCompositeOperation = "destination-out";
    roundRect(overlayCtx, rx, ry, rectW, rectH, cornerRadius);
    overlayCtx.fill();
    overlayCtx.restore();

    // Draw border around the card area
    overlayCtx.strokeStyle = "rgba(255, 255, 255, 0.6)";
    overlayCtx.lineWidth = 2;
    roundRect(overlayCtx, rx, ry, rectW, rectH, cornerRadius);
    overlayCtx.stroke();

    // Draw corner accents
    const accentLen = 24;
    const accentWidth = 3;
    overlayCtx.strokeStyle = "var(--accent, #3b82f6)";
    // Fallback: parse CSS variable
    overlayCtx.strokeStyle = "#3b82f6";
    overlayCtx.lineWidth = accentWidth;
    overlayCtx.lineCap = "round";

    // Top-left
    drawCorner(overlayCtx, rx, ry, accentLen, 1, 1);
    // Top-right
    drawCorner(overlayCtx, rx + rectW, ry, accentLen, -1, 1);
    // Bottom-left
    drawCorner(overlayCtx, rx, ry + rectH, accentLen, 1, -1);
    // Bottom-right
    drawCorner(overlayCtx, rx + rectW, ry + rectH, accentLen, -1, -1);

    // Update resolution badge
    if (video.videoWidth && video.videoHeight) {
      resolutionBadge.textContent = `${video.videoWidth}×${video.videoHeight}`;
    }

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

  // Flash effect
  flashOverlay.classList.add("flash");
  setTimeout(() => flashOverlay.classList.remove("flash"), 150);

  // Calculate the card rectangle in video-pixel coordinates
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

  // Map from display coordinates to actual video pixels
  // object-fit: cover means the video is scaled and cropped
  const videoAspect = video.videoWidth / video.videoHeight;
  const displayAspect = displayW / displayH;

  let scaleX, scaleY, offsetX, offsetY;

  if (videoAspect > displayAspect) {
    // Video is wider than display: height fits, width is cropped
    scaleY = video.videoHeight / displayH;
    scaleX = scaleY;
    offsetX = (video.videoWidth - displayW * scaleX) / 2;
    offsetY = 0;
  } else {
    // Video is taller than display: width fits, height is cropped
    scaleX = video.videoWidth / displayW;
    scaleY = scaleX;
    offsetX = 0;
    offsetY = (video.videoHeight - displayH * scaleY) / 2;
  }

  const cropX = Math.round(rx * scaleX + offsetX);
  const cropY = Math.round(ry * scaleY + offsetY);
  const cropW = Math.round(rectW * scaleX);
  const cropH = Math.round(rectH * scaleY);

  // Draw cropped region to preview canvas
  previewCanvas.width = cropW;
  previewCanvas.height = cropH;
  previewCtx.drawImage(
    video,
    cropX,
    cropY,
    cropW,
    cropH,
    0,
    0,
    cropW,
    cropH
  );

  // Store as blob for later sending
  previewCanvas.toBlob(
    (blob) => {
      capturedBlob = blob;
      showView(previewView);
    },
    "image/jpeg",
    0.92
  );
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

    // TODO @gruzdev-as: Handle server response (e.g. show card info, add to table)
    alert("Card sent successfully!");
  } catch (err) {
    console.error("Send error:", err);
    alert(`Failed to send: ${err.message}`);
  } finally {
    sendBtn.classList.remove("sending");
    sendBtn.innerHTML =
      '<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M12 5l7 7-7 7"/></svg> Send';
  }
}

// ── Event Listeners ──
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

// ── Init ──
startCamera();
