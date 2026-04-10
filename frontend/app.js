function setupStream(canvasId, wsPath) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) {
      console.error(`Canvas element with ID '${canvasId}' not found.`);
      return;
  }
  const ctx = canvas.getContext("2d");

  // Dynamically determine connection host to fix Docker LAN proxy issues
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}${wsPath}`;
  const ws = new WebSocket(wsUrl);
  ws.binaryType = "blob";

  const img = new Image();

  img.onload = () => {
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    URL.revokeObjectURL(img.src);
  };

  ws.onmessage = (event) => {
    const url = URL.createObjectURL(event.data);
    img.src = url;
  };

  // Move Event Listeners inside function envelope to fix ReferenceError scoping
  ws.onopen = () => {
    console.log("WS connected");
  };

  ws.onclose = () => {
    console.log("WS closed");
  };

  ws.onerror = (err) => {
    console.error("WS error", err);
  };
}

setupStream("canvas", "/ws/stream");
