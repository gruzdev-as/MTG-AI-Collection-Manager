const API_PREFIX = '/api';

export const api = {
  // Collection Mutators
  getCollection: async (limit = 100, offset = 0, sortBy = "added_at", order = "desc") => {
    const res = await fetch(`${API_PREFIX}/collection?limit=${limit}&offset=${offset}&sort_by=${sortBy}&order=${order}`);
    if (!res.ok) throw new Error('Failed to fetch collection');
    return res.json();
  },
  
  updateCollectionItem: async (collectionId, updates) => {
    const res = await fetch(`${API_PREFIX}/collection/${collectionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    if (!res.ok) throw new Error('Failed to update item');
    return res.json();
  },

  deleteCollectionItem: async (collectionId) => {
    const res = await fetch(`${API_PREFIX}/collection/${collectionId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete item');
    return res.json();
  },

  addCardsToCollection: async (cards) => {
    const res = await fetch(`${API_PREFIX}/collection/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cards)
    });
    if (!res.ok) throw new Error('Failed to upload cards list');
    return res.json();
  },

  // Scanner Core 
  scanPhoto: async (blob) => {
    const formData = new FormData();
    formData.append("image", blob, "card.jpg");
    
    const res = await fetch(`${API_PREFIX}/scan`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error('Inference Network Rejected Request');
    return res.json();
  },

  pollResult: async (frameId) => {
    const res = await fetch(`${API_PREFIX}/result/${frameId}`);
    if (res.status === 202) return null; // Pending
    if (!res.ok) throw new Error('Polling Failed');
    return res.json();
  }
};
