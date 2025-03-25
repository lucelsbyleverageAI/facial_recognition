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
      consent_faces(limit: 1) {
        face_image_path
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