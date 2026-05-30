/**
 * ✅ FIXED (Bug #14): Session management context
 * 
 * Manages screenshot sessions (save/load/delete).
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { useLocalStorageWithSerializer } from '../hooks/useLocalStorage';

interface Session {
  id: string;
  name: string;
  timestamp: string;
  urls: string;
  results: any[];
}

interface SessionContextType {
  sessions: Session[];
  setSessions: (sessions: Session[]) => void;
  selectedSessions: Set<string>;
  setSelectedSessions: (sessions: Set<string>) => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sessions, setSessions] = useLocalStorageWithSerializer<Session[]>(
    "screenshot-sessions",
    []
  );
  const [selectedSessions, setSelectedSessions] = React.useState<Set<string>>(
    new Set()
  );

  const value: SessionContextType = {
    sessions,
    setSessions,
    selectedSessions,
    setSelectedSessions,
  };

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
};

export const useSessionContext = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSessionContext must be used within SessionProvider');
  }
  return context;
};

