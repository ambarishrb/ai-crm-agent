import { useSelector } from 'react-redux';

export default function MaterialSearch() {
  const materials = useSelector((s) => s.interaction.materialsShared);

  return (
    <div className="material-sample-section">
      <div className="section-header">
        <label>Materials Shared</label>
      </div>
      {materials.length > 0 ? (
        <div className="chip-list">
          {materials.map((m, i) => (
            <span key={i} className="chip">{m}</span>
          ))}
        </div>
      ) : (
        <p className="empty-state">No materials added.</p>
      )}
    </div>
  );
}
