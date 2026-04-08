import { useEffect, useState } from 'react';
import { listInteractions, deleteInteraction, deleteAllInteractions } from '../services/api';

const SENTIMENT_STYLE = {
  Positive: { color: 'var(--green)', background: '#e6f4ea' },
  Neutral:  { color: 'var(--blue)',  background: 'var(--blue-light)' },
  Negative: { color: 'var(--red)',   background: '#fce8e6' },
};

function truncate(str, n = 60) {
  if (!str) return '—';
  return str.length > n ? str.slice(0, n) + '…' : str;
}

function formatDate(d) {
  if (!d) return '—';
  const dt = new Date(d + 'T00:00:00');
  return dt.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

export default function InteractionsList({ onNew, onOpen }) {
  const [interactions, setInteractions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirmingId, setConfirmingId] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [confirmingAll, setConfirmingAll] = useState(false);
  const [deletingAll, setDeletingAll] = useState(false);

  useEffect(() => {
    listInteractions()
      .then(setInteractions)
      .catch(() => setError('Failed to load interactions.'))
      .finally(() => setLoading(false));
  }, []);

  async function handleDeleteAll() {
    setDeletingAll(true);
    try {
      await deleteAllInteractions();
      setInteractions([]);
    } catch {
      setError('Failed to delete all interactions.');
    } finally {
      setDeletingAll(false);
      setConfirmingAll(false);
    }
  }

  async function handleDelete(id) {
    setDeleting(id);
    try {
      await deleteInteraction(id);
      setInteractions((prev) => prev.filter((i) => i.id !== id));
    } catch {
      setError('Failed to delete interaction.');
    } finally {
      setDeleting(null);
      setConfirmingId(null);
    }
  }

  return (
    <div className="interactions-list-page">
      <div className="interactions-list-toolbar">
        <div>
          <h2 className="interactions-list-title">HCP Interactions</h2>
          {!loading && !error && (
            <span className="interactions-list-count">{interactions.length} record{interactions.length !== 1 ? 's' : ''}</span>
          )}
        </div>
        <div className="toolbar-actions">
          {!loading && !error && interactions.length > 0 && (
            confirmingAll ? (
              <div className="delete-confirm">
                <span className="delete-confirm__label">Delete all {interactions.length} records?</span>
                <button
                  className="btn btn--danger btn--sm"
                  disabled={deletingAll}
                  onClick={handleDeleteAll}
                >
                  {deletingAll ? 'Deleting…' : 'Yes, delete all'}
                </button>
                <button
                  className="btn btn--ghost btn--sm"
                  disabled={deletingAll}
                  onClick={() => setConfirmingAll(false)}
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                className="btn btn--ghost btn--sm btn--ghost-danger"
                onClick={() => setConfirmingAll(true)}
              >
                Delete All
              </button>
            )
          )}
          <button className="btn btn--primary" onClick={onNew}>
            + New Interaction
          </button>
        </div>
      </div>

      {loading && <div className="interactions-list-status">Loading…</div>}
      {error   && <div className="interactions-list-status interactions-list-status--error">{error}</div>}

      {!loading && !error && interactions.length === 0 && (
        <div className="interactions-list-empty">
          <p>No interactions logged yet.</p>
          <button className="btn btn--primary" onClick={onNew}>Log your first interaction</button>
        </div>
      )}

      {!loading && !error && interactions.length > 0 && (
        <div className="interactions-table-wrap">
          <table className="interactions-table">
            <thead>
              <tr>
                <th>HCP</th>
                <th>Type</th>
                <th>Date</th>
                <th>Sentiment</th>
                <th>Topics</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {interactions.map((i) => {
                const sentiment = i.sentiment || 'Neutral';
                const sentStyle = SENTIMENT_STYLE[sentiment] || SENTIMENT_STYLE.Neutral;
                const isConfirming = confirmingId === i.id;
                const isDeleting = deleting === i.id;

                return (
                  <tr
                    key={i.id}
                    className="interactions-table__row"
                    onClick={() => !isConfirming && onOpen(i.id)}
                  >
                    <td className="interactions-table__hcp">{i.hcp_name || '—'}</td>
                    <td>
                      <span className="interaction-type-badge">{i.interaction_type || '—'}</span>
                    </td>
                    <td className="interactions-table__date">{formatDate(i.interaction_date)}</td>
                    <td>
                      <span className="sentiment-badge" style={sentStyle}>{sentiment}</span>
                    </td>
                    <td className="interactions-table__topics">{truncate(i.topics_discussed)}</td>
                    <td className="interactions-table__action" onClick={(e) => e.stopPropagation()}>
                      {isConfirming ? (
                        <div className="delete-confirm">
                          <span className="delete-confirm__label">Delete this record?</span>
                          <button
                            className="btn btn--danger btn--sm"
                            disabled={isDeleting}
                            onClick={() => handleDelete(i.id)}
                          >
                            {isDeleting ? 'Deleting…' : 'Yes, delete'}
                          </button>
                          <button
                            className="btn btn--ghost btn--sm"
                            disabled={isDeleting}
                            onClick={() => setConfirmingId(null)}
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="row-actions">
                          <button
                            className="btn btn--ghost btn--sm"
                            onClick={() => onOpen(i.id)}
                          >
                            Open
                          </button>
                          <button
                            className="btn btn--ghost btn--sm btn--ghost-danger"
                            onClick={() => setConfirmingId(i.id)}
                          >
                            Delete
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
