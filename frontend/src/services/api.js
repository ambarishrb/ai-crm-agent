import axios from 'axios';

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
});

export const searchHcps = (query) =>
  api.get('/hcps', { params: { search: query } }).then((r) => r.data);

export const getHcp = (id) =>
  api.get(`/hcps/${id}`).then((r) => r.data);

export const createInteraction = (data) =>
  api.post('/interactions', data).then((r) => r.data);

export const getInteraction = (id) =>
  api.get(`/interactions/${id}`).then((r) => r.data);

export const listInteractions = (hcpId) =>
  api.get('/interactions', { params: hcpId ? { hcp_id: hcpId } : {} }).then((r) => r.data);

export const updateInteraction = (id, data) =>
  api.put(`/interactions/${id}`, data).then((r) => r.data);

export const deleteInteraction = (id) =>
  api.delete(`/interactions/${id}`);

export const deleteAllInteractions = () =>
  api.delete('/interactions').then((r) => r.data);

export const searchMaterials = (query) =>
  api.get('/materials', { params: { search: query } }).then((r) => r.data);

export const getSamples = () =>
  api.get('/samples').then((r) => r.data);

export const sendChatMessage = (message, currentFormState, interactionId) =>
  api.post('/chat', {
    message,
    current_form_state: currentFormState,
    interaction_id: interactionId,
  }).then((r) => r.data);

export default api;
