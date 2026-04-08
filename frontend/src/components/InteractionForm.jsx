import { useSelector, useDispatch } from 'react-redux';
import { submitInteraction, resetForm } from '../store/interactionSlice';
import MaterialSearch from './MaterialSearch';
import SampleAdd from './SampleAdd';
import SentimentRadio from './SentimentRadio';
import FollowUpLinks from './FollowUpLinks';

export default function InteractionForm() {
  const form = useSelector((s) => s.interaction);
  const dispatch = useDispatch();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.hcp.id) {
      alert('Please log an interaction via the AI chat first.');
      return;
    }
    dispatch(submitInteraction());
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-section-title">Interaction Details</div>

      <div className="form-row">
        <div className="form-group">
          <label>HCP Name</label>
          <input
            type="text"
            placeholder="Filled by AI assistant..."
            value={form.hcp.name}
            disabled
          />
        </div>
        <div className="form-group">
          <label>Interaction Type</label>
          <select value={form.interactionType} disabled>
            <option value="Meeting">Meeting</option>
            <option value="Call">Call</option>
            <option value="Email">Email</option>
            <option value="Conference">Conference</option>
          </select>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Date</label>
          <input type="date" value={form.date} disabled />
        </div>
        <div className="form-group">
          <label>Time</label>
          <input type="time" value={form.time} disabled />
        </div>
      </div>

      <div className="form-group">
        <label>Attendees</label>
        <input
          type="text"
          placeholder="Filled by AI assistant..."
          value={form.attendees}
          disabled
        />
      </div>

      <div className="form-group">
        <label>Topics Discussed</label>
        <textarea
          placeholder="Filled by AI assistant..."
          value={form.topicsDiscussed}
          disabled
        />
      </div>

      <button type="button" className="btn btn--voice" disabled>
        Summarize from Voice Note (Requires Consent)
      </button>

      <div className="form-section-title">Materials Shared / Samples Distributed</div>

      <MaterialSearch />
      <SampleAdd />

      <SentimentRadio />

      <div className="form-group">
        <label>Outcomes</label>
        <textarea
          placeholder="Filled by AI assistant..."
          value={form.outcomes}
          disabled
        />
      </div>

      <div className="form-group">
        <label>Follow-up Actions</label>
        <textarea
          placeholder="Filled by AI assistant..."
          value={form.followUpActions}
          disabled
        />
      </div>

      <FollowUpLinks />

      {form.aiSummary && (
        <div className="form-group">
          <label>AI Summary</label>
          <p style={{ fontSize: 13, color: 'var(--grey-700)', lineHeight: 1.5 }}>
            {form.aiSummary}
          </p>
        </div>
      )}

      <div className="submit-row">
        <button
          type="submit"
          className="btn btn--primary"
          disabled={form.isSubmitting || !form.hcp.id}
        >
          {form.isSubmitting ? 'Submitting...' : 'Submit Interaction'}
        </button>
        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => dispatch(resetForm())}
        >
          Clear Form
        </button>
        {form.savedInteractionId && (
          <span style={{ marginLeft: 12, fontSize: 13, color: 'var(--green)' }}>
            Saved successfully
          </span>
        )}
      </div>
    </form>
  );
}
