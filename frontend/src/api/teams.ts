import api from "./client";
import type { Team, TeamMember } from "../types";

export const getTeams = () => api.get<{ data: Team[] }>("/teams/");

export const createTeam = (data: { name: string; description?: string }) =>
  api.post<{ data: Team }>("/teams/", data);

export const getTeam = (id: number) =>
  api.get<{ data: Team }>(`/teams/${id}/`);

export const updateTeam = (id: number, data: Partial<Team>) =>
  api.patch<{ data: Team }>(`/teams/${id}/`, data);

export const deleteTeam = (id: number) => api.delete(`/teams/${id}/`);

export const getTeamMembers = (teamId: number) =>
  api.get<{ data: TeamMember[] }>(`/teams/${teamId}/members/`);

export const addTeamMember = (teamId: number, userId: number) =>
  api.post(`/teams/${teamId}/add-members/`, { user_id: userId });

export const removeTeamMember = (teamId: number, userId: number) =>
  api.delete(`/teams/${teamId}/members/${userId}/`);
