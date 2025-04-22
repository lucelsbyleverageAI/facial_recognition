#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
print_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
print_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
print_err() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Source environment variables from .env file
if [ -f "$SCRIPT_DIR/../.env" ]; then
    source "$SCRIPT_DIR/../.env"
else 
    print_err "No .env file found in the parent directory"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$HASURA_GRAPHQL_ENDPOINT" ]; then
    # Default to localhost if not provided
    HASURA_GRAPHQL_ENDPOINT="http://localhost:8080"
fi

if [ -z "$HASURA_ADMIN_SECRET" ]; then
    print_err "HASURA_ADMIN_SECRET is not set in the .env file"
    exit 1
fi

if [ -z "$HASURA_GRAPHQL_DATABASE_URL" ]; then
    print_err "HASURA_GRAPHQL_DATABASE_URL is not set in the .env file"
    exit 1
fi

print_info "Waiting for Hasura to be ready..."

# Function to check if Hasura is ready
wait_for_hasura() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$HASURA_GRAPHQL_ENDPOINT/healthz" | grep -q "200"; then
            print_ok "Hasura is ready!"
            return 0
        else
            print_info "Waiting for Hasura to start... (${attempt}/${max_attempts})"
            sleep 2
            attempt=$((attempt + 1))
        fi
    done
    
    print_err "Hasura did not become ready in time"
    return 1
}

# Wait for Hasura to be ready
if ! wait_for_hasura; then
    exit 1
fi

# Add a delay to ensure Postgres has completed initializing with our SQL script
print_info "Waiting for database to be fully initialized..."
sleep 5

# Track all tables individually
print_info "Tracking all tables individually..."

# Get list of tables
TABLES=("projects" "consent_profiles" "consent_faces" "cards" "card_configs" "watch_folders" "clips" "frames" "detected_faces" "face_matches" "processing_tasks")

for table in "${TABLES[@]}"; do
    print_info "Tracking table: $table"
    RESPONSE=$(curl -s -X POST "$HASURA_GRAPHQL_ENDPOINT/v1/metadata" \
        -H "X-Hasura-Admin-Secret: $HASURA_ADMIN_SECRET" \
        -H "Content-Type: application/json" \
        -d "{
            \"type\": \"pg_track_table\",
            \"args\": {
                \"source\": \"default\",
                \"schema\": \"public\",
                \"name\": \"$table\"
            }
        }")
    
    if echo "$RESPONSE" | grep -q "\"message\""; then
        print_ok "Table $table tracked successfully"
    else
        print_err "Failed to track table $table"
        print_err "Error: $RESPONSE"
    fi
done

# Track all foreign key relationships automatically
print_info "Tracking all foreign key relationships..."

# Define relationships manually based on Foreign Key Constraints (Parent:Child:FKColumn)
RELATIONSHIPS=(
    # FK on cards
    "projects:cards:project_id"
    
    # FK on consent_profiles
    "projects:consent_profiles:project_id"
    
    # FK on consent_faces
    "consent_profiles:consent_faces:profile_id"
    
    # FK on card_configs
    "cards:card_configs:card_id"
    
    # FK on watch_folders
    "card_configs:watch_folders:config_id"
    
    # FK on clips
    "cards:clips:card_id"
    "watch_folders:clips:watch_folder_id"
    
    # FK on frames
    "clips:frames:clip_id"
    
    # FK on detected_faces
    "frames:detected_faces:frame_id"
    
    # FK on face_matches
    "detected_faces:face_matches:detection_id"
    "consent_faces:face_matches:consent_face_id"
    
    # FK on processing_tasks
    "cards:processing_tasks:card_id"
)

for rel in "${RELATIONSHIPS[@]}"; do
    IFS=':' read -r table1 table2 column <<< "$rel"
    
    print_info "Tracking relationship pair for: $table1 <-> $table2 via $column"
    
    # Convert parent table name (table1) to singular for object relationship name
    if [[ "$table1" == *s ]]; then
        table1_singular="${table1%s}"
    else
        table1_singular="$table1"
    fi

    # 1. Attempt to create ARRAY relationship (Parent -> Child)
    # Example: projects -> cards (on projects table)
    ARRAY_REL_RESPONSE=$(curl -s -X POST "$HASURA_GRAPHQL_ENDPOINT/v1/metadata" \
        -H "X-Hasura-Admin-Secret: $HASURA_ADMIN_SECRET" \
        -H "Content-Type: application/json" \
        -d "{
            \"type\": \"pg_create_array_relationship\",
            \"args\": {
                \"source\": \"default\",
                \"table\": {
                    \"schema\": \"public\",
                    \"name\": \"$table1\"
                },
                \"name\": \"${table2}\",
                \"using\": {
                    \"foreign_key_constraint_on\": {
                        \"table\": {
                            \"schema\": \"public\",
                            \"name\": \"$table2\"
                        },
                        \"column\": \"${column}\"
                    }
                }
            }
        }")

    # Process array relationship response
    if echo "$ARRAY_REL_RESPONSE" | grep -q "already exists"; then
        print_warn "Array relationship already exists: $table1 -> $table2"
    elif echo "$ARRAY_REL_RESPONSE" | grep -q "\"message\""; then
        print_ok "Array relationship created: $table1 -> $table2"
    else
        # Try to extract a meaningful error message if possible
        ERROR_MSG=$(echo "$ARRAY_REL_RESPONSE" | grep -o '"error":"[^"]*"' | cut -d '"' -f 4 || echo "Unknown error")
        print_err "Failed to create array relationship $table1 -> $table2: $ERROR_MSG"
    fi

    # 2. Attempt to create OBJECT relationship (Child -> Parent)
    # Example: card -> project (on cards table)
    OBJECT_REL_RESPONSE=$(curl -s -X POST "$HASURA_GRAPHQL_ENDPOINT/v1/metadata" \
        -H "X-Hasura-Admin-Secret: $HASURA_ADMIN_SECRET" \
        -H "Content-Type: application/json" \
        -d "{
            \"type\": \"pg_create_object_relationship\",
            \"args\": {
                \"source\": \"default\",
                \"table\": {
                    \"schema\": \"public\",
                    \"name\": \"$table2\"
                },
                \"name\": \"${table1_singular}\",
                \"using\": {
                    \"foreign_key_constraint_on\": \"${column}\"
                }
            }
        }")

    # Process object relationship response
    if echo "$OBJECT_REL_RESPONSE" | grep -q "already exists"; then
        print_warn "Object relationship already exists: $table2 -> ${table1_singular}"
    elif echo "$OBJECT_REL_RESPONSE" | grep -q "\"message\""; then
        print_ok "Object relationship created: $table2 -> ${table1_singular}"
    else
        ERROR_MSG=$(echo "$OBJECT_REL_RESPONSE" | grep -o '"error":"[^"]*"' | cut -d '"' -f 4 || echo "Unknown error")
        print_err "Failed to create object relationship $table2 -> ${table1_singular}: $ERROR_MSG"
    fi
done

# Special handling for one-to-one relationship between cards and card_configs
print_info "Ensuring object relationship cards.card_config exists (1:1)"
OBJ_REL_CHECK=$(curl -s -X POST "$HASURA_GRAPHQL_ENDPOINT/v1/query" \
    -H "X-Hasura-Admin-Secret: $HASURA_ADMIN_SECRET" \
    -H "Content-Type: application/json" \
    -d "{\n        \"type\": \"run_sql\",\n        \"args\": {\n            \"sql\": \"SELECT rel_name FROM hdb_catalog.hdb_relationship WHERE table_name = 'cards' AND rel_name = 'card_config'\"\n        }\n    }")

if echo "$OBJ_REL_CHECK" | grep -q "card_config"; then
    print_ok "Object relationship card_config already exists on cards"
else
    print_info "Creating object relationship card_config on cards..."
    RESP_OBJ=$(curl -s -X POST "$HASURA_GRAPHQL_ENDPOINT/v1/metadata" \
        -H "X-Hasura-Admin-Secret: $HASURA_ADMIN_SECRET" \
        -H "Content-Type: application/json" \
        -d '{
            "type": "pg_create_object_relationship",
            "args": {
                "source": "default",
                "table": {"schema": "public", "name": "cards"},
                "name": "card_config",
                "using": {
                    "manual_configuration": {
                        "remote_table": {"schema": "public", "name": "card_configs"},
                        "column_mapping": {"card_id": "card_id"}
                    }
                }
            }
        }')

    if echo "$RESP_OBJ" | grep -q "\"message\""; then
        print_ok "Object relationship card_config created successfully"
    else
        print_err "Failed to create object relationship card_config"
        echo "$RESP_OBJ"
    fi
fi

print_ok "Hasura initialization completed successfully!" 