import { useApi } from "~/shared/api";
import type { AuthTokens, Credentials, RegisterPayload } from "../model/types";

export const sessionApi = {
  login(creds: Credentials): Promise<AuthTokens> {
    return useApi().post<AuthTokens>("/auth/login", creds);
  },
  register(payload: RegisterPayload): Promise<AuthTokens> {
    return useApi().post<AuthTokens>("/auth/register", payload);
  },
};
