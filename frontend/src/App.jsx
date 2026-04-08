import { useEffect } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import './App.css';
import LogInteraction from './components/LogInteraction';
import InteractionsList from './components/InteractionsList';
import { resetForm, loadInteractionData } from './store/interactionSlice';

function ListPage() {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  return (
    <>
      <div className="page-header">
        <h1>HCP Interaction Log</h1>
      </div>
      <InteractionsList
        onNew={() => { dispatch(resetForm()); navigate('/interactions/new'); }}
        onOpen={(id) => navigate(`/interactions/${id}`)}
      />
    </>
  );
}

function NewInteractionPage() {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  useEffect(() => { dispatch(resetForm()); }, []);

  return (
    <>
      <div className="page-header page-header--form">
        <button className="btn btn--ghost btn--back" onClick={() => navigate('/')}>← Back</button>
        <h1>New Interaction</h1>
      </div>
      <LogInteraction />
    </>
  );
}

function EditInteractionPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  useEffect(() => { dispatch(loadInteractionData(id)); }, [id]);

  return (
    <>
      <div className="page-header page-header--form">
        <button className="btn btn--ghost btn--back" onClick={() => navigate('/')}>← Back</button>
        <h1>Edit Interaction</h1>
      </div>
      <LogInteraction />
    </>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ListPage />} />
      <Route path="/interactions/new" element={<NewInteractionPage />} />
      <Route path="/interactions/:id" element={<EditInteractionPage />} />
    </Routes>
  );
}
