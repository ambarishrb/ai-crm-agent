import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { createInteraction as apiCreateInteraction, updateInteraction as apiUpdateInteraction, getInteraction as apiGetInteraction } from '../services/api';

export const initialState = {
  hcp: { id: '', name: '' },
  interactionType: 'Meeting',
  date: '',
  time: '',
  attendees: '',
  topicsDiscussed: '',
  materialsShared: [],
  samplesDistributed: [],
  sentiment: 'Neutral',
  outcomes: '',
  followUpActions: '',
  aiSuggestedFollowups: [],
  aiSummary: '',
  isSubmitting: false,
  savedInteractionId: null,
};

export const loadInteractionData = createAsyncThunk(
  'interaction/load',
  async (id) => {
    return await apiGetInteraction(id);
  }
);

export const submitInteraction = createAsyncThunk(
  'interaction/submit',
  async (_, { getState }) => {
    const state = getState().interaction;
    const payload = {
      interaction_type: state.interactionType,
      interaction_date: state.date || null,
      interaction_time: state.time || null,
      attendees: state.attendees || null,
      topics_discussed: state.topicsDiscussed || null,
      sentiment: state.sentiment,
      outcomes: state.outcomes || null,
      follow_up_actions: state.followUpActions || null,
      ai_suggested_followups: state.aiSuggestedFollowups.length > 0 ? state.aiSuggestedFollowups : null,
      ai_summary: state.aiSummary || null,
    };

    // If interaction already exists (created by AI), update it; otherwise create new
    if (state.savedInteractionId) {
      return await apiUpdateInteraction(state.savedInteractionId, payload);
    }
    return await apiCreateInteraction(payload);
  }
);

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    setField(state, action) {
      const { field, value } = action.payload;
      state[field] = value;
    },
    setMultipleFields(state, action) {
      Object.entries(action.payload).forEach(([key, value]) => {
        if (key in state) {
          state[key] = value;
        }
      });
    },
    resetForm() {
      return initialState;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(submitInteraction.pending, (state) => {
        state.isSubmitting = true;
      })
      .addCase(submitInteraction.fulfilled, (state, action) => {
        state.isSubmitting = false;
        state.savedInteractionId = action.payload.id;
      })
      .addCase(submitInteraction.rejected, (state) => {
        state.isSubmitting = false;
      })
      .addCase(loadInteractionData.fulfilled, (state, action) => {
        const d = action.payload;
        state.hcp = { id: d.hcp_id || '', name: d.hcp_name || '' };
        state.interactionType = d.interaction_type || 'Meeting';
        state.date = d.interaction_date || '';
        state.time = d.interaction_time || '';
        state.attendees = d.attendees || '';
        state.topicsDiscussed = d.topics_discussed || '';
        state.sentiment = d.sentiment || 'Neutral';
        state.outcomes = d.outcomes || '';
        state.followUpActions = d.follow_up_actions || '';
        state.aiSuggestedFollowups = d.ai_suggested_followups || [];
        state.aiSummary = d.ai_summary || '';
        state.materialsShared = [];
        state.samplesDistributed = [];
        state.savedInteractionId = d.id;
        state.isSubmitting = false;
      });
  },
});

export const {
  setField,
  setMultipleFields,
  resetForm,
} = interactionSlice.actions;

export default interactionSlice.reducer;
