import { useNavigate } from 'react-router-dom';
import { Camera, Library } from 'lucide-react';

export default function MainMenu() {
  const navigate = useNavigate();

  return (
    <div className="w-full h-full flex flex-col items-center justify-center p-6 pb-[env(safe-area-inset-bottom)] pt-[env(safe-area-inset-top)] overflow-y-auto">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold mb-3 bg-gradient-to-br from-white to-slate-400 bg-clip-text text-transparent">
            Welcome Back
          </h1>
          <p className="text-slate-400 text-lg">What would you like to do today?</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <button 
            onClick={() => navigate('/scanner')}
            className="flex flex-col items-center text-center p-10 rounded-2xl border border-blue-500/30 bg-gradient-to-br from-blue-500/10 to-blue-900/20 text-slate-100 transition-all hover:-translate-y-1 hover:border-blue-500 hover:shadow-[0_10px_40px_-10px_rgba(59,130,246,0.4)] active:translate-y-0"
          >
            <Camera size={48} className="text-blue-500 mb-6" />
            <h3 className="text-xl font-semibold mb-2">Scanner Tool</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Digitize and detect your physical cards in real-time.
            </p>
          </button>

          <button 
            onClick={() => navigate('/collection')}
            className="flex flex-col items-center text-center p-10 rounded-2xl border border-white/10 bg-white/5 text-slate-100 transition-all hover:-translate-y-1 hover:border-white/20 active:translate-y-0"
          >
            <Library size={48} className="text-slate-400 mb-6" />
            <h3 className="text-xl font-semibold mb-2">My Collection</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              View, track, and manage your inventory and stacks.
            </p>
          </button>
        </div>
      </div>
    </div>
  );
}
