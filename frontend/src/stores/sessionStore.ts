/**
 * ✅ Phase 2: Zustand Session Store
 * Replaces SessionContext with better performance
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Screenshot {
  filename: string;
  path: string;
  url: string;
  timestamp: string;
  quality_score?: number;
  segments?: number;
}

interface Session {
  id: string;
  name: string;
  defaultName: string;
  timestamp: string;
  screenshots: Screenshot[];
  urls: string[];
  duration: number;
  settings: {
    captureMode: string;
    useStealth: boolean;
    useRealBrowser: boolean;
  };
}

interface SessionState {
	// Sessions
	sessions: Session[];
	/**
	 * Setter that mirrors React's useState API:
	 *
	 * - setSessions(newArray)
	 * - setSessions(prev => newArray)
	 */
	setSessions: (updater: Session[] | ((prev: Session[]) => Session[])) => void;
	addSession: (session: Session) => void;
	removeSession: (id: string) => void;
	updateSession: (id: string, updates: Partial<Session>) => void;

  // Selected Sessions
  selectedSessions: Set<string>;
	  // Setter that mirrors React's useState API for Sets:
	  // - setSelectedSessions(new Set([...]))
	  // - setSelectedSessions(prev => new Set(prev))
	  setSelectedSessions: (
	    updater: Set<string> | ((prev: Set<string>) => Set<string>)
	  ) => void;
  toggleSession: (id: string) => void;
  selectAll: () => void;
  deselectAll: () => void;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      // Sessions
	      sessions: [],
	      setSessions: (updater) =>
	        set((state) => ({
	          sessions:
	            typeof updater === "function"
	              ? (updater as (prev: Session[]) => Session[])(state.sessions)
	              : updater,
	        })),
      addSession: (session) => set((state) => ({ sessions: [...state.sessions, session] })),
      removeSession: (id) => set((state) => ({ sessions: state.sessions.filter(s => s.id !== id) })),
      updateSession: (id, updates) => set((state) => ({
        sessions: state.sessions.map(s => s.id === id ? { ...s, ...updates } : s)
      })),

	      // Selected Sessions
	      selectedSessions: new Set(),
	      setSelectedSessions: (updater) =>
	        set((state) => ({
	          selectedSessions:
	            typeof updater === "function"
	              ? (updater as (prev: Set<string>) => Set<string>)(
	                  state.selectedSessions,
	                )
	              : updater,
	        })),
      toggleSession: (id) => set((state) => {
        const newSelected = new Set(state.selectedSessions);
        if (newSelected.has(id)) {
          newSelected.delete(id);
        } else {
          newSelected.add(id);
        }
        return { selectedSessions: newSelected };
      }),
      selectAll: () => set((state) => ({
        selectedSessions: new Set(state.sessions.map(s => s.id))
      })),
      deselectAll: () => set({ selectedSessions: new Set() }),
    }),
    {
      name: 'session-storage',
      partialize: (state) => ({
        sessions: state.sessions,
        // Don't persist selectedSessions
      }),
    }
  )
);

// Selectors
export const selectSessions = (state: SessionState) => state.sessions;
export const selectSelectedSessions = (state: SessionState) => state.selectedSessions;
export const selectSessionById = (id: string) => (state: SessionState) =>
  state.sessions.find(s => s.id === id);
export const selectSelectedSessionsData = (state: SessionState) =>
  state.sessions.filter(s => state.selectedSessions.has(s.id));

