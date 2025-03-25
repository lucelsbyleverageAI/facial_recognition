# Project Import Service

This module provides services for importing projects, consent profiles, and face images from a filesystem structure into the database.

## Architecture

The code follows a modular approach with clear separation of concerns:

- **ProjectImportOrchestrator**: Main entry point that coordinates the import process.
- **ProjectService**: Handles project-related operations.
- **ProfileService**: Handles consent profile-related operations.
- **FaceService**: Handles consent face-related operations.

## Filesystem Structure

The service expects the following filesystem structure:

```
ConsentFolder/
├── {ProjectId}_{ProjectName}/
│   ├── {ProfileId}_{ProfileName}/
│   │   ├── {FaceId}_F.jpg  (Frontal face image)
│   │   └── {FaceId}_S.jpg  (Side face image)
│   └── ...
└── ...
```

## Usage

```python
from src.services.project_import.project_import_orchestrator import ProjectImportOrchestrator

# Create an orchestrator instance
orchestrator = ProjectImportOrchestrator()  # Uses default consent folder path
# or
orchestrator = ProjectImportOrchestrator("/path/to/consent/folder")  # Custom path

# Import all project data
import asyncio
stats = asyncio.run(orchestrator.import_all_project_data())
```

## Benefits of Modular Structure

1. **Modularity**: Each service has a single responsibility.
2. **Testability**: Services can be tested independently.
3. **Readability**: Smaller, focused classes are easier to understand.
4. **Maintainability**: Changes to one aspect don't affect others.
5. **Extensibility**: New features can be added without changing existing code.

## Error Handling

All services include comprehensive error handling and logging to make it easier to diagnose issues during the import process. 