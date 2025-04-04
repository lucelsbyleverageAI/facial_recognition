'use client';

import { useQuery, useMutation } from '@apollo/client';
import { GET_CARD_CONFIG, UPDATE_CARD_CONFIG } from '@/lib/graphql/queries';

// Define types based on the database schema
export interface CardConfig {
  config_id: string;
  scene_sensitivity: number;
  fallback_frame_rate: number;
  use_eq: boolean;
  lut_file?: string | null;
  model_name: string;
  detector_backend: string;
  align: boolean;
  enforce_detection: boolean;
  distance_metric: string;
  expand_percentage: number;
  threshold?: number;
  normalization: string;
  silent: boolean;
  refresh_database: boolean;
  anti_spoofing: boolean;
  detection_confidence_threshold: number;
  watch_folders?: WatchFolder[];
}

export interface WatchFolder {
  watch_folder_id: string;
  folder_path: string;
  status: 'idle' | 'scanned' | 'active' | 'error';
}

interface CardConfigData {
  card_configs: CardConfig[];
}

export type CardConfigInput = Omit<CardConfig, 'config_id' | 'watch_folders'>;

export function useCardConfig(cardId: string) {
  // Query to get the card configuration
  const { data, loading, error, refetch } = useQuery<CardConfigData>(GET_CARD_CONFIG, {
    variables: { cardId },
    skip: !cardId,
  });

  // Mutation to update the card configuration
  const [updateConfig, updateResult] = useMutation(UPDATE_CARD_CONFIG, {
    onCompleted: () => {
      refetch();
    },
  });

  // Helper function to update card config
  const updateCardConfig = async (configId: string, updates: Partial<CardConfigInput>) => {
    try {
      // Remove __typename if present to avoid GraphQL errors
      const cleanUpdates = { ...updates };
      if ('__typename' in cleanUpdates) {
        delete (cleanUpdates as any).__typename;
      }
      
      const result = await updateConfig({
        variables: {
          configId,
          updates: cleanUpdates,
        },
      });
      return result.data?.update_card_configs_by_pk;
    } catch (error) {
      console.error('Error updating card config:', error);
      throw error;
    }
  };

  return {
    cardConfig: data?.card_configs[0] || null,
    loading,
    error,
    updateCardConfig,
    updating: updateResult.loading,
    updateError: updateResult.error,
    refetch,
  };
} 