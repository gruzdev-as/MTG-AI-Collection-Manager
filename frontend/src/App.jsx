import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import MainMenu from './pages/MainMenu';
import ScannerTab from './pages/ScannerTab';
import CollectionManager from './pages/CollectionManager';

function TopNav() {
  const location = useLocation();
  const navigate = useNavigate();

  // Hide nav exclusively on the absolute main menu dashboard root natively
  if (location.pathname === '/') return null;

  const titles = {
    '/scanner': 'Scanner Tool',
    '/collection': 'My Collection',
  };

  return (
    <nav className="nav-header">
      <button 
        onClick={() => navigate('/')} 
        className="w-10 h-10 flex items-center justify-center bg-transparent text-slate-100/70 hover:text-white transition-colors active:bg-white/10 rounded-full"
        title="Back to menu"
      >
        <ArrowLeft size={24} />
      </button>
      <h2 className="ml-4 text-xl font-bold text-slate-100">{titles[location.pathname] || 'MTG Scanner'}</h2>
    </nav>
  );
}

export default function App() {
  return (
    <div className="w-full h-full flex flex-col">
      <TopNav />
      <div className="flex-1 overflow-hidden relative">
        <Routes>
          <Route path="/" element={<MainMenu />} />
          <Route path="/scanner" element={<ScannerTab />} />
          <Route path="/collection" element={<CollectionManager />} />
        </Routes>
      </div>
    </div>
  );
}
