/**
 * Microsoft Clarity Analytics Type Definitions
 * 
 * This file contains TypeScript interfaces and type definitions
 * for Microsoft Clarity analytics integration.
 */

/**
 * Configuration interface for Microsoft Clarity
 */
export interface ClarityConfig {
  /** Microsoft Clarity project identifier */
  projectId: string;
}

/**
 * Environment variables interface for Clarity configuration
 */
export interface ClarityEnvironment {
  /** Public environment variable for Clarity project ID */
  NEXT_PUBLIC_CLARITY_PROJECT_ID?: string;
}

/**
 * Page view event data structure for Clarity tracking
 */
export interface ClarityPageView {
  /** Full URL including pathname and search parameters */
  url: string;
  /** Timestamp when the page view occurred */
  timestamp: number;
}

/**
 * Microsoft Clarity global function interface
 * Extends the Window interface to include Clarity's global function
 */
declare global {
  interface Window {
    /**
     * Microsoft Clarity global tracking function
     * @param action - The action to perform (e.g., 'set', 'identify', 'consent')
     * @param args - Additional arguments for the action
     */
    clarity: (action: string, ...args: any[]) => void;
  }
}

/**
 * Clarity tracking actions enum for type safety
 */
export enum ClarityAction {
  SET = 'set',
  IDENTIFY = 'identify',
  CONSENT = 'consent',
  UPGRADE = 'upgrade'
}

/**
 * Clarity set command parameters
 */
export interface ClaritySetParams {
  /** Key to set (e.g., 'page', 'userId') */
  key: string;
  /** Value to set */
  value: string | number | boolean;
}