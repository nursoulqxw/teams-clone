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

  owner_info?: {
    id: number;
    first_name: string;
    last_name: string;
  };

  members?: User[];
  members_count?: number;
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

export interface ShortAssignment {
  id: number;
  title: string;
}

export interface StudentInfo {
  id: number;
  email: string;
}

export interface AssignmentSubmission {
  assigment: ShortAssignment;
  student_info: StudentInfo;

  submitted: boolean;
  status: string;
  submitted_at?: string;

  points_awarded?: number;

  file?: string;
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
