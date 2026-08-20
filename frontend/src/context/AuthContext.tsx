import React, { createContext, useContext, useState, useEffect } from 'react';

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
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('zerosql_admin_token'));
  const [username, setUsername] = useState<string | null>(() => localStorage.getItem('zerosql_admin_user'));

  useEffect(() => {
    if (token) {
      localStorage.setItem('zerosql_admin_token', token);
    } else {
      localStorage.removeItem('zerosql_admin_token');
    }
  }, [token]);

  useEffect(() => {
    if (username) {
      localStorage.setItem('zerosql_admin_user', username);
    } else {
      localStorage.removeItem('zerosql_admin_user');
    }
  }, [username]);

  const login = (newToken: string, newUsername: string) => {
    setToken(newToken);
    setUsername(newUsername);
  };

  const logout = () => {
    setToken(null);
    setUsername(null);
    localStorage.removeItem('zerosql_admin_token');
    localStorage.removeItem('zerosql_admin_user');
  };

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
