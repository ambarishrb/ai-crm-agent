import { useSelector, useDispatch } from 'react-redux';
import { setField } from '../store/interactionSlice';

export default function FollowUpLinks() {
  const followups = useSelector((s) => s.interaction.aiSuggestedFollowups);
  const dispatch = useDispatch();

  if (!followups || followups.length === 0) return null;

  const handleClick = (text) => {
    dispatch(setField({ field: 'followUpActions', value: text }));
  };

  return (
    <div className="form-group">
      <label>AI Suggested Follow-ups</label>
      <div className="followup-links">
        {followups.map((text, i) => (
          <button
            key={i}
            className="followup-link"
            onClick={() => handleClick(text)}
          >
            + {text}
          </button>
        ))}
      </div>
    </div>
  );
}
