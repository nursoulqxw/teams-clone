import api from "./client";
import type { User, TokenPair } from "../types";

export const login = (email: string, password: string) =>
  api.post<{ data: TokenPair }>("/users/login/", { email, password });

export const register = (data: {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}) => api.post("/users/register/", data);

export const logout = (refresh: string) =>
  api.post("/users/logout/", { refresh });

export const getMe = () => api.get<{ data: User }>("/users/me/");

export const updateMe = (data: Partial<User>) =>
  api.patch<{ data: User }>("/users/me/", data);
