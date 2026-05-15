import api from "./client";
import type { Assignment, AssignmentSubmission } from "../types";

export const getAssignments = (teamId?: number) =>
  api.get<{ data: Assignment[] }>(
    teamId ? `/assignment/?team_id=${teamId}` : "/assignment/"
  );

export const createAssignment = (data: {
  title: string;
  description?: string;
  team: number;
  due_date?: string;
}) => api.post<{ data: Assignment }>("/assignment/", data);

export const getAssignment = (id: number) =>
  api.get<{ data: Assignment }>(`/assignment/${id}/`);

export const updateAssignment = (id: number, data: Partial<Assignment>) =>
  api.patch<{ data: Assignment }>(`/assignment/${id}/`, data);

export const submitAssignment = (id: number, data?: object) =>
  api.post<{ data: AssignmentSubmission }>(
    `/assignment/${id}/submit/`,
    data ?? {}
  );

export const getSubmissions = (assignmentId: number) =>
  api.get<AssignmentSubmission[]>(`/assignment/${assignmentId}/submissions/`);

export const gradeSubmission = (
  assignmentId: number,
  submissionId: number,
  grade: number
) =>
  api.post(`/assignment/${assignmentId}/grade/${submissionId}/`, { grade });
