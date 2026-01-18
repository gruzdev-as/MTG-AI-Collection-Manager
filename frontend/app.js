function setupStream(canvasId, wsUrl) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");

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
}

setupStream("canvas", "ws://localhost/ws/stream");

ws.onopen = () => {
  console.log("WS connected");
};

ws.onclose = () => {
  console.log("WS closed");
};

ws.onerror = (err) => {
  console.error("WS error", err);
};
