import api from "./client";
import type { Assignment, AssignmentSubmission } from "../types";

export const getAssignments = (teamId?: number) =>
  api.get<{ data: Assignment[] }>(
    teamId ? `/assignment/?team_id=${teamId}` : "/assignment/"
  );

export const createAssignment = (data: {
  title: string;
  description?: string;
  team_id: number;
  due_data?: string;
  max_points?: number;
}) => api.post<{ data: Assignment }>("/assignment/", data);

export const getAssignment = (id: number) =>
  api.get<{ data: Assignment }>(`/assignment/${id}/`);

export const updateAssignment = (id: number, data: Partial<Assignment>) =>
  api.patch<{ data: Assignment }>(`/assignment/${id}/`, data);

export const submitAssignment = async (
  assignmentId: number,
  formData: FormData
) => {
  return api.post(
    `/assignment/${assignmentId}/submit/`,
    formData
  );
};

export const getSubmissions = (assignmentId: number) =>
  api.get<AssignmentSubmission[]>(`/assignment/${assignmentId}/submissions/`);

export const gradeSubmission = (
  assignmentId: number,
  submissionId: number,
  points: number
) =>
  api.post(`/assignment/${assignmentId}/grade/${submissionId}/`, {points_awarded: points});
