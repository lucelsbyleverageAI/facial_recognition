import { gql } from '@apollo/client';

export const GET_PROJECTS = gql`
  query GetProjects {
    projects {
      project_id
      project_name
      created_at
    }
  }
`;

export const GET_PROJECT_WITH_DETAILS = gql`
  query GetProjectWithDetails($projectId: uuid!) {
    projects_by_pk(project_id: $projectId) {
      project_id
      project_name
      created_at
      consent_profiles {
        profile_id
        person_name
        consent_faces(limit: 1) {
          face_image_path
        }
      }
      cards {
        card_id
        card_name
        status
        created_at
      }
    }
  }
`;

export const GET_CONSENT_PROFILES_BY_PROJECT = gql`
  query GetConsentProfilesByProject($projectId: uuid!, $limit: Int = 5, $offset: Int = 0) {
    consent_profiles(
      where: { project_id: { _eq: $projectId } }
      order_by: { person_name: asc }
      limit: $limit
      offset: $offset
    ) {
      profile_id
      person_name
      consent_faces {
        consent_face_id
        face_image_path
        pose_type
      }
    }
    consent_profiles_aggregate(where: { project_id: { _eq: $projectId } }) {
      aggregate {
        count
      }
    }
  }
`;

export const GET_CARDS_BY_PROJECT = gql`
  query GetCardsByProject($projectId: uuid!, $limit: Int = 5, $offset: Int = 0) {
    cards(
      where: { project_id: { _eq: $projectId } }
      order_by: { created_at: desc }
      limit: $limit
      offset: $offset
    ) {
      card_id
      card_name
      status
      created_at
    }
    cards_aggregate(where: { project_id: { _eq: $projectId } }) {
      aggregate {
        count
      }
    }
  }
`;

export const GET_PROJECT_INFO = gql`
  query GetProjectInfo($projectId: uuid!) {
    projects_by_pk(project_id: $projectId) {
      project_id
      project_name
    }
  }
`;

export const ADD_NEW_CARD = gql`
  mutation AddNewCard($projectId: uuid!, $cardName: String!, $description: String) {
    insert_cards_one(object: {project_id: $projectId, card_name: $cardName, description: $description, status: "pending"}) {
      card_id
      card_name
      description
      created_at
      status
      project_id
    }
  }
`;

export const GET_CARD_INFO = gql`
  query GetCardInfo($projectId: uuid!, $cardId: uuid!) {
    projects_by_pk(project_id: $projectId) {
      project_id
      project_name
    }
    cards_by_pk(card_id: $cardId) {
      card_id
      card_name
    }
  }
`;

export const GET_CARD_CONFIG = gql`
  query GetCardConfig($cardId: uuid!) {
    card_configs(where: {card_id: {_eq: $cardId}}) {
      config_id
      scene_sensitivity
      fallback_frame_rate
      use_eq
      lut_file
      model_name
      detector_backend
      align
      enforce_detection
      distance_metric
      expand_percentage
      threshold
      normalization
      silent
      refresh_database
      anti_spoofing
      detection_confidence_threshold
      watch_folders {
        watch_folder_id
        folder_path
        status
      }
    }
  }
`;

export const UPDATE_CARD_CONFIG = gql`
  mutation UpdateCardConfig($configId: uuid!, $updates: card_configs_set_input!) {
    update_card_configs_by_pk(pk_columns: {config_id: $configId}, _set: $updates) {
      config_id
    }
  }
`;

export const ADD_WATCH_FOLDER = gql`
  mutation AddWatchFolder($configId: uuid!, $folderPath: String!) {
    insert_watch_folders_one(object: {config_id: $configId, folder_path: $folderPath, status: "idle"}) {
      watch_folder_id
      folder_path
      status
    }
  }
`;

export const REMOVE_WATCH_FOLDER = gql`
  mutation RemoveWatchFolder($watchFolderId: uuid!) {
    delete_watch_folders_by_pk(watch_folder_id: $watchFolderId) {
      watch_folder_id
    }
  }
`;

export const UPDATE_WATCH_FOLDER_STATUS = gql`
  mutation UpdateWatchFolderStatus($watchFolderId: uuid!, $status: String!) {
    update_watch_folders_by_pk(
      pk_columns: {watch_folder_id: $watchFolderId}, 
      _set: {status: $status}
    ) {
      watch_folder_id
      status
    }
  }
`;

export const UPDATE_CLIP_STATUS = gql`
  mutation UpdateClipStatus($clipId: uuid!, $status: String!) {
    update_clips_by_pk(
      pk_columns: {clip_id: $clipId}, 
      _set: {status: $status}
    ) {
      clip_id
      status
    }
  }
`;

export const DELETE_CLIP = gql`
  mutation DeleteClip($clipId: uuid!) {
    delete_clips_by_pk(clip_id: $clipId) {
      clip_id
    }
  }
`;

export const GET_CARD_BY_ID = gql`
  query GetCardById($cardId: uuid!) {
    cards_by_pk(card_id: $cardId) {
      card_id
      card_name
      description
      status
      created_at
      project_id
    }
  }
`;

// Subscription for card status updates
export const CARD_STATUS_SUBSCRIPTION = gql`
  subscription WatchCardStatus($cardId: uuid!) {
    cards_by_pk(card_id: $cardId) {
      card_id
      card_name
      description
      status
      created_at
      project_id
    }
  }
`; 