import { useSelector } from 'react-redux';

export default function SampleAdd() {
  const samples = useSelector((s) => s.interaction.samplesDistributed);

  return (
    <div className="material-sample-section">
      <div className="section-header">
        <label>Samples Distributed</label>
      </div>
      {samples.length > 0 ? (
        <div className="chip-list">
          {samples.map((s, i) => (
            <span key={i} className="chip">{s}</span>
          ))}
        </div>
      ) : (
        <p className="empty-state">No samples added.</p>
      )}
    </div>
  );
}
