import { useState, useEffect, useRef } from 'react';
import { Camera, RefreshCw, X, Send, Trash2 } from 'lucide-react';
import { api } from '../services/api';

const CARD_ASPECT = 63 / 88;

export default function ScannerTab() {
  const [stream, setStream] = useState(null);
  const [facingMode, setFacingMode] = useState('environment');
  const [capturedBlob, setCapturedBlob] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isSending, setIsSending] = useState(false);
  
  const [pendingCards, setPendingCards] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [toast, setToast] = useState(null); // { message: string, type: 'success' | 'error' }

  const videoRef = useRef(null);
  const overlayRef = useRef(null);
  const previewRef = useRef(null);
  const rafRef = useRef(null);

  // ── Camera Initialization ──
  const startCamera = async () => {
    stopCamera();
    try {
      const constraints = { video: { facingMode, width: { ideal: 1920 }, height: { ideal: 1080 } }, audio: false };
      const s = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(s);
      setErrorMsg(null);
    } catch (err) {
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setErrorMsg("Camera permission denied. Please allow access in browser settings.");
      } else {
        setErrorMsg(`Camera error: ${err.message}`);
      }
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      setStream(null);
    }
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
  };

  useEffect(() => {
    if (stream && videoRef.current) {
      videoRef.current.srcObject = stream;
      videoRef.current.play().then(startOverlay);
    }
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream]);

  // Clean wipe on unmount
  useEffect(() => {
    return () => stopCamera();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── HUD Overlay Render Loop ──
  const startOverlay = () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    
    function draw() {
      const cvs = overlayRef.current;
      if (!cvs) return;
      const ctx = cvs.getContext('2d');
      const w = cvs.clientWidth;
      const h = cvs.clientHeight;

      if (cvs.width !== w || cvs.height !== h) {
        cvs.width = w; cvs.height = h;
      }
      ctx.clearRect(0, 0, w, h);

      const margin = 0.15;
      const availW = w * (1 - 2 * margin);
      const availH = h * (1 - 2 * margin);

      let rectW, rectH;
      if (availW / availH < CARD_ASPECT) {
        rectW = availW; rectH = rectW / CARD_ASPECT;
      } else {
        rectH = availH; rectW = rectH * CARD_ASPECT;
      }

      const rx = (w - rectW) / 2;
      const ry = (h - rectH) / 2;
      const r = 12;

      ctx.fillStyle = "rgba(0, 0, 0, 0.45)";
      ctx.fillRect(0, 0, w, h);

      ctx.save();
      ctx.globalCompositeOperation = "destination-out";
      ctx.beginPath();
      ctx.moveTo(rx + r, ry);
      ctx.lineTo(rx + rectW - r, ry); ctx.arcTo(rx + rectW, ry, rx + rectW, ry + r, r);
      ctx.lineTo(rx + rectW, ry + rectH - r); ctx.arcTo(rx + rectW, ry + rectH, rx + rectW - r, ry + rectH, r);
      ctx.lineTo(rx + r, ry + rectH); ctx.arcTo(rx, ry + rectH, rx, ry + rectH - r, r);
      ctx.lineTo(rx, ry + r); ctx.arcTo(rx, ry, rx + r, ry, r);
      ctx.closePath();
      ctx.fill();
      ctx.restore();

      ctx.strokeStyle = "rgba(255, 255, 255, 0.6)"; ctx.lineWidth = 2;
      ctx.stroke();

      const accentLen = 24; const accentWidth = 3;
      ctx.strokeStyle = "#3b82f6"; ctx.lineWidth = accentWidth; ctx.lineCap = "round";
      
      const drawC = (x, y, dx, dy) => {
        ctx.beginPath(); ctx.moveTo(x, y + dy * accentLen); ctx.lineTo(x, y); ctx.lineTo(x + dx * accentLen, y); ctx.stroke();
      };
      
      drawC(rx, ry, 1, 1);
      drawC(rx + rectW, ry, -1, 1);
      drawC(rx, ry + rectH, 1, -1);
      drawC(rx + rectW, ry + rectH, -1, -1);

      rafRef.current = requestAnimationFrame(draw);
    }
    draw();
  };

  // ── Capture Action ──
  const capturePhoto = () => {
    const video = videoRef.current;
    const overlay = overlayRef.current;
    if (!video || !video.videoWidth || !overlay) return;

    const displayW = overlay.clientWidth;
    const displayH = overlay.clientHeight;
    const margin = 0.15;
    const availW = displayW * (1 - 2 * margin);
    const availH = displayH * (1 - 2 * margin);

    let rectW, rectH;
    if (availW / availH < CARD_ASPECT) {
      rectW = availW; rectH = rectW / CARD_ASPECT;
    } else {
      rectH = availH; rectW = rectH * CARD_ASPECT;
    }

    const rx = (displayW - rectW) / 2;
    const ry = (displayH - rectH) / 2;
    const videoAspect = video.videoWidth / video.videoHeight;
    const displayAspect = displayW / displayH;
    
    let scaleX, scaleY, offsetX, offsetY;
    if (videoAspect > displayAspect) {
      scaleY = video.videoHeight / displayH; scaleX = scaleY;
      offsetX = (video.videoWidth - displayW * scaleX) / 2; offsetY = 0;
    } else {
      scaleX = video.videoWidth / displayW; scaleY = scaleX;
      offsetX = 0; offsetY = (video.videoHeight - displayH * scaleY) / 2;
    }

    const cropX = Math.round(rx * scaleX + offsetX);
    const cropY = Math.round(ry * scaleY + offsetY);
    const cropW = Math.round(rectW * scaleX);
    const cropH = Math.round(rectH * scaleY);

    const canvas = document.createElement('canvas');
    canvas.width = cropW; canvas.height = cropH;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, cropX, cropY, cropW, cropH, 0, 0, cropW, cropH);

    canvas.toBlob(blob => {
      setCapturedBlob(blob);
      setTimeout(() => {
        if(previewRef.current) {
          previewRef.current.width = cropW; previewRef.current.height = cropH;
          previewRef.current.getContext('2d').drawImage(canvas, 0, 0);
        }
      }, 50);
    }, 'image/jpeg', 0.92);
  };

  // ── Inference Handling ──
  const sendPhoto = async () => {
    if (!capturedBlob || isSending) return;
    setIsSending(true);
    
    try {
      const result = await api.scanPhoto(capturedBlob);
      const frameId = result.frame_id;
      
      const newCardState = { 
        id: Math.random().toString(), 
        frameId, 
        name: 'Detecting...', number: '', set: '', language: 'EN', condition: 'NM', isFoil: false,
        uuid: null 
      };
      
      setPendingCards(prev => [newCardState, ...prev]);
      setCapturedBlob(null); // Return to camera instantly
      
      // Background poll
      const interval = setInterval(async () => {
        try {
          const data = await api.pollResult(frameId);
          if (data) {
            clearInterval(interval);
            setPendingCards(current => current.map(c => c.frameId === frameId ? {
              ...c, 
              name: data.card_name, 
              number: data.card_number, 
              set: data.card_set, 
              language: data.card_language || c.language,
              uuid: data.id
            } : c));
            setToast({ message: `Detected: ${data.card_name}`, type: 'success' });
            setTimeout(() => setToast(null), 3000);
          }
        } catch(e) { clearInterval(interval); }
      }, 1000);

    } catch (e) {
      alert(`Send failed: ${e.message}`);
    } finally {
      setIsSending(false);
    }
  };

  // ── Database Handling ──
  const uploadToDB = async () => {
    const validUploads = pendingCards.filter(c => c.uuid !== null).map(c => ({
      id: c.uuid,
      is_foil: c.isFoil,
      card_condition: c.condition,
      quantity: 1
    }));
    
    if (!validUploads.length) {
      alert("No valid cards finished detecting yet.");
      return;
    }

    setIsUploading(true);
    try {
      await api.addCardsToCollection(validUploads);
      setToast({ message: "Cards successfully synced!", type: 'success' });
      setTimeout(() => setToast(null), 3000);
      setPendingCards([]);
    } catch(e) {
      setToast({ message: e.message, type: 'error' });
      setTimeout(() => setToast(null), 4000);
    } finally {
      setIsUploading(false);
    }
  };

  // State Views
  if (errorMsg) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center">
        <h2 className="text-xl font-bold text-red-400 mb-2">Camera Error</h2>
        <p className="text-slate-400 mb-6">{errorMsg}</p>
        <button onClick={startCamera} className="btn-primary">Try Again</button>
      </div>
    );
  }

  if (stream || capturedBlob) {
    return (
      <div className="w-full h-full absolute inset-0 z-40 bg-black flex flex-col">
        {/* Active Camera View */}
        <div className={capturedBlob ? 'hidden' : 'relative flex-1 overflow-hidden flex flex-col'}>
          <video ref={videoRef} autoPlay playsInline muted className="absolute inset-0 w-full h-full object-cover" />
          <canvas ref={overlayRef} className="absolute inset-0 w-full h-full pointer-events-none" />
          
          <div className="absolute top-4 left-4 right-4 flex justify-between z-10">
            <button onClick={stopCamera} className="w-10 h-10 bg-black/40 backdrop-blur rounded-full flex items-center justify-center text-white border border-white/10 active:scale-95"><X size={20}/></button>
            <button onClick={() => { setFacingMode(f => f === 'environment' ? 'user' : 'environment'); startCamera(); }} className="w-10 h-10 bg-black/40 backdrop-blur rounded-full flex items-center justify-center text-white border border-white/10 active:scale-95"><RefreshCw size={20}/></button>
          </div>
          
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-black/60 backdrop-blur px-5 py-2 rounded-full border border-white/10 text-sm font-medium text-white whitespace-nowrap z-10">
            Place the card inside the frame
          </div>
          
          {/* Spacer pushing capture button to bottom */}
          <div className="flex-1 pointer-events-none"></div>
          
          <div className="h-28 bg-gradient-to-t from-black/80 to-transparent flex items-center justify-center shrink-0 w-full z-10 relative">
             <button onClick={capturePhoto} className="w-16 h-16 rounded-full border-[3px] border-white flex items-center justify-center active:scale-95 transition-transform"><div className="w-[52px] h-[52px] bg-white rounded-full active:bg-blue-500"></div></button>
          </div>
        </div>

        {/* Captured Preview View */}
        {capturedBlob && (
          <div className="w-full h-full flex flex-col bg-bg absolute inset-0 z-50">
            <div className="flex-1 flex items-center justify-center p-6 overflow-hidden">
              <canvas ref={previewRef} className="max-w-full max-h-full rounded-2xl shadow-2xl border border-white/10" />
            </div>
            <div className="flex justify-center gap-4 p-6 pb-[max(1.5rem,env(safe-area-inset-bottom))] bg-black/40">
               <button onClick={() => setCapturedBlob(null)} className="btn-secondary w-full max-w-[160px]">Retake</button>
               <button onClick={sendPhoto} disabled={isSending} className="btn-primary w-full max-w-[160px]">
                 {isSending ? <div className="spinner"></div> : <><Send size={18} /> Send</>}
               </button>
            </div>
          </div>
        )}

        {/* Non-blocking Toast Notification */}
        {toast && (
          <div className="fixed top-20 left-1/2 -translate-x-1/2 z-[100] animate-in fade-in slide-in-from-top-4 duration-300">
            <div className={`px-6 py-3 rounded-full shadow-2xl border backdrop-blur-md flex items-center gap-3 ${
              toast.type === 'success' ? 'bg-green-500/20 border-green-500/50 text-green-400' : 'bg-red-500/20 border-red-500/50 text-red-400'
            }`}>
              <div className="w-2 h-2 rounded-full bg-current animate-pulse"></div>
              <span className="font-semibold text-sm">{toast.message}</span>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col overflow-y-auto p-4 md:p-6 pb-[env(safe-area-inset-bottom)]">
      <div className="max-w-4xl mx-auto w-full">
         <div className="mb-6">
           <button onClick={startCamera} className="w-full btn-primary py-5 text-lg shadow-[0_10px_30px_rgba(59,130,246,0.3)] border border-blue-400/30">
              <Camera size={24} /> Launch Scanner View
           </button>
         </div>

         <div className="glass-panel overflow-hidden flex flex-col">
            <div className="p-5 border-b border-border flex justify-between items-center bg-black/20">
               <h2 className="font-semibold text-lg">Pending Uploads</h2>
               <span className="bg-blue-500 text-white px-2 py-0.5 rounded-full text-xs font-bold">{pendingCards.length}</span>
            </div>
            
            {pendingCards.length > 0 ? (
              <>
                <div className="overflow-x-auto">
                   <table className="w-full text-left min-w-[700px]">
                     <thead>
                       <tr className="border-b border-border bg-black/10">
                         <th className="p-4 text-xs font-medium text-slate-400">CARD</th>
                         <th className="p-4 text-xs font-medium text-slate-400">SET</th>
                         <th className="p-4 text-xs font-medium text-slate-400 w-24">LANG</th>
                         <th className="p-4 text-xs font-medium text-slate-400 w-24">FOIL</th>
                         <th className="p-4 text-xs font-medium text-slate-400 w-32">COND</th>
                         <th className="p-4 w-12"></th>
                       </tr>
                     </thead>
                     <tbody className="divide-y divide-border/50">
                       {pendingCards.map(c => (
                         <tr key={c.id}>
                           <td className="p-4 font-semibold">{c.name} <span className="text-slate-500 font-normal text-xs ml-2">{c.number}</span></td>
                           <td className="p-4 font-mono text-sm">{c.set || '-'}</td>
                           <td className="p-4 font-bold text-slate-300 text-xs">{c.language}</td>
                           <td className="p-4">
                             <input type="checkbox" checked={c.isFoil} onChange={(e) => setPendingCards(prev => prev.map(p => p.id === c.id ? {...p, isFoil: e.target.checked} : p))} className="w-4 h-4 accent-blue-500 bg-transparent" />
                           </td>
                           <td className="p-4">
                              <select value={c.condition} onChange={(e) => setPendingCards(prev => prev.map(p => p.id === c.id ? {...p, condition: e.target.value} : p))} className="bg-transparent border border-border rounded p-1 w-full text-sm">
                                <option className="bg-bg" value="NM">NM</option><option className="bg-bg" value="SP">SP</option><option className="bg-bg" value="MP">MP</option><option className="bg-bg" value="HP">HP</option>
                              </select>
                           </td>
                           <td className="p-4">
                             <button onClick={() => setPendingCards(prev => prev.filter(p => p.id !== c.id))} className="text-slate-500 hover:text-red-400"><Trash2 size={16}/></button>
                           </td>
                         </tr>
                       ))}
                     </tbody>
                   </table>
                </div>
                <div className="p-4 bg-black/20 border-t border-border flex justify-center">
                  <button onClick={uploadToDB} disabled={isUploading || pendingCards.some(c => c.uuid === null)} className="btn-primary w-full sm:w-auto">
                    {isUploading ? 'Uploading...' : 'Upload to Database'}
                  </button>
                </div>
              </>
            ) : (
              <div className="p-12 text-center text-slate-500">
                <p>No cards pending.</p>
                <p className="text-sm mt-1">Press "Launch Scanner" to digitize.</p>
              </div>
            )}
         </div>
      </div>
    </div>
  );
}
