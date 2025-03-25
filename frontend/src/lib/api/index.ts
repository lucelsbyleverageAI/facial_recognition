import axios from 'axios';
import { ScanConsentFoldersResponse } from '@/types';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const scanConsentFolders = async (consentFolderPath: string): Promise<ScanConsentFoldersResponse> => {
  const response = await api.post('/scan-consent-folders', { consent_folder_path: consentFolderPath });
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

export default api; 