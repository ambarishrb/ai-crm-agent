import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { sendChatMessage } from '../services/api';
import { setMultipleFields } from './interactionSlice';

export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async (text, { getState, dispatch }) => {
    const { interaction } = getState();
    const formState = {
      hcp_name: interaction.hcp.name,
      hcp: interaction.hcp,
      interaction_type: interaction.interactionType,
      date: interaction.date,
      time: interaction.time,
      attendees: interaction.attendees,
      topics_discussed: interaction.topicsDiscussed,
      sentiment: interaction.sentiment,
      outcomes: interaction.outcomes,
      follow_up_actions: interaction.followUpActions,
      materials_shared: interaction.materialsShared,
      samples_distributed: interaction.samplesDistributed,
    };

    const interactionId = interaction.savedInteractionId;
    const response = await sendChatMessage(text, formState, interactionId);

    // Bridge: apply form_updates to the interaction slice
    if (response.form_updates) {
      dispatch(setMultipleFields(response.form_updates));
    }

    // If the agent created/referenced an interaction, save its ID
    if (response.interaction_id) {
      dispatch(setMultipleFields({ savedInteractionId: response.interaction_id }));
    }

    return response;
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [],
    isLoading: false,
  },
  reducers: {
    clearMessages(state) {
      state.messages = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state, action) => {
        state.isLoading = true;
        state.messages.push({ role: 'user', content: action.meta.arg });
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isLoading = false;
        state.messages.push({ role: 'assistant', content: action.payload.reply });
      })
      .addCase(sendMessage.rejected, (state) => {
        state.isLoading = false;
        state.messages.push({ role: 'assistant', content: 'Sorry, something went wrong. Please try again.' });
      });
  },
});

export const { clearMessages } = chatSlice.actions;

export default chatSlice.reducer;
