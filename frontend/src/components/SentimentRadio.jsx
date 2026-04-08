import { useSelector } from 'react-redux';

const options = [
  { value: 'Positive', icon: '\u{1F60A}', className: 'sentiment-option--positive' },
  { value: 'Neutral', icon: '\u{1F610}', className: 'sentiment-option--neutral' },
  { value: 'Negative', icon: '\u{1F61E}', className: 'sentiment-option--negative' },
];

export default function SentimentRadio() {
  const sentiment = useSelector((s) => s.interaction.sentiment);

  return (
    <div className="form-group">
      <label>Observed/Inferred HCP Sentiment</label>
      <div className="sentiment-group">
        {options.map((opt) => (
          <label key={opt.value} className={`sentiment-option ${opt.className}`}>
            <input
              type="radio"
              name="sentiment"
              value={opt.value}
              checked={sentiment === opt.value}
              disabled
              readOnly
            />
            {opt.icon} {opt.value}
          </label>
        ))}
      </div>
    </div>
  );
}
