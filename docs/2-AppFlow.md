# Application Flow

## Projects Dashboard

The Projects Dashboard is the landing page (no login as it is a local setup). At the top is a header with the application name "Facial Recognition Processing". The main content area shows a grid of project cards. Each project card displays the project name, ID, date created. At the bottom of each card is a "Select" button, along with an "Expand" toggle button.

When a project is expanded, it reveals:
- A list of consent profiles (sorted alphabetically), showing:
  - First 5 names with associated thumbnail images of consent files
  - "Show More" button if there are additional profiles
- A list of associated cards, displaying:
  - First 5 card IDs and names
  - "Show More" button if there are additional cards

When a user clicks on a project's "Select" button, they are taken to the Project Details page for that project.

## Project Details Page

The Project Details Page shows after selecting a project from the dashboard. The page has a breadcrumb navigation at the top showing "Projects > [Project Name]". The user can easily navigate back to the projects dashboard by clicking 'Projects' in the breadcrumb or the Home icon button in the header. The page is divided into two main sections:

### Cards Section
Located at the top half of the page, this section displays:
- A header with "Cards" title and a refresh button
- A searchable and sortable data grid showing:
  - Card ID
  - Card Name
  - Status
  - Last Modified Date
  - Each card has a Select button to navigate to the card details page
- Pagination controls for handling large datasets
- Quick filters for status
- A button to add a new card
Other than displaying information, the add new card button is the key functionality for this page. When clicked, it opens a modal to add a new card. The modal has fields for, card name and optional description. When the user clicks submit in the modal, the card is added to the database and the grid is updated to include the new card.

### Consent Profiles Section
Located at the bottom half of the page, this section includes:
- A header with "Consent Profiles" title and a refresh button
- A virtualized grid view of consent profiles with:
  - Thumbnail images arranged in a responsive grid
  - Name displayed below each thumbnail
  - Hover state showing additional details
- Search bar for filtering profiles by name
- Alphabet quick-jump sidebar for easy navigation
- "Load More" button for infinite scroll functionality
- Group headers showing alphabetical sections (A, B, C, etc.)

## Card Details Page

The Card Details Page shows after selecting a card from the Project Details page. The page has a breadcrumb navigation at the top showing "Projects > [Project Name] > [Card Name]". The user can easily navigate back to the project details page by clicking the project name in the breadcrumb or clicking 'Projects' in the breadcrumb to get back to the projects dashboard or the Home icon button in the header. The card page is split into two tabs, 'Processing Dashboard' and 'Results'. At the top of the processing dashboard tab is a configuration section that displays existing watch folders and allows users to add or remove watch folders from the card. The user has actions associated with each watch folder location, including to Run Initial Scan or toggle monitoring status to activate or deactivate monitoring. If there are no watch folders present, the user is encouraged to add one as the user cannot start any processing until the watch folder is setup. The UI shows the current status. There is also a processing configuration button that opens up the processing configuration modal and allows the user to adjust the processing configuration for the card. The next section is the clips section which shows cards for clips associated with the card and their status - either unselected, pending, queued, processing, or completed. In pending, the user can cancel the pending clip and move it to unselected. Then there is a start processing button which will trigger the backend to process any queued clips. Once start processing is clicked, there is a stop processing button which will stop the processing of any running clips. In the results tab, the user can see the results of the processing with a table of results frame-by-frame. There will be columns for clip, frame, timestamp, thumbnail, status, detected faces, matched faces. This will be a paginated table with options to increase the number of rows displayed and toggle pages. There will be pre-defined filter options for status, frames with detected faces, frames with matched faces, frames with unmatched faces. At the top there will be a button to generate a report.
