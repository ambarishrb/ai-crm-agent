import { configureStore } from '@reduxjs/toolkit';
import interactionReducer, { initialState as interactionInitialState } from './interactionSlice';
import chatReducer from './chatSlice';

const STORAGE_KEY = 'hcp_interaction_form';

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? { interaction: JSON.parse(raw) } : undefined;
  } catch {
    return undefined;
  }
}

function saveState(state) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // ignore write errors
  }
}

const store = configureStore({
  reducer: {
    interaction: interactionReducer,
    chat: chatReducer,
  },
  preloadedState: loadState(),
});

store.subscribe(() => {
  saveState(store.getState().interaction);
});

export default store;
