import axios from 'axios';
import { ScanConsentFoldersResponse } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const scanConsentFolders = async (consentFolderPath: string, useS3: boolean = false): Promise<ScanConsentFoldersResponse> => {
  const response = await api.post('/scan-consent-folders', { consent_folder_path: consentFolderPath, use_s3: useS3 });
  return response.data;
};

/**
 * Scan a watch folder for video clips and add them to the database
 * @param watchFolderId The ID of the watch folder
 * @param folderPath The path to scan
 * @returns Result of the scan operation
 */
export interface ScanWatchFolderResponse {
  task_id: string;
  status: string;
  clips_found: number;
  clips_created: number;
  clips_updated: number;
  watch_folder_path: string;
  duplicate_filenames?: string[]; // List of filenames that were skipped because they already exist for this card
}

export const scanWatchFolder = async (watchFolderId: string, folderPath: string): Promise<ScanWatchFolderResponse> => {
  const response = await api.post('/scan-watch-folder', { 
    watch_folder_id: watchFolderId, 
    folder_path: folderPath 
  });
  return response.data;
};

/**
 * Generate a URL to access local filesystem images through the API proxy
 * @param imagePath The local file path of the image
 * @returns A URL that can be used in img tags
 */
export const getImageUrl = (imagePath: string): string => {
  if (!imagePath) return '';
  
  // Encode the path to handle spaces and special characters
  const encodedPath = encodeURIComponent(imagePath);
  return `${API_BASE_URL}/images?path=${encodedPath}`;
};

/**
 * Start monitoring a watch folder for new video clips
 * @param watchFolderId The ID of the watch folder
 * @param inactivityTimeoutMinutes Number of minutes of inactivity before stopping monitoring
 * @returns Result of the monitoring operation
 */
export interface StartWatchFolderMonitoringResponse {
  status: string;
  watch_folder_id: string;
  monitoring_status: string;
  message: string;
  inactivity_timeout_minutes: number;
}

export const startWatchFolderMonitoring = async (
  watchFolderId: string,
  inactivityTimeoutMinutes: number = 30
): Promise<StartWatchFolderMonitoringResponse> => {
  console.log(`API: Starting monitoring for watch folder ID: ${watchFolderId}`);
  try {
    const response = await api.post('/start-watch-folder-monitoring', {
      watch_folder_id: watchFolderId.toString(), // Ensure it's a string
      inactivity_timeout_minutes: inactivityTimeoutMinutes
    });
    return response.data;
  } catch (error) {
    console.error('API error in startWatchFolderMonitoring:', error);
    throw error;
  }
};

/**
 * Stop monitoring a watch folder
 * @param watchFolderId The ID of the watch folder
 * @returns Result of the stop operation
 */
export interface StopWatchFolderMonitoringResponse {
  status: string;
  watch_folder_id: string;
  monitoring_status: string;
  message: string;
}

export const stopWatchFolderMonitoring = async (
  watchFolderId: string
): Promise<StopWatchFolderMonitoringResponse> => {
  const response = await api.post('/stop-watch-folder-monitoring', {
    watch_folder_id: watchFolderId
  });
  return response.data;
};

/**
 * Start processing a card (embedding generation, clip processing, etc.)
 * @param cardId The ID of the card to process
 * @param config Optional configuration overrides
 * @returns Result of the processing operation
 */
export interface StartProcessingResponse {
  task_id: string;
  status: string;
  message: string;
  clips_count: number;
}

export const startProcessing = async (
  cardId: string,
  config?: Record<string, any>
): Promise<StartProcessingResponse> => {
  const response = await api.post('/start-processing', {
    card_id: cardId,
    config
  });
  return response.data;
};

/**
 * Stop an active processing task
 * @param taskId The ID of the task to stop
 * @returns Result of the stop operation
 */
export interface StopProcessingResponse {
  status: string;
  message: string;
}

export const stopProcessing = async (
  taskId: string
): Promise<StopProcessingResponse> => {
  const response = await api.post('/stop-processing', {
    task_id: taskId
  });
  return response.data;
};

/**
 * Get a list of all processing tasks (for debugging/monitoring)
 * @returns List of tasks with their status
 */
export interface ProcessingTask {
  task_id: string;
  card_id: string;
  status: string;
  started_at: string;
  updated_at: string;
  progress: number;
  stage: string;
  message?: string;
}

export const getProcessingTasks = async (): Promise<ProcessingTask[]> => {
  const response = await api.get('/processing-tasks');
  return response.data;
};

export default api; 