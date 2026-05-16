export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  avatar?: string;
}

export interface Team {
  id: number;
  name: string;
  description?: string;
  owner: number;
  members: number[];
  created_at: string;
}

export interface TeamMember {
  id: number;
  user: User;
  team: number;
  role: "owner" | "member";
  joined_at: string;
}

export interface Channel {
  id: number;
  name: string;
  description?: string;
  team: number;
  created_at: string;
}

export interface Message {
  id: number;
  channel: number;
  author: User;
  content: string;
  created_at: string;
  updated_at: string;
  is_edited: boolean;
}

export interface Assignment {
  id: number;
  title: string;
  description?: string;
  team_id: number;
  due_data?: string;
  max_points?: number;
  created_at: string;
  status?: string;
}

export interface AssignmentSubmission {
  id: number;
  assignment: number;
  student_id: User;
  submitted: boolean;
  status: string;
  grade?: number;
  submitted_at?: string;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface WSMessage {
  type: "chat_message" | "error";
  message?: string;
  sender?: string;
  sender_id?: number;
  timestamp?: string;
}
