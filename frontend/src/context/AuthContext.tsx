import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

interface AuthContextType {
  isAuthenticated: boolean;
  username: string | null;
  token: string | null;
  login: (token: string, username: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  username: null,
  token: null,
  login: () => {},
  logout: () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Store admin Bearer token strictly in sessionStorage (session-scoped)
  const [token, setToken] = useState<string | null>(() => {
    return sessionStorage.getItem('zerosql_admin_token');
  });

  const [username, setUsername] = useState<string | null>(() => {
    return sessionStorage.getItem('zerosql_admin_user');
  });

  useEffect(() => {
    if (token) {
      sessionStorage.setItem('zerosql_admin_token', token);
    } else {
      sessionStorage.removeItem('zerosql_admin_token');
    }
  }, [token]);

  useEffect(() => {
    if (username) {
      sessionStorage.setItem('zerosql_admin_user', username);
    } else {
      sessionStorage.removeItem('zerosql_admin_user');
    }
  }, [username]);

  const login = useCallback((newToken: string, newUsername: string) => {
    setToken(newToken);
    setUsername(newUsername);
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUsername(null);
    sessionStorage.removeItem('zerosql_admin_token');
    sessionStorage.removeItem('zerosql_admin_user');
    // Ensure any legacy localStorage keys are also completely purged
    localStorage.removeItem('zerosql_admin_token');
    localStorage.removeItem('zerosql_admin_user');
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!token,
        username,
        token,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
