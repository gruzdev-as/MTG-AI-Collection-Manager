import { useState, useEffect } from 'react';
import { Trash2, ChevronLeft, ChevronRight, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { api } from '../services/api';

export default function CollectionManager() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState('added_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [loading, setLoading] = useState(true);

  const ITEMS_PER_PAGE = 100;

  const loadCollection = async (pageNum, currentSortBy = sortBy, currentSortOrder = sortOrder) => {
    setLoading(true);
    try {
      const offset = (pageNum - 1) * ITEMS_PER_PAGE;
      const data = await api.getCollection(ITEMS_PER_PAGE, offset, currentSortBy, currentSortOrder);
      setItems(data.items);
      setTotal(data.total_count);
      setPage(pageNum);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSort = (key) => {
    let nextOrder = 'desc';
    if (sortBy === key && sortOrder === 'desc') {
      nextOrder = 'asc';
    }
    setSortBy(key);
    setSortOrder(nextOrder);
    loadCollection(1, key, nextOrder);
  };

  useEffect(() => {
    loadCollection(1);
  }, []);

  const handleUpdateQty = async (id, currentQty, delta) => {
    const newQty = currentQty + delta;
    if (newQty < 1) {
      handleDelete(id);
      return;
    }
    // Optimistic Update
    setItems(items.map(i => i.collection_id === id ? { ...i, quantity: newQty } : i));
    try {
      await api.updateCollectionItem(id, { quantity: newQty });
    } catch {
      loadCollection(page); // revert on fail
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to remove this stack?")) return;
    setItems(items.filter(i => i.collection_id !== id));
    try {
      await api.deleteCollectionItem(id);
      setTotal(prev => prev - 1);
    } catch {
      loadCollection(page);
    }
  };

  return (
    <div className="w-full h-full overflow-y-auto p-6 pb-[env(safe-area-inset-bottom)]">
      <div className="max-w-6xl mx-auto w-full">

        {/* Stats Dashboard */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div className="glass-panel p-6 flex flex-col">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Total Unique Cards</span>
            <span className="text-3xl font-bold text-slate-100">{items.length} (Page)</span>
          </div>
          <div className="glass-panel p-6 flex flex-col">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Total Physical Cards</span>
            <span className="text-3xl font-bold text-slate-100">{total}</span>
          </div>
        </div>

        {/* Data Table */}
        <div className="glass-panel overflow-hidden flex flex-col">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[700px]">
              <thead>
                <tr className="bg-black/20 border-b border-border">
                  <th className="p-4 text-[10px] font-medium text-slate-400 uppercase tracking-wider w-16">Coll ID</th>
                  <th className="p-4 text-[10px] font-medium text-slate-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors" onClick={() => toggleSort('card_name')}>
                    <div className="flex items-center gap-1">
                      Card Name 
                      {sortBy === 'card_name' ? (sortOrder === 'desc' ? <ArrowDown size={10} /> : <ArrowUp size={10} />) : <ArrowUpDown size={10} className="opacity-30" />}
                    </div>
                  </th>
                  <th className="p-4 text-[10px] font-medium text-slate-400 uppercase tracking-wider w-24 cursor-pointer hover:text-white" onClick={() => toggleSort('card_set')}>
                    <div className="flex items-center gap-1">
                      Set
                      {sortBy === 'card_set' ? (sortOrder === 'desc' ? <ArrowDown size={10} /> : <ArrowUp size={10} />) : <ArrowUpDown size={10} className="opacity-30" />}
                    </div>
                  </th>
                  <th className="p-4 text-[10px] font-medium text-slate-400 uppercase tracking-wider w-16">Num</th>
                  <th className="p-4 text-[10px] font-medium text-slate-400 uppercase tracking-wider w-16">Lang</th>
                  <th className="p-4 text-[10px] font-medium text-slate-400 uppercase tracking-wider w-24 cursor-pointer hover:text-white" onClick={() => toggleSort('card_rarity')}>
                    <div className="flex items-center gap-1">
                      Rarity
                      {sortBy === 'card_rarity' ? (sortOrder === 'desc' ? <ArrowDown size={10} /> : <ArrowUp size={10} />) : <ArrowUpDown size={10} className="opacity-30" />}
                    </div>
                  </th>
                  <th className="p-4 text-[10px] font-medium text-slate-400 uppercase tracking-wider w-20">Foil</th>
                  <th className="p-4 text-[10px] font-medium text-slate-400 uppercase tracking-wider w-20">Cond</th>
                  <th className="p-4 text-[10px] font-medium text-slate-400 uppercase tracking-wider w-32 cursor-pointer hover:text-white" onClick={() => toggleSort('quantity')}>
                    <div className="flex items-center gap-1">
                      Qty
                      {sortBy === 'quantity' ? (sortOrder === 'desc' ? <ArrowDown size={10} /> : <ArrowUp size={10} />) : <ArrowUpDown size={10} className="opacity-30" />}
                    </div>
                  </th>
                  <th className="p-4 text-[10px] font-medium text-slate-400 uppercase tracking-wider cursor-pointer hover:text-white" onClick={() => toggleSort('added_at')}>
                    <div className="flex items-center gap-1">
                      Added At
                      {sortBy === 'added_at' ? (sortOrder === 'desc' ? <ArrowDown size={10} /> : <ArrowUp size={10} />) : <ArrowUpDown size={10} className="opacity-30" />}
                    </div>
                  </th>
                  <th className="p-4 text-[10px] font-medium text-slate-400 uppercase tracking-wider cursor-pointer hover:text-white" onClick={() => toggleSort('last_updated')}>
                    <div className="flex items-center gap-1">
                      Updated
                      {sortBy === 'last_updated' ? (sortOrder === 'desc' ? <ArrowDown size={10} /> : <ArrowUp size={10} />) : <ArrowUpDown size={10} className="opacity-30" />}
                    </div>
                  </th>
                  <th className="p-4 text-[10px] font-medium text-slate-400 uppercase tracking-wider w-12"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {items.map(item => (
                  <tr key={item.collection_id} className="hover:bg-white/5 transition-colors border-b border-border/30">
                    <td className="p-4 text-xs font-mono text-slate-500">{item.collection_id}</td>
                    <td className="p-4 text-xs font-semibold text-slate-100">{item.card_name}</td>
                    <td className="p-4 text-xs text-slate-300 font-mono">{item.card_set.toUpperCase()}</td>
                    <td className="p-4 text-xs text-slate-500">{item.card_number}</td>
                    <td className="p-4 text-xs text-slate-300 uppercase font-bold">{item.card_language}</td>
                    <td className="p-4">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-bold ${
                        item.card_rarity === 'mythic' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                        item.card_rarity === 'rare' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                        item.card_rarity === 'uncommon' ? 'bg-slate-400/20 text-slate-300 border border-slate-400/30' :
                        'bg-slate-700/20 text-slate-500 border border-slate-700/30'
                      }`}>
                        {item.card_rarity}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${item.is_foil ? 'bg-indigo-500/20 text-indigo-400' : 'bg-slate-800 text-slate-500'}`}>
                        {item.is_foil ? 'FOIL' : 'NRM'}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className="text-[11px] font-mono text-slate-300">{item.card_condition}</span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <button onClick={() => handleUpdateQty(item.collection_id, item.quantity, -1)} className="w-6 h-6 rounded border border-border bg-white/5 flex items-center justify-center hover:bg-white/10 text-slate-300">-</button>
                        <span className="w-4 text-center text-xs font-bold text-slate-100">{item.quantity}</span>
                        <button onClick={() => handleUpdateQty(item.collection_id, item.quantity, 1)} className="w-6 h-6 rounded border border-border bg-white/5 flex items-center justify-center hover:bg-white/10 text-slate-300">+</button>
                      </div>
                    </td>
                    <td className="p-4 text-[10px] text-slate-500 whitespace-nowrap">
                      {new Date(item.added_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>
                    <td className="p-4 text-[10px] text-slate-500 whitespace-nowrap">
                      {new Date(item.last_updated).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>
                    <td className="p-4 text-right">
                      <button onClick={() => handleDelete(item.collection_id)} className="p-1.5 text-slate-500 hover:text-red-400 transition-colors">
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
                {!loading && items.length === 0 && (
                  <tr>
                    <td colSpan="12" className="p-12 text-center text-slate-500">
                      Your collection is completely empty.
                    </td>
                  </tr>
                )}
                {loading && (
                  <tr>
                    <td colSpan="12" className="p-12 text-center text-slate-500">
                      <div className="spinner mb-2"></div><br />Loading technical metadata...
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="bg-black/20 border-t border-border p-4 flex items-center justify-between">
            <button
              disabled={page === 1}
              onClick={() => loadCollection(page - 1)}
              className="px-4 py-2 text-sm font-medium border border-border rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 flex items-center gap-2"
            >
              <ChevronLeft size={16} /> Prev
            </button>
            <span className="text-sm font-medium text-slate-400">Page {page}</span>
            <button
              disabled={page * ITEMS_PER_PAGE >= total}
              onClick={() => loadCollection(page + 1)}
              className="px-4 py-2 text-sm font-medium border border-border rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 flex items-center gap-2"
            >
              Next <ChevronRight size={16} />
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
