import React, { createContext, useReducer, useContext, ReactNode } from 'react';

export interface ResourcePermissions {
  databases: Array<{ id: string; permissions: string[] }>;
  tables: Array<{ id: string; permissions: string[] }>;
  columns?: Array<{ id: string; permissions: string[] }>;
  queries?: Array<{ id: string; permissions: string[] }>;
  apis?: Array<{ id: string; permissions: string[] }>;
}

export interface User {
  id: string;
  email: string;
  name?: string;
  token?: string;
  roles?: string[];
  permissions?: string[];
  resourcePermissions?: ResourcePermissions;
}

export interface UserState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

export type UserAction =
  | { type: 'SIGNIN_SUCCESS'; payload: User }
  | { type: 'SIGNUP_SUCCESS'; payload: User }
  | { type: 'SIGNOUT' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null };

const initialState: UserState = {
  user: null,
  loading: false,
  error: null
};

function userReducer(state: UserState, action: UserAction): UserState {
  switch (action.type) {
    case 'SIGNIN_SUCCESS':
    case 'SIGNUP_SUCCESS':
      return { ...state, user: action.payload, loading: false, error: null };
    case 'SIGNOUT':
      return { ...state, user: null, loading: false, error: null };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    default:
      return state;
  }
}

const UserContext = createContext<
  | {
      state: UserState;
      dispatch: React.Dispatch<UserAction>;
    }
  | undefined
>(undefined);

export const UserProvider = ({ children }: { children: ReactNode }) => {
  const [state, dispatch] = useReducer(userReducer, initialState);
  return (
    <UserContext.Provider value={{ state, dispatch }}>
      {children}
    </UserContext.Provider>
  );
};

export function useUser() {
  const context = useContext(UserContext);
  if (!context) throw new Error('useUser must be used within UserProvider');
  return context;
}

// Helper functions for permission checks

export function hasPermission(user: User | null, permission: string): boolean {
  if (!user) return false;
  return user.permissions?.includes(permission) || false;
}

export function hasResourcePermission(
  user: User | null,
  resourceType: keyof ResourcePermissions,
  resourceId: string,
  permission: string
): boolean {
  if (!user || !user.resourcePermissions) return false;

  const resources = user.resourcePermissions[resourceType];
  if (!resources) return false;

  const resource = resources.find((r) => r.id === resourceId);
  return resource?.permissions.includes(permission) || false;
}

export function canAccessDatabase(
  user: User | null,
  databaseId: string
): boolean {
  return hasResourcePermission(user, 'databases', databaseId, 'read');
}

export function canAccessTable(user: User | null, tableId: string): boolean {
  return hasResourcePermission(user, 'tables', tableId, 'read');
}
