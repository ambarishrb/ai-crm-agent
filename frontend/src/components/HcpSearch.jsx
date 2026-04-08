import { useState, useCallback, useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setField } from '../store/interactionSlice';
import { searchHcps } from '../services/api';

export default function HcpSearch() {
  const hcp = useSelector((s) => s.interaction.hcp);
  const dispatch = useDispatch();
  const [query, setQuery] = useState(hcp.name || '');
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const timerRef = useRef(null);
  const wrapperRef = useRef(null);

  useEffect(() => {
    setQuery(hcp.name || '');
  }, [hcp.name]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const doSearch = useCallback((q) => {
    if (q.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      try {
        const data = await searchHcps(q);
        setResults(data);
        setOpen(data.length > 0);
      } catch {
        setResults([]);
      }
    }, 300);
  }, []);

  const handleChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    doSearch(val);
    if (!val) {
      dispatch(setField({ field: 'hcp', value: { id: '', name: '' } }));
    }
  };

  const handleSelect = (item) => {
    dispatch(setField({ field: 'hcp', value: { id: item.id, name: item.full_name } }));
    setQuery(item.full_name);
    setOpen(false);
  };

  return (
    <div className="search-wrapper" ref={wrapperRef}>
      <input
        type="text"
        placeholder="Search or select HCP..."
        value={query}
        onChange={handleChange}
        onFocus={() => results.length > 0 && setOpen(true)}
      />
      {open && (
        <div className="search-dropdown">
          {results.map((r) => (
            <div
              key={r.id}
              className="search-dropdown__item"
              onClick={() => handleSelect(r)}
            >
              {r.full_name}
              <small>({r.specialty} - {r.organization})</small>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
